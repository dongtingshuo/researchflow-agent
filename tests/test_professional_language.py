from pathlib import Path
import unittest


TEXT_PATHS = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/evaluation_report.md"),
    Path("docs/demo_guide.md"),
    Path("docs/project_summary.md"),
    Path("docs/technical_overview.md"),
    Path("docs/EXPERIMENT_RUNNER.md"),
    Path("docs/REPRODUCTION_WORKFLOW.md"),
    Path("docs/SAFETY.md"),
    Path("docs/PROJECT_OVERVIEW.md"),
    Path("docs/DEMO_RECORDING_GUIDE.md"),
    Path("docs/TROUBLESHOOTING.md"),
    Path("docs/API_REFERENCE.md"),
    Path("docs/PROJECT_STRUCTURE.md"),
    Path("docs/ROADMAP.md"),
    Path("examples/validation_results.md"),
    Path("examples/validation_workflows.md"),
    Path("examples/reproduction_demo/sample_paper_excerpt.md"),
    Path("examples/reproduction_demo/expected_outputs/reproduction_report.md"),
]


class ProfessionalLanguageTests(unittest.TestCase):
    def test_public_docs_avoid_personal_positioning_terms(self):
        blocked_terms = [
            "port" + "folio",
            "res" + "ume",
            "graduate school " + "appli" + "cation",
            "appli" + "cation " + "material",
            "undergraduate " + "port" + "folio",
            "research " + "proposal",
            "job " + "hunting",
            "C" + "V",
            "大学" + "院",
            "申" + "请",
            "导" + "师",
            "面" + "试官",
            "申" + "请" + "材料",
            "作品" + "集",
            "简" + "历",
            "套" + "磁",
            "申" + "请" + "项目",
            "申" + "请" + "展示",
            "给" + "导" + "师看",
            "本科" + "生",
            "课程" + "设计",
            "求" + "职",
            "升" + "学",
        ]
        for path in TEXT_PATHS:
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                for term in blocked_terms:
                    self.assertNotIn(term.lower(), text)

    def test_readme_contains_required_professional_sections(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        required_sections = [
            "Project Positioning / 项目定位",
            "Core Features / 核心功能",
            "System Architecture / 系统架构",
            "Tech Stack / 技术栈",
            "Installation / 安装",
            "Configuration / 配置",
            "Usage / 使用流程",
            "Evaluation and Validation / 评测与验证",
            "Security Notes / 安全设计",
            "Verifier Design / Verifier 设计",
            "Testing / 测试",
            "Known Limitations / 已知局限",
            "Roadmap / 后续计划",
        ]
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, readme)


if __name__ == "__main__":
    unittest.main()
