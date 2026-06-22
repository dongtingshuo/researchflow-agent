import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.experiment.command_planner import CommandCandidate
from src.experiment.runner import run_command_candidate


def _candidate(command: str) -> CommandCandidate:
    return CommandCandidate(
        command=command,
        purpose="test",
        risk_level="safe",
        reason="test candidate",
        can_execute_by_default=True,
    )


class RunnerTests(unittest.TestCase):
    def test_repository_script_requires_explicit_trust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            marker = root / "executed.txt"
            (root / "inspect.py").write_text(
                "from pathlib import Path\nPath('executed.txt').write_text('yes')\n",
                encoding="utf-8",
            )

            result = run_command_candidate(
                _candidate("python inspect.py --dry-run"),
                cwd=root,
                output_dir=root / "outputs",
                dry_run=False,
            )

            self.assertFalse(result.executed)
            self.assertFalse(marker.exists())
            self.assertIn("explicit trust confirmation", result.error)

    def test_trusted_repository_script_runs_without_inheriting_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "inspect.py").write_text(
                "import os\nprint('key-visible:', bool(os.getenv('OPENAI_API_KEY')))\n",
                encoding="utf-8",
            )

            with patch.dict("os.environ", {"OPENAI_API_KEY": "not-for-child"}):
                result = run_command_candidate(
                    _candidate("python inspect.py --dry-run"),
                    cwd=root,
                    output_dir=root / "outputs",
                    dry_run=False,
                    allow_repository_scripts=True,
                )

            self.assertTrue(result.executed)
            self.assertEqual(result.returncode, 0)
            self.assertIn("key-visible: False", result.stdout)

    def test_repository_script_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "workspace"
            root.mkdir()
            outside = Path(tmpdir) / "outside.py"
            outside.write_text("print('outside')", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "escapes the workspace"):
                run_command_candidate(
                    _candidate("python ../outside.py --dry-run"),
                    cwd=root,
                    output_dir=root / "outputs",
                    dry_run=False,
                    allow_repository_scripts=True,
                )


if __name__ == "__main__":
    unittest.main()
