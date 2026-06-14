"""Load codebases from GitHub URLs or uploaded zip archives."""

from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlparse


class CodeLoadError(RuntimeError):
    """Raised when a repository or archive cannot be loaded."""


def clone_github_repository(repo_url: str, workspace_dir: Path) -> Path:
    """Clone a GitHub repository into the workspace directory."""
    if not repo_url.strip():
        raise CodeLoadError("Please provide a GitHub repository URL.")
    parsed = urlparse(repo_url)
    if parsed.scheme not in {"http", "https", "git", "ssh"} and not repo_url.startswith(
        "git@"
    ):
        raise CodeLoadError("Only GitHub repository URLs are supported.")
    if "github.com" not in repo_url:
        raise CodeLoadError("The repository URL must point to github.com.")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    repo_name = _repo_name_from_url(repo_url)
    target_dir = _unique_path(workspace_dir / repo_name)

    try:
        from git import Repo  # type: ignore

        Repo.clone_from(repo_url, target_dir)
    except Exception:
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            raise CodeLoadError(f"Failed to clone repository: {exc}") from exc

    return target_dir


def extract_zip_archive(zip_path: str | Path, workspace_dir: Path) -> Path:
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
            for member in archive.infolist():
                member_path = target_dir / member.filename
                resolved = member_path.resolve()
                if not str(resolved).startswith(str(target_dir.resolve())):
                    raise CodeLoadError("Unsafe zip path detected.")
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


def _collapse_single_root(path: Path) -> Path:
    entries = [entry for entry in path.iterdir() if not entry.name.startswith("__MACOSX")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return path
