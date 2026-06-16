"""Code analyzer package."""

from src.code_analyzer.analyzer import (
    analyze_codebase,
    analyze_github_repository,
    analyze_zip_archive,
    generate_directory_tree,
    identify_key_files,
    read_key_file_contents,
)
from src.code_analyzer.models import CodeAnalysisResult, KeyFile

__all__ = [
    "CodeAnalysisResult",
    "KeyFile",
    "analyze_codebase",
    "analyze_github_repository",
    "analyze_zip_archive",
    "generate_directory_tree",
    "identify_key_files",
    "read_key_file_contents",
]
