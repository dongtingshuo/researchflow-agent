"""Toy training entry point for the reproduction demo.

This script intentionally avoids real training. It prints a short message so
the command planner can detect a training entry point without requiring data.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Toy training script.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.dry_run:
        print(f"training dry-run: config={args.config}")
        return 0
    print("Toy training is intentionally not executed in this demo.")
    print("Use evaluate.py --dry-run for the reproducible smoke-test output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
