# Safety Notes

# 安全说明

## Safety Goal / 安全目标

ResearchFlow-Agent is designed for local research workflows. It can inspect papers and code repositories, but it should not silently run risky commands or claim that an experiment has been reproduced without evidence.

ResearchFlow-Agent 面向本地科研工作流。系统可以检查论文和代码仓库，但不应静默执行高风险命令，也不应在缺少证据时声称实验已经复现。

## Default Dry-Run / 默认 dry-run

The Reproduction workflow defaults to:

复现工作流默认使用：

```text
dry-run only
```

In this mode, commands are planned and saved as artifacts, but not executed.

该模式只生成和保存候选命令，不执行命令。

## Risk Levels / 风险等级

| Risk Level | Meaning | Default Execution |
| --- | --- | --- |
| `safe` | Low-risk inspection commands, such as `python script.py --help`. | May run only when user selects `run safe commands`. |
| `needs_confirm` | Training, dependency installation, repository scripts, or checkpoint-dependent commands. | Not executed by default. |
| `unsafe` | Destructive, privileged, shell-piped, or unparseable commands. | Blocked. |

## Blocked Patterns / 阻断模式

Commands are marked unsafe when they contain:

以下命令会被标记为 unsafe：

- `rm`
- `sudo`
- `curl`
- `wget`
- `curl | bash`
- shell pipes or redirects such as `|`, `>`, `<`, `;`, `&`
- shell executables such as `bash`, `sh`, `zsh`
- destructive utilities such as `dd`, `mkfs`, `shutdown`, `reboot`

## Repository and Zip Safety / 仓库与 Zip 安全

Existing repository loading rules still apply:

原有仓库加载规则继续生效：

- GitHub clone only accepts public HTTPS URLs in the `https://github.com/owner/repo` form.
- SSH URLs, non-GitHub domains, spoofed domains, query strings, and fragments are rejected.
- Zip extraction checks path traversal, absolute paths, symlinks, member count, and total size.
- Uploaded files, cloned repositories, vector stores, outputs, and `.env` are ignored by Git.

## Human Review / 人工复核

The system can help prepare reproduction commands and parse logs, but users should still review:

系统可以辅助准备复现命令和解析日志，但用户仍需人工核对：

- dataset paths
- checkpoint paths
- hardware requirements
- expected runtime
- dependency conflicts
- metric definitions
- paper table/page evidence
- whether reproduced metrics use the same dataset split as the paper

## Verifier Boundary / Verifier 边界

Verifier classifies paper, code, log, inference, and missing evidence. It is a risk and evidence-attribution tool, not a guarantee of factual correctness.

Verifier 用于区分论文、代码、日志、推断和缺失证据。它是风险提示和证据归因工具，不保证事实完全正确。
