"""Safe subprocess runner for reproduction commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Iterable
from uuid import uuid4

from config import OUTPUT_DIR
from src.experiment.command_planner import CommandCandidate, classify_command_risk


@dataclass(frozen=True)
class CommandRunResult:
    """Captured command execution result."""

    command: str
    cwd: str
    dry_run: bool
    executed: bool
    risk_level: str
    returncode: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    output_path: Path
    error: str = ""

    def combined_log(self) -> str:
        """Return stdout and stderr as a single text log."""
        blocks = []
        if self.stdout:
            blocks.append(self.stdout)
        if self.stderr:
            blocks.append(self.stderr)
        if self.error:
            blocks.append(self.error)
        return "\n".join(blocks)


def run_command_candidate(
    candidate: CommandCandidate,
    cwd: str | Path,
    output_dir: str | Path | None = None,
    timeout_seconds: int = 30,
    max_output_chars: int = 8000,
    dry_run: bool = True,
    allow_needs_confirm: bool = False,
    allow_repository_scripts: bool = False,
) -> CommandRunResult:
    """Run or dry-run one candidate command with explicit trust checks."""
    risk, reason, can_execute = classify_command_risk(candidate.command)
    workspace = Path(cwd).resolve()
    if not workspace.exists() or not workspace.is_dir():
        raise ValueError(f"Command workspace is not a directory: {workspace}")
    repository_script = (
        _repository_script_path(candidate.argv(), workspace)
        if risk != "unsafe"
        else None
    )
    repository_script_allowed = repository_script is None or allow_repository_scripts
    target_output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    run_dir = target_output_dir / "experiment_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / _run_filename()

    should_execute = (
        not dry_run
        and risk != "unsafe"
        and (risk == "safe" or allow_needs_confirm)
        and (can_execute or allow_needs_confirm)
        and repository_script_allowed
    )
    started = time.monotonic()
    stdout = ""
    stderr = ""
    returncode: int | None = None
    error = ""

    if should_execute:
        try:
            completed = subprocess.run(
                candidate.argv(),
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=max(1, timeout_seconds),
                check=False,
                env=_sanitized_environment(),
            )
            stdout = _trim(completed.stdout, max_output_chars)
            stderr = _trim(completed.stderr, max_output_chars)
            returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = _trim(exc.stdout or "", max_output_chars)
            stderr = _trim(exc.stderr or "", max_output_chars)
            error = f"Command timed out after {timeout_seconds} seconds."
            returncode = None
        except OSError as exc:
            error = f"Command execution failed: {exc}"
            returncode = None
    else:
        if dry_run:
            error = _dry_run_reason(dry_run, risk, reason)
        elif not repository_script_allowed:
            error = (
                "Repository script execution requires explicit trust confirmation, "
                "even when --help or --dry-run is present."
            )
        else:
            error = _dry_run_reason(dry_run, risk, reason)

    duration = time.monotonic() - started
    result = CommandRunResult(
        command=candidate.command,
        cwd=str(workspace),
        dry_run=dry_run,
        executed=should_execute,
        risk_level=risk,
        returncode=returncode,
        duration_seconds=round(duration, 4),
        stdout=stdout,
        stderr=stderr,
        output_path=output_path,
        error=error,
    )
    _save_result(result)
    return result


def run_safe_commands(
    candidates: Iterable[CommandCandidate],
    cwd: str | Path,
    output_dir: str | Path | None = None,
    timeout_seconds: int = 30,
    max_output_chars: int = 8000,
    dry_run: bool = True,
    allow_repository_scripts: bool = False,
) -> list[CommandRunResult]:
    """Run or dry-run candidates, with repository scripts blocked by default."""
    return [
        run_command_candidate(
            candidate,
            cwd=cwd,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            dry_run=dry_run,
            allow_needs_confirm=False,
            allow_repository_scripts=allow_repository_scripts,
        )
        for candidate in candidates
        if candidate.risk_level == "safe" or dry_run
    ]


def _save_result(result: CommandRunResult) -> None:
    payload = asdict(result)
    payload["output_path"] = str(result.output_path)
    result.output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _run_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return f"run-{timestamp}-{uuid4().hex[:8]}.json"


def _dry_run_reason(dry_run: bool, risk: str, reason: str) -> str:
    if dry_run:
        return "Dry-run mode: command was not executed."
    if risk == "unsafe":
        return f"Blocked unsafe command: {reason}"
    return f"Command requires confirmation: {reason}"


def _trim(text: str | bytes, limit: int) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 80)] + "\n...[output truncated by ResearchFlow-Agent]..."


def _repository_script_path(argv: list[str], workspace: Path) -> Path | None:
    """Validate and return a Python repository script referenced by argv."""
    if len(argv) < 2 or argv[0].lower() not in {"python", "python3"}:
        return None
    script_arg = argv[1]
    if script_arg.startswith("-"):
        return None
    script_path = (workspace / script_arg).resolve()
    try:
        script_path.relative_to(workspace)
    except ValueError as exc:
        raise ValueError("Repository script path escapes the workspace.") from exc
    if script_path.suffix.lower() != ".py":
        raise ValueError("Only Python script files can be executed by the runner.")
    if not script_path.exists() or not script_path.is_file():
        raise ValueError(f"Repository script does not exist: {script_arg}")
    return script_path


def _sanitized_environment() -> dict[str, str]:
    """Pass only runtime essentials to repository subprocesses."""
    allowed = {
        "PATH",
        "HOME",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "PYTHONIOENCODING",
        "CONDA_PREFIX",
        "VIRTUAL_ENV",
        "SYSTEMROOT",
        "WINDIR",
    }
    environment = {key: value for key, value in os.environ.items() if key in allowed}
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment
