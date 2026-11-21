import tempfile
from pathlib import Path
import unittest
from mavengraph.visualize import to_dot, render


class VisualizationTests(unittest.TestCase):
    def test_escaping_isolated_root_and_cycle(self):
        dot = to_dot({'A"': ["B"], "B": ['A"'], "C": []}, "C")
        self.assertIn('"A\\"" -> "B";', dot)
        self.assertIn('"C" [fillcolor=', dot)
        self.assertIn('"B" -> "A\\"";', dot)

    def test_missing_renderer_preserves_dot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "graph.svg"
            with self.assertRaisesRegex(ValueError, "не найден"):
                render(
                    {"A": []},
                    "A",
                    output,
                    executable=str(Path(directory) / "missing-dot"),
                )
            self.assertTrue(output.with_suffix(".dot").is_file())
