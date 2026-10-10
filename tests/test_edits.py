import tempfile
import unittest
from pathlib import Path
from doctor import Repository, validate_edit, parse_edit

class EditTests(unittest.TestCase):
    def test_good_edit_and_rejections(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'job.py'
            original = 'def transform(row):\n    return row["customer_id"]\n'
            file.write_text(original)
            repo = Repository(d)
            context = repo.context('customer_id')
            edit = {'path':'job.py','old_code':'    return row["customer_id"]','new_code':'    return row["customerId"]','explanation':'Map upstream key'}
            diff = validate_edit(edit, repo, context)
            self.assertIn('-    return row["customer_id"]', diff)
            self.assertIn('+    return row["customerId"]', diff)
            self.assertEqual(file.read_text(), original)
            for changes in ({'new_code':edit['old_code']}, {'old_code':'missing'}, {'path':'../escape.py'}, {'new_code':'    return ['}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    validate_edit({**edit, **changes}, repo, context)
            file.write_text(original + original)
            with self.assertRaises(ValueError):
                validate_edit(edit, repo, context)
            with self.assertRaises(ValueError):
                parse_edit('{invalid')


if __name__ == '__main__':
    unittest.main()
