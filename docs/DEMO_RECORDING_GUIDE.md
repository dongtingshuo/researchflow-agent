# Demo Recording Guide

# 演示录制指南

## Start Gradio / 启动 Gradio

```bash
python app.py
```

Open the local Gradio URL printed in the terminal.

打开终端输出中的本地 Gradio URL。

## Recommended Demo Flow / 推荐演示流程

1. Open the **Paper QA** tab.
2. Upload a paper PDF or use a small local example.
3. Show paper-grounded QA with page citations.
4. Open the **Code Analysis** tab.
5. Analyze `examples/reproduction_demo/toy_repo/` through a zip upload, or use a public GitHub URL.
6. Open the **Reproduction / 论文复现** tab.
7. Use dry-run mode to show command planning.
8. Use `run safe commands` to show log parsing and report generation with the toy repository.
9. Open the generated Markdown report.

中文流程：

1. 打开 **Paper QA** Tab。
2. 上传论文 PDF，或使用小型本地示例。
3. 展示带页码引用的 paper-grounded QA。
4. 打开 **Code Analysis** Tab。
5. 通过 zip 上传分析 `examples/reproduction_demo/toy_repo/`，或使用公开 GitHub URL。
6. 打开 **Reproduction / 论文复现** Tab。
7. 使用 dry-run 展示命令规划。
8. 使用 `run safe commands` 展示日志解析和报告生成。
9. 打开生成的 Markdown report。

## Recommended Screenshots / 推荐截图

- Home screen
- Paper QA
- Code Analysis
- Reproduction Tab
- Generated report
- Verifier result

中文建议截图：

- 首页
- Paper QA
- Code Analysis
- Reproduction Tab
- 生成的 report
- Verifier result

## Recording Suggestions / 录屏建议

- Keep the recording around 2 to 3 minutes.
- 建议录屏时长控制在 2 到 3 分钟。
- Do not show API keys.
- 不展示 API key。
- Do not show private local paths.
- 不展示本地隐私路径。
- Do not show personal private information.
- 不展示个人隐私信息。
- Keep the explanation accurate and restrained.
- 讲解保持准确、克制。
- Focus on the complete workflow.
- 重点展示完整工作流。
- Show the dry-run-first safety design.
- 展示 dry-run 优先的安全设计。
- Show the final `reproduction_report.md`.
- 展示最终的 `reproduction_report.md`。

## Notes / 注意事项

- Do not show `.env`.
- 不展示 `.env`。
- Do not show real API keys.
- 不展示真实 API key。
- Do not show private paths or private files.
- 不展示私人路径或私人文件。
- Do not describe the toy demo as a real benchmark result.
- 不要把 toy demo 描述成真实 benchmark 结果。
- Do not claim the system can reproduce arbitrary papers automatically.
- 不要声称系统可以自动复现任意论文。
- Use professional workflow-oriented wording.
- 使用面向工作流的专业表述。
