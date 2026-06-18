"""Safe subprocess runner for reproduction commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
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
) -> CommandRunResult:
    """Run or dry-run one candidate command with safety checks."""
    risk, reason, can_execute = classify_command_risk(candidate.command)
    workspace = Path(cwd).resolve()
    target_output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    run_dir = target_output_dir / "experiment_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / _run_filename()

    should_execute = (
        not dry_run
        and risk != "unsafe"
        and (risk == "safe" or allow_needs_confirm)
        and (can_execute or allow_needs_confirm)
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
) -> list[CommandRunResult]:
    """Run or dry-run all candidates, executing only safe commands."""
    return [
        run_command_candidate(
            candidate,
            cwd=cwd,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            dry_run=dry_run,
            allow_needs_confirm=False,
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
