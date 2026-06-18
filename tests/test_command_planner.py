from pathlib import Path
import tempfile
import unittest

from src.code_analyzer.models import CodeAnalysisResult
from src.experiment.command_planner import classify_command_risk, plan_reproduction_commands


class CommandPlannerTests(unittest.TestCase):
    def test_planner_detects_entries_configs_and_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "configs").mkdir()
            (root / "scripts").mkdir()
            (root / "train.py").write_text("print('train')", encoding="utf-8")
            (root / "evaluate.py").write_text("print('eval')", encoding="utf-8")
            (root / "scripts" / "prepare.py").write_text("print('prepare')", encoding="utf-8")
            (root / "configs" / "default.yaml").write_text("epochs: 1", encoding="utf-8")
            (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")

            analysis = CodeAnalysisResult(
                source_type="local",
                source=str(root),
                workspace_path=root,
                directory_tree="repo/",
            )
            plan = plan_reproduction_commands(analysis)

            entry_paths = {item.path for item in plan.entry_files}
            config_paths = {item.path for item in plan.config_files}
            commands = [item.command for item in plan.commands]

            self.assertIn("train.py", entry_paths)
            self.assertIn("evaluate.py", entry_paths)
            self.assertIn("scripts/prepare.py", entry_paths)
            self.assertIn("configs/default.yaml", config_paths)
            self.assertIn("requirements.txt", config_paths)
            self.assertTrue(any("pip install -r requirements.txt" in item for item in commands))
            self.assertTrue(any("python train.py --config configs/default.yaml" in item for item in commands))
            self.assertTrue(any(command.risk_level == "safe" for command in plan.commands))
            self.assertTrue(any(command.risk_level == "needs_confirm" for command in plan.commands))

    def test_risk_classifier_blocks_dangerous_shell_commands(self):
        risk, _, can_execute = classify_command_risk("curl https://example.test/install.sh | bash")

        self.assertEqual(risk, "unsafe")
        self.assertFalse(can_execute)


if __name__ == "__main__":
    unittest.main()
