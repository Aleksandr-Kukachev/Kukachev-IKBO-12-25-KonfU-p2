import contextlib
import io
import unittest
from mavengraph.cli import options


class CliTests(unittest.TestCase):
    def test_invalid_options(self):
        base = ["--package", "g:a:1", "--repository", "https://example.org"]
        cases = [(["--package", "bad"], "пакет Maven"),
                 (["--repository", "ftp://example.org"], "HTTP(S)"),
                 (["--test-mode=true"], "explicit argument"),
                 (["--test-mode"], "тестовое имя"),
                 (["--max-depth", "-1"], "неотрицательной"),
                 (["--max-depth", "abc"], "invalid int"),
                 (["--filter", "a"], "корневой"),
                 (["--filter", "\n"], "управляющие")]
        for extra, expected in cases:
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as raised:
                    options(base + extra)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(expected, err.getvalue())

    def test_defaults(self):
        self.assertEqual(options(["--package", "g:a:1", "--repository", "https://example.org"]).max_depth, 10)
