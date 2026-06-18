"""Code-aware reproduction command planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import shlex

from src.code_analyzer.models import CodeAnalysisResult


ENTRY_NAMES = {
    "train.py": "training",
    "evaluate.py": "evaluation",
    "eval.py": "evaluation",
    "test.py": "evaluation",
    "infer.py": "inference",
    "inference.py": "inference",
    "demo.py": "demo",
    "main.py": "main",
}

CONFIG_NAMES = {
    "config.py",
    "requirements.txt",
    "pyproject.toml",
    "environment.yml",
    "environment.yaml",
}

DANGEROUS_TOKENS = {
    "rm",
    "sudo",
    "curl",
    "wget",
    "chmod",
    "chown",
    "dd",
    "mkfs",
    "shutdown",
    "reboot",
    "kill",
    "pkill",
    "nc",
    "bash",
    "sh",
    "zsh",
}

SHELL_METACHARS = re.compile(r"[|;&><`$]")


@dataclass(frozen=True)
class EntryFile:
    """A possible Python entry point for reproduction."""

    path: str
    kind: str
    exists: bool = True


@dataclass(frozen=True)
class ConfigFile:
    """A configuration or dependency file found in a repository."""

    path: str
    kind: str
    exists: bool = True


@dataclass(frozen=True)
class CommandCandidate:
    """One candidate command with explicit risk metadata."""

    command: str
    purpose: str
    risk_level: str
    reason: str
    entry_file: str = ""
    config_file: str = ""
    can_execute_by_default: bool = False

    def argv(self) -> list[str]:
        """Return a shell-free argv representation of the command."""
        return shlex.split(self.command)


@dataclass(frozen=True)
class CommandPlan:
    """Candidate commands and repository execution evidence."""

    workspace_path: Path
    entry_files: list[EntryFile] = field(default_factory=list)
    config_files: list[ConfigFile] = field(default_factory=list)
    commands: list[CommandCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the command plan as Markdown."""
        lines = [
            "# Reproduction Command Plan",
            "",
            f"- Workspace: `{self.workspace_path}`",
            "",
            "## Entry Files",
        ]
        if self.entry_files:
            lines.extend(f"- `{item.path}` ({item.kind})" for item in self.entry_files)
        else:
            lines.append("- No likely entry file was detected.")

        lines.extend(["", "## Config and Dependency Files"])
        if self.config_files:
            lines.extend(f"- `{item.path}` ({item.kind})" for item in self.config_files)
        else:
            lines.append("- No configuration or dependency file was detected.")

        lines.extend(["", "## Candidate Commands"])
        if self.commands:
            lines.extend(
                f"- `{item.command}` | risk: `{item.risk_level}` | {item.purpose}. {item.reason}"
                for item in self.commands
            )
        else:
            lines.append("- No candidate commands were generated.")

        if self.warnings:
            lines.extend(["", "## Warnings"])
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


def plan_reproduction_commands(
    code_analysis: CodeAnalysisResult,
    user_notes: str = "",
) -> CommandPlan:
    """Generate safe-by-default reproduction command candidates."""
    workspace = code_analysis.workspace_path
    entry_files = _discover_entry_files(workspace)
    config_files = _discover_config_files(workspace)
    commands: list[CommandCandidate] = []
    warnings: list[str] = []

    requirements = _find_config(config_files, "requirements.txt")
    if requirements is not None:
        commands.append(
            _candidate(
                f"pip install -r {shlex.quote(requirements.path)}",
                purpose="Install Python dependencies",
                reason="Dependency installation changes the local environment and may require network access.",
                entry_file="",
                config_file=requirements.path,
            )
        )

    environment = _find_kind(config_files, "conda_environment")
    if environment is not None:
        commands.append(
            _candidate(
                f"conda env update -f {shlex.quote(environment.path)}",
                purpose="Update a conda environment from environment file",
                reason="Environment updates can modify packages and may require network access.",
                config_file=environment.path,
            )
        )

    default_config = _preferred_runtime_config(config_files)
    for entry in entry_files:
        commands.extend(_commands_for_entry(entry, default_config))

    if not entry_files:
        warnings.append("No Python training, evaluation, inference, demo, main, or scripts entry file was found.")
    if user_notes.strip():
        warnings.append(f"User notes were not executed automatically: {user_notes.strip()}")

    commands = [_with_risk(command) for command in commands]
    return CommandPlan(
        workspace_path=workspace,
        entry_files=entry_files,
        config_files=config_files,
        commands=commands,
        warnings=warnings,
    )


def classify_command_risk(command: str) -> tuple[str, str, bool]:
    """Classify a command as safe, needs_confirm, or unsafe."""
    if SHELL_METACHARS.search(command):
        return "unsafe", "Shell metacharacters are not allowed in planned commands.", False

    try:
        argv = shlex.split(command)
    except ValueError:
        return "unsafe", "Command cannot be parsed safely.", False
    if not argv:
        return "unsafe", "Empty command.", False

    lowered = [part.lower() for part in argv]
    if any(part in DANGEROUS_TOKENS for part in lowered):
        return "unsafe", "Command contains a blocked executable or destructive operation.", False
    if lowered[:2] == ["python", "--version"] or lowered[:2] == ["python3", "--version"]:
        return "safe", "Python version inspection is low risk.", True
    if "--help" in lowered and lowered[0] in {"python", "python3"}:
        return "safe", "Help command is treated as a low-risk inspection command.", True
    if "--dry-run" in lowered and lowered[0] in {"python", "python3"}:
        return "safe", "Dry-run repository command is treated as a low-risk inspection command.", True
    if lowered[0] in {"pip", "conda"} or "install" in lowered:
        return "needs_confirm", "Dependency or environment modification requires user confirmation.", False
    if any("train.py" in part or part.endswith("/train.py") for part in lowered):
        return "needs_confirm", "Training commands may be long-running and require datasets or hardware.", False
    if lowered[0] in {"python", "python3"}:
        return "needs_confirm", "Repository Python scripts require user confirmation before execution.", False
    return "needs_confirm", "Command is not in the low-risk allowlist.", False


def _discover_entry_files(workspace: Path) -> list[EntryFile]:
    entries: list[EntryFile] = []
    seen: set[str] = set()
    for path in sorted(workspace.rglob("*.py"), key=lambda item: str(item).lower()):
        if _ignored(path, workspace):
            continue
        relative = path.relative_to(workspace).as_posix()
        name = path.name.lower()
        kind = ENTRY_NAMES.get(name)
        if kind is None and relative.startswith("scripts/"):
            kind = "script"
        if kind is None:
            continue
        if relative in seen:
            continue
        seen.add(relative)
        entries.append(EntryFile(path=relative, kind=kind))
    return sorted(entries, key=_entry_priority)


def _discover_config_files(workspace: Path) -> list[ConfigFile]:
    configs: list[ConfigFile] = []
    seen: set[str] = set()
    for path in sorted(workspace.rglob("*"), key=lambda item: str(item).lower()):
        if not path.is_file() or _ignored(path, workspace):
            continue
        relative = path.relative_to(workspace).as_posix()
        lower = relative.lower()
        kind = ""
        if path.name.lower() in CONFIG_NAMES:
            kind = _config_kind(path.name.lower())
        elif lower.startswith("configs/") and path.suffix.lower() in {".yaml", ".yml"}:
            kind = "runtime_config"
        if not kind or relative in seen:
            continue
        seen.add(relative)
        configs.append(ConfigFile(path=relative, kind=kind))
    return sorted(configs, key=_config_priority)


def _commands_for_entry(
    entry: EntryFile,
    config: ConfigFile | None,
) -> list[CommandCandidate]:
    commands = [
        CommandCandidate(
            command=f"python {shlex.quote(entry.path)} --help",
            purpose=f"Inspect {entry.kind} command-line options",
            risk_level="safe",
            reason="Help output can reveal expected arguments without starting a run.",
            entry_file=entry.path,
            can_execute_by_default=True,
        )
    ]
    config_arg = f" --config {shlex.quote(config.path)}" if config is not None else ""
    if entry.kind == "training":
        commands.append(
            CommandCandidate(
                command=f"python {shlex.quote(entry.path)}{config_arg}",
                purpose="Run a training entry point",
                risk_level="needs_confirm",
                reason="Training may require datasets, checkpoints, GPU, and a long runtime.",
                entry_file=entry.path,
                config_file=config.path if config is not None else "",
            )
        )
    elif entry.kind in {"evaluation", "inference"}:
        commands.append(
            CommandCandidate(
                command=f"python {shlex.quote(entry.path)} --dry-run{config_arg}",
                purpose=f"Run {entry.kind} dry-run or smoke-test mode",
                risk_level="safe",
                reason="Dry-run mode should expose expected logs without running a full experiment.",
                entry_file=entry.path,
                config_file=config.path if config is not None else "",
                can_execute_by_default=True,
            )
        )
        commands.append(
            CommandCandidate(
                command=f"python {shlex.quote(entry.path)}{config_arg}",
                purpose=f"Run {entry.kind}",
                risk_level="needs_confirm",
                reason="Evaluation or inference may require checkpoints and dataset paths.",
                entry_file=entry.path,
                config_file=config.path if config is not None else "",
            )
        )
    elif entry.kind in {"demo", "main", "script"}:
        commands.append(
            CommandCandidate(
                command=f"python {shlex.quote(entry.path)}{config_arg}",
                purpose=f"Run {entry.kind} entry point",
                risk_level="needs_confirm",
                reason="Repository scripts should be manually reviewed before execution.",
                entry_file=entry.path,
                config_file=config.path if config is not None else "",
            )
        )
    return commands


def _candidate(
    command: str,
    purpose: str,
    reason: str,
    entry_file: str = "",
    config_file: str = "",
) -> CommandCandidate:
    risk, risk_reason, can_execute = classify_command_risk(command)
    return CommandCandidate(
        command=command,
        purpose=purpose,
        risk_level=risk,
        reason=f"{reason} {risk_reason}".strip(),
        entry_file=entry_file,
        config_file=config_file,
        can_execute_by_default=can_execute,
    )


def _with_risk(command: CommandCandidate) -> CommandCandidate:
    risk, reason, can_execute = classify_command_risk(command.command)
    return CommandCandidate(
        command=command.command,
        purpose=command.purpose,
        risk_level=risk,
        reason=command.reason if command.risk_level == risk else reason,
        entry_file=command.entry_file,
        config_file=command.config_file,
        can_execute_by_default=can_execute,
    )


def _find_config(configs: list[ConfigFile], path: str) -> ConfigFile | None:
    return next((item for item in configs if item.path.lower() == path.lower()), None)


def _find_kind(configs: list[ConfigFile], kind: str) -> ConfigFile | None:
    return next((item for item in configs if item.kind == kind), None)


def _preferred_runtime_config(configs: list[ConfigFile]) -> ConfigFile | None:
    runtime_configs = [item for item in configs if item.kind == "runtime_config"]
    if not runtime_configs:
        return None
    return sorted(runtime_configs, key=lambda item: ("default" not in item.path.lower(), item.path))[0]


def _config_kind(name: str) -> str:
    if name == "requirements.txt":
        return "pip_requirements"
    if name in {"environment.yml", "environment.yaml"}:
        return "conda_environment"
    if name == "pyproject.toml":
        return "python_project"
    return "runtime_config"


def _entry_priority(item: EntryFile) -> tuple[int, str]:
    order = {
        "training": 0,
        "evaluation": 1,
        "inference": 2,
        "demo": 3,
        "main": 4,
        "script": 5,
    }
    return order.get(item.kind, 99), item.path


def _config_priority(item: ConfigFile) -> tuple[int, str]:
    order = {
        "pip_requirements": 0,
        "python_project": 1,
        "conda_environment": 2,
        "runtime_config": 3,
    }
    return order.get(item.kind, 99), item.path


def _ignored(path: Path, workspace: Path) -> bool:
    ignored_parts = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
    }
    try:
        relative_parts = path.relative_to(workspace).parts
    except ValueError:
        return True
    return any(part in ignored_parts for part in relative_parts)
