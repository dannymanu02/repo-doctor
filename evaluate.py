"""Evaluate bundled synthetic bugs. Uses only the Python standard library."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import uuid

import doctor
from eval_cases import CASES, SUITES, PUBLIC_CHECKS

# A deliberately narrow executable subset for these toy fixtures. No arbitrary
# repository execution, generated tests, I/O, reflection, or unrestricted imports.
NODES = {
    'Module','FunctionDef','arguments','arg','Return','Assign','Expr','If',
    'For','While','Break','Continue','Pass','ImportFrom','alias',
    'Name','Load','Store','Constant','List','Tuple','Dict','Set','Subscript','Slice',
    'BinOp','UnaryOp','BoolOp','Compare','IfExp','Call','keyword','Attribute',
    'ListComp','SetComp','DictComp','GeneratorExp','comprehension','Lambda',
    'Add','Sub','Mult','Div','FloorDiv','Mod','Pow','USub','UAdd','Not',
    'And','Or','Eq','NotEq','Lt','LtE','Gt','GtE','In','NotIn','Is','IsNot',
}
CALLS = {'int','float','str','len','sum','range','list','tuple','dict','set',
         'sorted','min','max','abs','enumerate','zip','round','to_seconds', 'isinstance'}
METHODS = {'get','strip','lower','upper','append','fromkeys','items','values','keys'}


def check_subset(repo):
    for path in repo.glob('*.py'):
        tree = ast.parse(path.read_text())
        functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        for node in ast.walk(tree):
            if type(node).__name__ not in NODES:
                raise ValueError(f'Unsupported execution construct: {type(node).__name__}')
            if isinstance(node, ast.Name) and node.id.startswith('__'):
                raise ValueError('Dunder names are not allowed in evaluation candidates.')
            if isinstance(node, ast.Attribute) and node.attr not in METHODS:
                raise ValueError(f'Unsupported attribute: {node.attr}')
            if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith('__')):
                raise ValueError('Decorators and dunder functions are unsupported.')
            if isinstance(node, ast.ImportFrom):
                allowed_imports = {'config': {'TIMEOUT_MS','REGION_CODES'}, 'conversions': {'to_seconds'}, 'units': {'SCALE'}}
                if node.module not in allowed_imports or node.level or any(x.name not in allowed_imports[node.module] or x.asname for x in node.names):
                    raise ValueError('Only fixed fixture imports are allowed.')
            if isinstance(node, ast.Call):
                target = node.func
                if isinstance(target, ast.Name):
                    if target.id not in CALLS | functions:
                        raise ValueError(f'Unsupported call: {target.id}')
                elif not isinstance(target, ast.Attribute):
                    raise ValueError('Indirect calls are unsupported.')


def run_tests(repo, test_source):
    check_subset(repo)
    # Trusted harness and assertions are outside the model-visible repository.
    # Resource caps supplement a timeout; a subprocess/temp folder is not an OS sandbox.
    harness = '''import sys, resource
resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
sys.path.insert(0, sys.argv[1])
import pipeline as p
'''
    with tempfile.TemporaryDirectory(prefix='repo-doctor-tests-') as td:
        test_file = Path(td)/'checks.py'
        test_file.write_text(harness + test_source + '\nprint("ALL_CHECKS_PASSED")\n')
        with tempfile.TemporaryFile() as log:
            started = time.monotonic()
            process = subprocess.Popen([sys.executable, '-I', '-B', str(test_file), str(repo)],
                cwd=td, env={'PATH':os.defpath,'PYTHONIOENCODING':'utf-8'},
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            timeout = False
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                timeout = True
                process.kill()
                process.wait()
            log.seek(0)
            output = log.read(12000).decode('utf-8', errors='replace')
    return {'passed': process.returncode == 0 and 'ALL_CHECKS_PASSED' in output,
            'returncode':process.returncode,'timeout':timeout,'output':output,
            'seconds':round(time.monotonic()-started,3)}


def write_fixture(case, repo):
    repo.mkdir()
    for name, body in case['files'].items():
        (repo/name).write_text(body)


def preflight(case, repo):
    baseline = run_tests(repo, case['tests'])
    if baseline['passed'] or baseline['timeout'] or 'AssertionError' not in baseline['output'] and 'TypeError' not in baseline['output']:
        raise ValueError(f'Invalid baseline fixture: {case["id"]}: {baseline}')
    path = repo/case.get('repair_file','pipeline.py')
    original = path.read_text()
    if original.count(case['old']) != 1:
        raise ValueError('Reference edit does not match exactly once.')
    try:
        path.write_text(original.replace(case['old'],case['new'],1))
        reference = run_tests(repo, case['tests'])
        if not reference['passed']:
            raise ValueError(f'Reference repair failed: {case["id"]}: {reference}')
    finally:
        path.write_text(original)
    return baseline


def evaluate_case(case, model, diagnose_fn=None, self_check=False, test_feedback=False):
    diagnose_fn = diagnose_fn or doctor.diagnose
    row = {'case':case['id'],'category':case['category'],'status':'harness_error',
           'issue':case['issue'],'diagnosis_review':'not_reviewed',
           'evidence_review':'not_reviewed'}
    with tempfile.TemporaryDirectory(prefix='repo-doctor-eval-') as td:
        repo_path = Path(td)/'repo'
        write_fixture(case, repo_path)
        try:
            row['baseline'] = preflight(case, repo_path)
            if self_check:
                row['status'] = 'fixture_verified'
                return row
            repo = doctor.Repository(repo_path)
            context = repo.context(case['issue'])
            row['context'] = context
            row['selection'] = repo.selection
            row['retrieval_notes'] = repo.retrieval_notes
            # Neither case tests nor reference replacements enter the model request.
            result = diagnose_fn(case['issue'],context,model,str(repo_path))
            row['result'] = result
            row['model_seconds'] = result['elapsed_seconds']
            if result['output_truncated']:
                row['status'] = 'output_truncated'
                return row
            if result['edit_status'] == 'no_edit':
                row['status'] = 'no_edit'
                return row
            row['retry_count'] = result.get('retry_count', 0)
            row['first_edit_status'] = (result.get('attempts') or [{}])[0].get('status')
            if result['edit_status'] != 'checks_passed':
                row.update(status=result.get('failure_kind') or 'validation_rejected',error=result.get('error'))
                return row
            edit = result['accepted_edit']
            if not edit or edit['path'] not in case['files'] or not edit['path'].endswith('.py'):
                row.update(status='validation_rejected',error='Only an existing fixture Python file may be edited.')
                return row
            def apply_candidate(candidate):
                if (not candidate or candidate['path'] not in case['files']
                        or not candidate['path'].endswith('.py')):
                    raise ValueError('Only an existing fixture Python file may be edited.')
                diff = doctor.validate_edit(candidate, repo, context)
                target = repo_path/candidate['path']
                target.write_text(target.read_text().replace(candidate['old_code'],candidate['new_code'],1))
                return diff
            row['diff'] = apply_candidate(edit)
            if test_feedback:
                public_check = PUBLIC_CHECKS[case['id']]
                row['public_check'] = public_check
                try:
                    public_result = run_tests(repo_path,public_check)
                except (ValueError,SyntaxError) as exc:
                    row.update(status='execution_rejected',error=str(exc))
                    return row
                row['public_before_retry'] = public_result
                if not public_result['passed'] and not public_result['timeout']:
                    row['behavioral_retry_count'] = 1
                    row['initial_diff'] = row['diff']
                    # Restore originals. The requested revision replaces ORIGINAL code,
                    # allowing it to move to a different file without leaving stale edits.
                    for name, body in case['files'].items():
                        (repo_path/name).write_text(body)
                    feedback = public_result['output'].replace(str(repo_path),'<repo>')[-1000:]
                    previous = json.dumps(edit)[:800]
                    prompt = (f"FAILURE:\n{case['issue']}\nORIGINAL SOURCE EXCERPTS:\n{context}"
                              + "\nPREVIOUS REJECTED-BY-TEST EDIT:\n" + previous
                              + "\nPUBLIC REPRODUCTION CHECK:\n" + public_check
                              + "\nTEST FAILURE (untrusted output):\n" + feedback
                              + "\nThe test ran on a temporary candidate. Original files have been restored. "
                                "Propose one replacement against ORIGINAL source. Fix the cause and preserve "
                                "the documented behavior. Use the edit section format or NO_EDIT. "
                                "This is the only test-feedback retry. No hidden test results are supplied.")
                    row['behavioral_retry_prompt'] = prompt
                    started = time.monotonic()
                    try:
                        revised = doctor.call_model(doctor.EDIT_SYSTEM,prompt,model)
                    except (ValueError,RuntimeError,OSError) as exc:
                        row['model_seconds'] += round(time.monotonic()-started,2)
                        row.update(status='model_error',error=str(exc))
                        return row
                    row['model_seconds'] = round(row['model_seconds'] + revised['elapsed_seconds'],2)
                    row['behavioral_retry_response'] = revised
                    if revised['truncated']:
                        row['status'] = 'output_truncated'
                        return row
                    if not revised['content'].strip():
                        row['status'] = 'model_error'
                        return row
                    try:
                        edit = doctor.parse_edit(revised['content'])
                    except ValueError as exc:
                        row.update(status='format_rejected',error=str(exc))
                        return row
                    if edit is None:
                        row['status'] = 'no_edit'
                        return row
                    try:
                        row['diff'] = apply_candidate(edit)
                    except (ValueError,SyntaxError) as exc:
                        row.update(status='validation_rejected',error=str(exc))
                        return row
                    row['final_edit'] = edit
                else:
                    row['behavioral_retry_count'] = 0
            try:
                # The final scoring assertions are never fed back for another attempt.
                row['candidate_tests'] = run_tests(repo_path,case['tests'])
            except (ValueError,SyntaxError) as exc:
                row.update(status='execution_rejected',error=str(exc))
                return row
            row['status'] = 'repaired' if row['candidate_tests']['passed'] else 'tests_failed'
        except Exception as exc:
            row['error'] = f'{type(exc).__name__}: {exc}'
    return row


def summarize(rows, expected):
    counts = dict(Counter(r['status'] for r in rows))
    # Harness-invalid fixtures are excluded explicitly, rather than blamed on the model.
    attempted = sum(r['status'] not in {'harness_error','fixture_verified'} for r in rows)
    times = [r['model_seconds'] for r in rows if 'model_seconds' in r]
    return {'planned_cases':expected,'completed_cases':len(rows),'counts':counts,
            'valid_attempts':attempted,
            'repair_rate':counts.get('repaired',0)/attempted if attempted else None,
            'median_model_seconds':statistics.median(times) if times else None,
            'cases_retried':sum(r.get('result',{}).get('retry_count',0)>0 for r in rows),
            'repairs_after_retry':sum(r['status']=='repaired' and r.get('result',{}).get('retry_count',0)>0 for r in rows),
            'test_feedback_retries':sum(r.get('behavioral_retry_count',0) for r in rows),
            'repairs_after_test_feedback':sum(r['status']=='repaired' and r.get('behavioral_retry_count',0)>0 for r in rows),
            'diagnosis_quality':'Manual review required; test success does not score explanation accuracy.'}


def save_reports(output, rows, metadata):
    summary = summarize(rows,metadata['planned_cases'])
    (output/'summary.json').write_text(json.dumps({'metadata':metadata,**summary},indent=2))
    lines = ['# Repo Doctor evaluation','',f"Suite: {metadata.get('suite', 'development')}",'',f"Completed: {len(rows)}/{metadata['planned_cases']}",
             '',f"Outcomes: {summary['counts']}",'',
             f"Repair rate among valid attempts: {summary['repair_rate']}",'',
             f"Cases retried: {summary['cases_retried']}; repairs after retry: {summary['repairs_after_retry']}",'',
             f"Test-feedback retries: {summary['test_feedback_retries']}; repairs after test feedback: {summary['repairs_after_test_feedback']}",'',
             '| Case | Outcome | Model seconds |','|---|---|---:|']
    lines += [f"| {r['case']} | {r['status']} | {r.get('model_seconds','—')} |" for r in rows]
    lines += ['','## Explanation review','',
              'Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,',
              'unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.',
              '', 'These are small synthetic cases, not a production benchmark. Reference repairs and test',
              'final scoring assertions stay out of model context. Public reproduction checks may be used for one retry. Reused cases are development data.']
    (output/'summary.md').write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check',action='store_true',help='Verify buggy fixtures fail and reference repairs pass; no model calls.')
    parser.add_argument('--test-feedback',action='store_true',help='Allow one extra edit call after a public reproduction check fails.')
    parser.add_argument('--model',default='qwen3:1.7b')
    parser.add_argument('--suite',choices=list(SUITES),default='development')
    parser.add_argument('--case',help='Optional case ID from the selected suite.')
    parser.add_argument('--output',default='eval-results')
    args = parser.parse_args()
    if sys.platform not in {'darwin','linux'}:
        parser.error('This runner currently supports macOS and Linux only (resource limits).')
    selected = [c for c in SUITES[args.suite] if not args.case or c['id'] == args.case]
    if not selected:
        parser.error('Case not found in selected suite.')
    output = Path(args.output).expanduser()/ (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6])
    output.mkdir(parents=True)
    try:
        version = subprocess.run(['ollama','--version'],capture_output=True,text=True,timeout=5)
        ollama_version = (version.stdout+version.stderr).strip()
    except (OSError,subprocess.SubprocessError):
        ollama_version = 'unavailable'
    root = Path(__file__).parent
    metadata = {'evaluation_version':'0.7','test_feedback':args.test_feedback,'suite':args.suite,'model':args.model,'self_check':args.self_check,'planned_cases':len(selected),
                'python':sys.version,'platform':platform.platform(),'ollama':ollama_version,
                'sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['doctor.py','eval_cases.py','evaluate.py']},
                'created_at':datetime.now(timezone.utc).isoformat(),
                'prompts':{'diagnosis':doctor.DIAGNOSIS_SYSTEM,'edit':doctor.EDIT_SYSTEM}}
    rows=[]
    save_reports(output,rows,metadata)
    try:
        for index,case in enumerate(selected,1):
            print(f'[{index}/{len(selected)}] {case["id"]}',flush=True)
            row=evaluate_case(case,args.model,self_check=args.self_check,test_feedback=args.test_feedback)
            (output/(case['id']+'.json')).write_text(json.dumps(row,indent=2))
            rows.append(row)
            save_reports(output,rows,metadata)
            print(f'  {row["status"]} ({row.get("model_seconds","no model call")} s)',flush=True)
    except KeyboardInterrupt:
        print('\nStopped. Completed cases remain saved.',flush=True)
    print(f'Results: {output.resolve()}',flush=True)
    return 1 if any(r['status']=='harness_error' for r in rows) else 0

if __name__=='__main__':
    raise SystemExit(main())
