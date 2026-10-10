# Repo Doctor 0.3 — two-step local investigation

A local repository troubleshooter for an 8 GB Mac. The model first explains a
failure, then makes one proposed source replacement in a separate call. Python
checks that proposal and builds a diff. The app never writes to the inspected
repository or executes its code.

## Upgrade from 0.2

1. Stop Streamlit with Control+C.
2. Extract this ZIP separately and copy **doctor.py** and **app.py** into your
   existing project folder, replacing those two files. This includes all previous
   manual changes that still apply: thinking enabled and detailed HTTP errors.
3. Keep your existing virtual environment and model. No new dependency is needed.
4. In the existing project folder:

   ```bash
   source .venv/bin/activate
   python -m streamlit run app.py --server.address 127.0.0.1
   ```

5. Refresh http://localhost:8501. Confirm **Version 0.3 · Two-step investigation**.
6. Keep the deliberately broken demo unchanged. Use the original traceback in
   the problem field, click **Inspect repository**, then **Diagnose**.
7. Review **Raw responses — diagnosis and edit** and **Run details** if rejected.
   These include the actual plain-text outputs and per-stage timing.

## Fresh Mac setup

Install and open https://ollama.com/download/mac. Ollama documentation currently
requires macOS 14+; Apple Silicon supports CPU/GPU, Intel Macs use CPU only.
Install Python 3.10+ if needed. Then in Terminal:

```bash
ollama pull qwen3:1.7b
```

From this extracted folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

You can use any eligible local project by entering its absolute folder path.
A focus file is optional and uses a relative path such as `src/pipeline.py`.

## What changed

Version 0.2 requested diagnosis, evidence, code edits and tests in one JSON
response. In user testing with Qwen3 1.7B, answers included unchanged edits and
unescaped code strings. JSON mode also produced an HTTP 500 repetition error.
The user reported Ollama **0.34.2**. We have not established that this is a
version-specific Ollama bug or a memory problem.

Version 0.3 has two sequential calls, both with thinking enabled and **no format
field**. The first returns a plain-text diagnosis. The second sees the original
source/error plus a bounded portion of that unverified diagnosis and returns:

```text
FILE: relative/path.py
<<<OLD>>>
original substring
<<<NEW>>>
replacement substring
<<<END>>>
```

It can return `NO_EDIT` instead. Python requires the exact delimiters and one
edit. No JSON escaping is required for source code. Responses that don't follow
the protocol still get rejected; this design is not a guarantee of model quality.
A failed edit call preserves the diagnosis and actual error. There are no
automatic retries and no automatic code execution.

## Validation and limits

The validator checks that the path is eligible and was included in the evidence,
that the old substring was shown, matches exactly once in the current source,
and that the replacement changes it. It checks Python syntax using `ast.parse`
and generates real unified diff line offsets. A snapshot comparison rejects
changes to the target file made during inference. Re-inspect after any edits:
the evidence preview itself is a snapshot from when you clicked Inspect.

Passing these checks does not prove a correct fix. Citations and diagnosis are
unverified model text. Non-Python languages do not receive syntax checking.
Only a single existing-file edit is supported. Regression tests are deliberately
outside the generation tasks for now. Review and run your own tests after
manually applying an approved change.

For the supplied demo, the repaired transform should satisfy:

```python
assert transform(load()) == [{"id": "C001"}]
```

The demo file is intentionally broken in the archive. Do not fix it before
comparing model runs.

## Resource use

Defaults: qwen3:1.7b, 4,096-token context, thinking enabled, temperature 0.1,
and 1,600 generated tokens per call (budget may be consumed by thinking too).
There are two sequential calls per investigation. A truncated response is never
accepted as a patch. The higher per-call cap accommodates thinking; it is not an
attempt to raise Ollama's repetition limit. The protocol change removes JSON
constraints; whether it avoids that error must be tested on the user's machine.

The source preview is capped at about 5,000 characters, error text at 2,000,
and diagnosis passed to the second call at 1,800. These are heuristic limits,
not exact token counts. Shorten inputs if context or output limits are reached.
The 1.7B model download is roughly 1.4 GB; total runtime memory is higher.
Monitor Activity Monitor's memory pressure. To unload: `ollama stop qwen3:1.7b`.
A 0.6B fallback is selectable after `ollama pull qwen3:0.6b`, with likely reduced
capability. No new model is required for the 0.3 upgrade.

## Retrieval and access

This is lexical retrieval, not autonomous repository exploration. It scores
error terms, prioritizes traceback paths/lines, and includes up to five excerpts.
Missing code can lead to incorrect diagnoses. Use a small project folder.
Git discovery respects ignored untracked files; tracked files stay eligible.
Outside Git, .gitignore is not interpreted. Hidden paths, dependency/build
folders, symlinks, non-allowlisted extensions, files over 100 KB, and filenames
suggesting secrets are excluded. Discovery has an approximately 5,000-entry cap.
These filename checks do not detect all embedded secrets. Review the preview.
Source and logs go to the loopback Ollama API only; proxies are bypassed. Model
and dependency downloads need internet. Keep the UI and Ollama bound locally.

## CLI and tests

The core investigator needs only Python's standard library and running Ollama:

```bash
python3 doctor.py demo_repo --issue "KeyError: customer_id in pipeline.py" --preview
python3 doctor.py demo_repo --issue "KeyError: customer_id in pipeline.py"
python3 -m unittest discover -s tests -v
```

Nine core tests passed with mocked inference, covering retrieval/path access,
quoted and multiline edit parsing, invalid edits, HTTP error details, incomplete
responses, and two-call orchestration. This does not measure live model accuracy
or performance on your Mac. UI success and failed-retry states were also checked with mocked inference.

## References

- https://docs.ollama.com/macos
- https://docs.ollama.com/api/chat
- https://docs.ollama.com/api/errors
- https://ollama.com/library/qwen3:1.7b
