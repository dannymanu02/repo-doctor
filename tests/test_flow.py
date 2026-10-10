import io
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from doctor import Repository, diagnose, parse_edit, call_model

EDIT = '''FILE: pipeline.py
<<<OLD>>>
row["customer_id"]
<<<NEW>>>
row["customerId"]
<<<END>>>'''
def response(text, truncated=False):
    return {'content':text,'truncated':truncated,'elapsed_seconds':1,'generated_tokens':10,'tokens_per_second':10}

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repository('demo_repo')
        self.context = self.repo.context('customer_id pipeline.py')

    def test_parser_quotes_multiline_and_refusal(self):
        self.assertEqual(parse_edit(EDIT)['new_code'], 'row["customerId"]')
        self.assertIsNone(parse_edit('NO_EDIT'))
        multiline = EDIT.replace('row["customer_id"]', 'def f():\n    return row["customer_id"]')
        self.assertIn('\n    return', parse_edit(multiline)['old_code'])
        for value in (EDIT + '\nextra text', EDIT.replace('<<<END>>>',''), EDIT + '\n<<<END>>>'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_edit(value)

    @patch('doctor.call_model')
    def test_valid_two_call_flow_keeps_source_unchanged(self, mock):
        before = Path('demo_repo/pipeline.py').read_bytes()
        mock.side_effect = [response('Field-name mismatch.'), response(EDIT)]
        result = diagnose('customer_id', self.context, repo_path='demo_repo')
        self.assertEqual(result['edit_status'], 'checks_passed')
        self.assertEqual(mock.call_count, 2)
        self.assertIn('+    return [{"id": row["customerId"]}', result['answer'])
        self.assertEqual(before, Path('demo_repo/pipeline.py').read_bytes())

    @patch('doctor.call_model')
    def test_second_stage_failure_preserves_diagnosis(self, mock):
        mock.side_effect = [response('Field-name mismatch.'), RuntimeError('prediction aborted, token repeat limit reached')]
        result = diagnose('customer_id', self.context, repo_path='demo_repo')
        self.assertEqual(result['edit_status'], 'rejected')
        self.assertIn('Field-name mismatch.', result['answer'])
        self.assertIn('token repeat limit', result['error'])

    @patch('doctor.call_model')
    def test_truncated_first_stage_stops(self, mock):
        mock.return_value = response('partial', True)
        result = diagnose('customer_id', self.context, repo_path='demo_repo')
        self.assertEqual(mock.call_count, 1)
        self.assertTrue(result['output_truncated'])
        self.assertEqual(result['edit_status'], 'rejected')

    @patch('doctor.urllib.request.build_opener')
    def test_http_body_preserved(self, mock):
        mock.return_value.open.side_effect = urllib.error.HTTPError('http://localhost',500,'Error',{},io.BytesIO(b'{"error":"token repeat limit reached"}'))
        with self.assertRaisesRegex(RuntimeError, 'token repeat limit reached'):
            call_model('test','test','qwen3:1.7b')

if __name__ == '__main__':
    unittest.main()
