import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from doctor import Repository, call_model


class RepositoryTests(unittest.TestCase):
    def test_retrieves_failure_and_blocks_escape_and_secrets(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / "job.py").write_text("def run(row):\n    return row['customer_id']\n")
            (root / ".env").write_text("PASSWORD=not-real")
            (root / "secrets.py").write_text("secret = 'not-real'")
            (Path(outside) / "other.py").write_text("outside = True")
            (root / "link.py").symlink_to(Path(outside) / "other.py")
            repo = Repository(root)
            self.assertEqual(repo.files, ["job.py"])
            context = repo.context("KeyError: customer_id")
            self.assertIn("job.py", context)
            self.assertIn("2:     return", context)
            with self.assertRaises(ValueError):
                repo.read_file("../other.py")
            with self.assertRaises(ValueError):
                repo.read_file("link.py")

    def test_empty_match_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "job.py").write_text("value = 123\n" * 200)
            repo = Repository(directory)
            self.assertEqual(repo.context("unrelated"), "")
            self.assertLessEqual(len(repo.context("value", budget=200)), 200)

    @patch("doctor.urllib.request.build_opener")
    def test_ollama_contract_and_metrics(self, build):
        response = MagicMock()
        response.read.return_value = json.dumps({"message": {"content": "Diagnosis"}, "eval_count": 10, "eval_duration": 2_000_000_000}).encode()
        build.return_value.open.return_value.__enter__.return_value = response
        result = call_model("Investigate", "KeyError", "qwen3:1.7b")
        self.assertEqual(result["tokens_per_second"], 5)
        request = build.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        payload = json.loads(request.data)
        self.assertTrue(payload["think"])
        self.assertNotIn("format", payload)
        self.assertEqual(payload["options"]["num_ctx"], 4096)


if __name__ == "__main__":
    unittest.main()
