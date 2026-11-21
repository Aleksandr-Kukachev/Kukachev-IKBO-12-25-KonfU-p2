import json
import tempfile
from pathlib import Path
import unittest
from mavengraph.repository import TestRepository, RepositoryError


class TestRepositoryTests(unittest.TestCase):
    def test_validation(self):
        cases = [
            "[",
            "[]",
            '{"a": []}',
            '{"A": "B"}',
            '{"A": [42]}',
            '{"A": ["B"]}',
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.json"
            for value in cases:
                with self.subTest(value=value):
                    path.write_text(value, encoding="utf-8")
                    with self.assertRaises(RepositoryError):
                        TestRepository(path)

    def test_missing_root_and_duplicate_edge(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.json"
            path.write_text(json.dumps({"A": ["B", "B"], "B": []}))
            repo = TestRepository(path)
            self.assertEqual(repo.dependencies("A"), ["B"])
            with self.assertRaises(RepositoryError):
                repo.dependencies("Z")
