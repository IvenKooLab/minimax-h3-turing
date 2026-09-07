"""CLI tests - no GPU required (doctor failure path is exercised against a
dead endpoint, which is the normal state outside a render box)."""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from h3turing.cli import main  # noqa: E402


class TestCLI(unittest.TestCase):
    def test_tiers_lists_and_exits_zero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["tiers"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        for key in ("t2v-final", "t2v-ultra", "i2v-ultra"):
            self.assertIn(key, out)
        self.assertIn("NOT same-seed reproducible", out)

    def test_doctor_fail_exits_one_when_comfyui_down(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["doctor", "--base", "http://127.0.0.1:9"])
        self.assertEqual(code, 1)
        self.assertIn("comfyui_alive", buf.getvalue())

    def test_bench_rejects_unknown_tier(self):
        with self.assertRaises(KeyError):
            main(["bench", "--a", "nope", "--b", "t2v-final"])


if __name__ == "__main__":
    unittest.main()
