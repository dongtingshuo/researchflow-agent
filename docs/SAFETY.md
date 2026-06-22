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
| `safe` | Low-risk command shape. Repository Python scripts still require explicit trust. | Runs only after the relevant execution gate is enabled. |
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
- Git clone uses a timeout, disables interactive credential prompts, and rejects repositories above the configured post-clone size limit.
- SSH URLs, non-GitHub domains, spoofed domains, query strings, and fragments are rejected.
- Zip extraction checks path traversal, absolute paths, symlinks, member count, and total size.
- Uploaded files, cloned repositories, vector stores, outputs, and `.env` are ignored by Git.

## Repository Script Trust / 仓库脚本信任

`--help` and `--dry-run` are conventions, not isolation mechanisms. A Python script can execute arbitrary top-level code before parsing either flag. ResearchFlow-Agent therefore blocks repository scripts unless the user explicitly confirms that the repository has been reviewed and trusted.

`--help` 和 `--dry-run` 只是约定，不是隔离机制。Python 脚本可能在解析这些参数前执行任意顶层代码，因此系统会阻止未被显式检查和信任的仓库脚本。

When execution is enabled, script paths must remain inside the workspace and child processes receive a sanitized environment without API keys. This is still not a full sandbox; untrusted repositories should be executed in an isolated container or virtual machine.

启用执行后，脚本路径必须位于工作区内，子进程也不会继承 API key。该机制仍不是完整沙箱；不可信仓库应在隔离容器或虚拟机中执行。

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
