import tempfile
import unittest
import zipfile
from pathlib import Path

from config import Settings
from src.code_analyzer import analyze_codebase, analyze_zip_archive
from src.code_analyzer.analyzer import generate_directory_tree, identify_key_files
from src.code_analyzer.loader import CodeLoadError, extract_zip_archive


class CodeAnalyzerTests(unittest.TestCase):
    def test_generate_tree_and_identify_key_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo", encoding="utf-8")
            (root / "requirements.txt").write_text("torch", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "model.py").write_text("class Model: pass", encoding="utf-8")
            (root / "src" / "dataset.py").write_text("class Dataset: pass", encoding="utf-8")
            (root / "train.py").write_text("print('train')", encoding="utf-8")

            tree = generate_directory_tree(root)
            key_files = identify_key_files(root)
            paths = {item.path for item in key_files}

        self.assertIn("README.md", tree)
        self.assertIn("src/", tree)
        self.assertIn("README.md", paths)
        self.assertIn("requirements.txt", paths)
        self.assertIn("src/model.py", paths)
        self.assertIn("src/dataset.py", paths)
        self.assertIn("train.py", paths)

    def test_analyze_codebase_without_llm_returns_local_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            root.mkdir()
            (root / "README.md").write_text("Image classifier", encoding="utf-8")
            (root / "inference.py").write_text("print('infer')", encoding="utf-8")

            settings = Settings(workspace_dir=Path(tmpdir) / "workspaces")
            result = analyze_codebase(root, "local", "fixture", settings)

        self.assertIn("project/", result.directory_tree)
        self.assertIn("inference.py", result.key_files_markdown())
        self.assertIn("推理入口", result.summary)

    def test_analyze_zip_archive_extracts_and_analyzes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            archive_path = tmp / "code.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("sample/README.md", "# Sample")
                archive.writestr("sample/demo.py", "print('demo')")
                archive.writestr("sample/config.yaml", "batch_size: 4")

            settings = Settings(workspace_dir=tmp / "workspaces")
            result = analyze_zip_archive(archive_path, settings)
            paths = {item.path for item in result.key_files}

        self.assertEqual(result.source_type, "zip")
        self.assertIn("README.md", paths)
        self.assertIn("demo.py", paths)
        self.assertIn("config.yaml", paths)

    def test_extract_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            archive_path = tmp / "bad.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.py", "print('bad')")

            with self.assertRaises(CodeLoadError):
                extract_zip_archive(archive_path, tmp / "workspaces")


if __name__ == "__main__":
    unittest.main()
