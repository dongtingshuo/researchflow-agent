# Troubleshooting

# 常见问题排查

## Gradio Fails to Start / Gradio 无法启动

Check that dependencies are installed in the active environment:

确认依赖已安装在当前环境：

```bash
pip install -r requirements.txt
python app.py
```

If another service is using the same port, restart the app and use the URL printed by Gradio.

如果端口被占用，请重启应用并使用 Gradio 输出的本地 URL。

## Missing Dependencies / 缺少依赖

Use a dedicated environment:

建议使用独立环境：

```bash
conda create -n researchflow python=3.11
conda activate researchflow
pip install -r requirements.txt
```

For test and contribution workflows, use `pip install -r requirements-dev.txt`.

运行测试或参与开发时，请使用 `pip install -r requirements-dev.txt`。

## PDF Parsing Fails / PDF 解析失败

Possible causes:

可能原因：

- The PDF is scanned image content without extractable text.
- PDF 是扫描图像，缺少可抽取文本。
- The file is encrypted or damaged.
- 文件加密或损坏。
- The parser cannot map the text layout cleanly.
- 解析器无法稳定映射文本布局。

Try another PDF or run OCR before uploading scanned documents.

可尝试更换 PDF，或先对扫描文档做 OCR。

## GitHub Clone Fails / GitHub 仓库 Clone 失败

ResearchFlow-Agent accepts public HTTPS repository URLs in the `https://github.com/owner/repo` form.

ResearchFlow-Agent 接受 `https://github.com/owner/repo` 形式的公开 HTTPS 仓库 URL。

Check:

检查：

- URL format
- URL 格式
- network access
- 网络访问
- repository visibility
- 仓库可访问性
- clone timeout
- clone 超时时间
- configured post-clone size limit
- 配置的 clone 后仓库体积限制

## LLM Uses the Local Fallback / LLM 使用本地 Fallback

External content transmission is opt-in. Configure the endpoint and key, then set `ALLOW_EXTERNAL_CONTENT_TO_LLM=true` only when sending paper and repository excerpts to that provider is acceptable.

外部内容传输默认关闭。配置接口和密钥后，仅在确认可以向该服务商发送论文和仓库片段时设置 `ALLOW_EXTERNAL_CONTENT_TO_LLM=true`。

## Demo Does Not Generate a Report / Demo 没有生成报告

Run:

```bash
python scripts/run_reproduction_demo.py --run-safe
```

Expected report:

预期报告：

```text
data/outputs/reproduction_demo/reproduction_report.md
```

If the report is missing, check terminal errors and make sure the repository root is the working directory.

如果报告缺失，请查看终端错误，并确认当前目录是项目根目录。

## Pytest Cannot Run / pytest 无法运行

Basic command:

基础命令：

```bash
python -m pytest -q
```

If the current shell has no `python` command, use the project conda environment:

如果当前 shell 没有 `python` 命令，可使用项目 conda 环境：

```bash
conda run -n researchflow python -m pytest -q
```

If `python3` exists but pytest is missing, install dependencies in the selected environment.

如果存在 `python3` 但缺少 pytest，请在选定环境中安装依赖。

## CUDA Is Unavailable / CUDA 不可用

The project is designed to run on CPU for local workflow checks. The toy demo does not require CUDA.

项目的本地工作流检查可在 CPU 上运行。toy demo 不需要 CUDA。

For third-party repositories, review their own hardware requirements before running training or evaluation commands.

对于第三方仓库，请在运行训练或评估命令前检查其硬件要求。

## Why Dry-Run by Default / 为什么默认 dry-run

Repository commands can modify environments, require datasets, run for a long time, or assume specific hardware. Dry-run mode makes command planning visible before execution.

仓库命令可能修改环境、依赖数据集、运行时间较长或假设特定硬件。dry-run 模式可以先展示命令规划，再决定是否执行。

Repository scripts run only after the explicit trust option is selected. Risk classification and the trust gate reduce accidental execution but do not provide a full sandbox.

只有显式选择信任选项后才会运行仓库脚本。风险分类和信任门可减少误执行，但不构成完整沙箱。
