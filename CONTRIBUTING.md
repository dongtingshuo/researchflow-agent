# Contributing

# 贡献指南

Thank you for improving ResearchFlow-Agent. This project is designed as a modular, local-first research workflow tool. Contributions should keep the workflow inspectable, testable, and evidence-aware.

感谢改进 ResearchFlow-Agent。本项目定位为模块化、本地优先的科研工作流工具。贡献应保持流程可检查、可测试、证据可追踪。

## Environment Setup / 环境安装

```bash
conda create -n researchflow python=3.11
conda activate researchflow
pip install -r requirements-dev.txt
cp .env.example .env
```

Keep credentials and local paths out of Git.

请勿将凭据和本地私有路径提交到 Git。

## Run Tests / 运行测试

Basic test command:

基础测试命令：

```bash
python -m pytest -q
```

Conda environment:

使用 conda 环境：

```bash
conda run -n researchflow python -m pytest -q
```

Format check:

格式检查：

```bash
git diff --check
```

## Run Demo / 运行演示

Dry-run:

```bash
python scripts/run_reproduction_demo.py
```

Run the bundled, reviewed toy repository commands:

运行项目内置且已检查的 toy 仓库命令：

```bash
python scripts/run_reproduction_demo.py --run-safe
```

Generated files under `data/outputs/` should not be committed.

`data/outputs/` 下的生成文件不应提交到 Git。

## Code Style / 代码风格

- Keep modules small and focused.
- 保持模块小而清晰。
- Use type hints for new public functions.
- 新增公开函数应使用类型标注。
- Use `pathlib.Path` for file paths.
- 文件路径使用 `pathlib.Path`。
- Prefer deterministic local fallbacks when model calls are unavailable.
- 模型调用不可用时优先提供确定性本地 fallback。
- Do not put all logic in `app.py`; keep core logic under `src/`.
- 不要把所有逻辑放进 `app.py`；核心逻辑应放在 `src/`。

## Tests / 测试要求

Add or update tests when changing:

以下变更应新增或更新测试：

- paper parsing or result extraction
- 论文解析或结果抽取
- retrieval and QA behavior
- 检索和问答行为
- repository analysis
- 仓库分析
- command planning and runner behavior
- 命令规划和 runner 行为
- log parsing and result comparison
- 日志解析和结果对比
- verifier checks
- Verifier 检查
- report generation
- 报告生成

## Do Not Commit / 不应提交

- credentials or local secrets
- 凭据或本地 secret
- large datasets
- 大型数据集
- model weights or checkpoints
- 模型权重或 checkpoint
- generated files under `data/outputs/`
- `data/outputs/` 下的生成文件
- uploaded PDFs or cloned repositories
- 上传的 PDF 或 clone 的仓库
- local cache directories
- 本地缓存目录
