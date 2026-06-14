import tempfile
import unittest
from pathlib import Path

from src.code_analyzer.models import CodeAnalysisResult, KeyFile
from src.evaluation.verifier import verify_workflow_outputs


class VerifierTests(unittest.TestCase):
    def test_verifier_classifies_evidence_and_uncertainty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code_analysis = CodeAnalysisResult(
                source_type="github",
                source="https://github.com/example/repo",
                workspace_path=Path(tmpdir),
                directory_tree="repo/\n|-- train.py\n`-- model.py",
                key_files=[
                    KeyFile("train.py", "train.py", "Training entry point."),
                    KeyFile("model.py", "model.py", "Model definition."),
                ],
                summary="## 训练入口\n`train.py`\n\n## 模型定义位置\n`model.py`",
            )

            result = verify_workflow_outputs(
                paper_summary=(
                    "## 研究问题\n"
                    "- Page 1: This paper studies compact neural networks."
                ),
                code_analysis=code_analysis,
                experiment_plan=(
                    "# 实验复现计划\n"
                    "## 实验目标\n建议先跑最小实验。\n"
                    "## 环境配置\nPython 3.11。\n"
                    "## 依赖安装\n需要人工确认。\n"
                    "## 数据集准备\n未识别，需要人工确认。\n"
                    "## 训练步骤\npython train.py\n"
                    "## 测试步骤\nTBD\n"
                    "## 指标记录方式\n记录 Accuracy。\n"
                    "## 实验结果表格模板\nTBD\n"
                    "## 可能遇到的问题\n依赖冲突。\n"
                    "## 降低复现难度的简化方案\n可以使用小数据集。"
                ),
                project_report=(
                    "# 项目报告\n"
                    "## 项目背景\n"
                    "## 相关工作\n"
                    "## 方法原理\n"
                    "## 系统设计\n"
                    "## 实验环境\n"
                    "## 实验步骤\n"
                    "## 实验结果记录表\n待填写\n"
                    "## 结果分析\n"
                    "## 总结与展望\n"
                    "模型达到 99% accuracy。"
                ),
            )

        markdown = result.to_markdown()

        self.assertTrue(result.passed)
        self.assertGreaterEqual(len(result.paper_evidence), 1)
        self.assertGreaterEqual(len(result.code_evidence), 1)
        self.assertGreaterEqual(len(result.model_inferences), 1)
        self.assertGreaterEqual(len(result.missing_evidence), 1)
        self.assertGreaterEqual(len(result.human_review_needed), 1)
        self.assertGreaterEqual(len(result.possible_hallucinations), 1)
        self.assertIn("1. 来自论文的内容", markdown)
        self.assertIn("6. 可能存在幻觉的内容", markdown)
        self.assertIn("不能保证生成内容 100% 正确", markdown)


if __name__ == "__main__":
    unittest.main()
