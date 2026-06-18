"""Toy evaluation script for the reproduction demo.

The script emits deterministic metrics and does not download data or load a
model. It is designed for validating the local reproduction workflow.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Toy evaluation script.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    print(f"mode: {'dry-run' if args.dry_run else 'evaluation'}")
    print(f"config: {config_path.as_posix()}")
    print("dataset: toy-cifar")
    print("accuracy: 84.9")
    print("loss: 0.35")
    print("f1: 0.82")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
