"""Проверки поведения после переноса пакета и разделения функций."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mavengraph.cli import main, options
from mavengraph.repository import MavenRepository, RepositoryError


class RegressionTests(unittest.TestCase):
    def test_output_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "graph.json"
            source.write_text('{"A": ["B"], "B": []}', encoding="utf-8")
            base = [
                "--test-mode",
                "--package",
                "A",
                "--repository",
                str(source),
            ]
            for mode in ("config", "direct", "graph", "order", "dot"):
                with self.subTest(mode=mode):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(main(base + ["--mode", mode]), 0)
                    text = output.getvalue()
                    if mode == "graph":
                        self.assertEqual(
                            json.loads(text), {"A": ["B"], "B": []}
                        )
                    elif mode == "direct":
                        self.assertEqual(text, "B\n")
                    elif mode == "order":
                        self.assertEqual(text, "B\nA\n")
                    elif mode == "dot":
                        self.assertIn('"A" -> "B";', text)
                    else:
                        self.assertIn("test_mode=True", text)

    def test_image_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "graph.json"
            source.write_text('{"A": []}', encoding="utf-8")
            args = [
                "--test-mode",
                "--package",
                "A",
                "--repository",
                str(source),
                "--mode",
                "image",
            ]
            with patch("mavengraph.visualize.render") as render:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(args), 0)
                render.assert_called_once_with(
                    {"A": []}, "A", "build/graph.svg", "dot", False
                )

    def test_invalid_output_and_urls(self):
        base = ["--package", "g:a:1", "--repository", "https://example.org"]
        cases = [
            ["--show"],
            ["--mode", "image", "--output", "bad.pdf"],
            ["--repository", "https://user:pass@example.org"],
            ["--repository", "https://example.org?query=yes"],
            ["--repository", "https://example.org#part"],
            ["--repository", "https://example.org:bad"],
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        options(base + extra)
                    self.assertEqual(raised.exception.code, 2)

    def test_rejected_xml_does_not_poison_active_set(self):
        for xml in (
            b"<broken",
            b"<notproject/>",
            b"<!DOCTYPE project><project/>",
        ):
            with self.subTest(xml=xml):
                repo = MavenRepository("https://example.org", lambda _: xml)
                with self.assertRaises(RepositoryError):
                    repo.model("g:a:1")
                self.assertEqual(repo.active, set())
                repo.fetch = lambda _: b"<project/>"
                self.assertEqual(repo.dependencies("g:a:1"), [])

    def test_child_properties_do_not_modify_parent(self):
        parent = b"<project><properties><x>parent</x></properties></project>"
        child = (
            b"<project><parent><groupId>g</groupId><artifactId>p</artifactId>"
            b"<version>1</version></parent><properties><x>child</x>"
            b"</properties></project>"
        )
        repo = MavenRepository(
            "https://example.org",
            lambda url: parent if "/p/" in url else child,
        )
        self.assertEqual(repo.model("g:a:1")[0]["x"], "child")
        self.assertEqual(repo.model("g:p:1")[0]["x"], "parent")
