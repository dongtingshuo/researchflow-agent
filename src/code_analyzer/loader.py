"""Load codebases from GitHub URLs or uploaded zip archives."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from config import Settings


DEFAULT_GIT_CLONE_TIMEOUT_SECONDS = 120
DEFAULT_MAX_CLONE_TOTAL_BYTES = 500_000_000
DEFAULT_MAX_ZIP_MEMBERS = 4000
DEFAULT_MAX_ZIP_TOTAL_BYTES = 150_000_000


class CodeLoadError(RuntimeError):
    """Raised when a repository or archive cannot be loaded."""


def clone_github_repository(
    repo_url: str,
    workspace_dir: Path,
    settings: Settings | None = None,
) -> Path:
    """Clone a GitHub repository into the workspace directory."""
    normalized_url = normalize_github_url(repo_url)
    timeout = (
        settings.git_clone_timeout_seconds
        if settings is not None
        else DEFAULT_GIT_CLONE_TIMEOUT_SECONDS
    )

    workspace_dir.mkdir(parents=True, exist_ok=True)
    repo_name = _repo_name_from_url(normalized_url)
    target_dir = _unique_path(workspace_dir / repo_name)

    clone_env = os.environ.copy()
    clone_env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--no-tags",
                normalized_url,
                str(target_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=max(1, timeout),
            env=clone_env,
        )
        max_bytes = (
            settings.max_clone_total_bytes
            if settings is not None
            else DEFAULT_MAX_CLONE_TOTAL_BYTES
        )
        clone_size = _directory_size(target_dir)
        if clone_size > max_bytes:
            raise CodeLoadError(
                f"Cloned repository is too large ({clone_size} bytes > {max_bytes})."
            )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise CodeLoadError(
            f"Repository clone timed out after {timeout} seconds."
        ) from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(target_dir, ignore_errors=True)
        detail = (exc.stderr or "").strip()
        if detail:
            detail = detail[-500:]
        raise CodeLoadError(
            f"Failed to clone repository{f': {detail}' if detail else '.'}"
        ) from exc
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise

    return target_dir


def extract_zip_archive(
    zip_path: str | Path,
    workspace_dir: Path,
    settings: Settings | None = None,
) -> Path:
    """Safely extract an uploaded zip archive into the workspace directory."""
    source = Path(zip_path)
    if not source.exists():
        raise CodeLoadError(f"Zip archive does not exist: {source}")
    if source.suffix.lower() != ".zip":
        raise CodeLoadError("Please upload a .zip code archive.")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    target_dir = _unique_path(workspace_dir / _safe_name(source.stem))
    target_dir.mkdir(parents=True, exist_ok=False)

    try:
        with zipfile.ZipFile(source) as archive:
            _validate_zip_archive(
                archive,
                target_dir,
                max_members=(
                    settings.max_zip_members
                    if settings is not None
                    else DEFAULT_MAX_ZIP_MEMBERS
                ),
                max_total_bytes=(
                    settings.max_zip_total_bytes
                    if settings is not None
                    else DEFAULT_MAX_ZIP_TOTAL_BYTES
                ),
            )
            for member in archive.infolist():
                if _is_ignored_zip_member(member):
                    continue
                resolved = _safe_zip_member_path(target_dir, member.filename)
                if member.is_dir():
                    resolved.mkdir(parents=True, exist_ok=True)
                else:
                    resolved.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as src, resolved.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile as exc:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise CodeLoadError("The uploaded archive is not a valid zip file.") from exc
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise

    return _collapse_single_root(target_dir)


def normalize_github_url(repo_url: str) -> str:
    """Validate and normalize a public GitHub repository URL."""
    raw_url = repo_url.strip()
    if not raw_url:
        raise CodeLoadError("Please provide a GitHub repository URL.")
    if raw_url.startswith("git@") or raw_url.startswith("ssh://"):
        raise CodeLoadError(
            "For safety, only public HTTPS GitHub URLs are supported."
        )

    parsed = urlparse(raw_url)
    if parsed.scheme != "https":
        raise CodeLoadError("Only HTTPS GitHub repository URLs are supported.")
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise CodeLoadError("The repository URL must point to github.com.")
    if parsed.query or parsed.fragment:
        raise CodeLoadError("Repository URLs must not contain query strings or fragments.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise CodeLoadError("Use a repository URL in the form https://github.com/owner/repo.")
    owner, repo = parts
    name_pattern = re.compile(r"^[A-Za-z0-9_.-]+$")
    if not name_pattern.fullmatch(owner) or not name_pattern.fullmatch(repo):
        raise CodeLoadError("Repository owner and name contain unsupported characters.")
    repo = repo.removesuffix(".git")
    if repo in {"", ".", ".."} or owner in {"", ".", ".."}:
        raise CodeLoadError("Repository owner and name are invalid.")
    return f"https://github.com/{owner}/{repo}.git"


def _repo_name_from_url(repo_url: str) -> str:
    if repo_url.startswith("git@"):
        raw_name = repo_url.rsplit(":", 1)[-1].rsplit("/", 1)[-1]
    else:
        raw_name = urlparse(repo_url).path.rstrip("/").rsplit("/", 1)[-1]
    return _safe_name(raw_name.removesuffix(".git") or "repository")


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-._")
    return cleaned or "workspace"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.name}-{index}")
        if not candidate.exists():
            return candidate
    raise CodeLoadError(f"Could not allocate a workspace path for {path.name}.")


def _directory_size(path: Path) -> int:
    """Return the total size of regular files without following symlinks."""
    total = 0
    for item in path.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        try:
            total += item.stat().st_size
        except OSError:
            continue
    return total


def _validate_zip_archive(
    archive: zipfile.ZipFile,
    target_dir: Path,
    max_members: int,
    max_total_bytes: int,
) -> None:
    members = archive.infolist()
    if len(members) > max_members:
        raise CodeLoadError(
            f"Zip archive contains too many files ({len(members)} > {max_members})."
        )

    total_size = 0
    for member in members:
        if _is_ignored_zip_member(member):
            continue
        if _is_zip_symlink(member):
            raise CodeLoadError("Unsafe zip symlink detected.")
        _safe_zip_member_path(target_dir, member.filename)
        total_size += member.file_size
        if total_size > max_total_bytes:
            raise CodeLoadError(
                f"Zip archive is too large after extraction ({total_size} bytes)."
            )


def _safe_zip_member_path(target_dir: Path, member_name: str) -> Path:
    if not member_name or "\x00" in member_name:
        raise CodeLoadError("Unsafe zip path detected.")
    member_path = Path(member_name)
    if member_path.is_absolute():
        raise CodeLoadError("Unsafe zip path detected.")
    resolved = (target_dir / member_path).resolve()
    try:
        resolved.relative_to(target_dir.resolve())
    except ValueError as exc:
        raise CodeLoadError("Unsafe zip path detected.") from exc
    return resolved


def _is_zip_symlink(member: zipfile.ZipInfo) -> bool:
    mode = member.external_attr >> 16
    return (mode & 0o170000) == 0o120000


def _is_ignored_zip_member(member: zipfile.ZipInfo) -> bool:
    return member.filename.startswith("__MACOSX/") or member.filename.endswith(".DS_Store")


def _collapse_single_root(path: Path) -> Path:
    entries = [entry for entry in path.iterdir() if not entry.name.startswith("__MACOSX")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return path
