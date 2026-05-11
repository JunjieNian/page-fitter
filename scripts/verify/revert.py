#!/usr/bin/env python3
"""Restore every .bak under a project root.

CLI:
    python revert.py <project_root> [--force]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def revert(project_root: Path, force: bool) -> dict:
    restored = []
    refused = []
    for bak in project_root.rglob("*.bak"):
        target = bak.with_suffix("")  # strip .bak
        if target.exists():
            target_mt = target.stat().st_mtime
            bak_mt = bak.stat().st_mtime
            # If the .tex was edited *after* the .bak was created, force is
            # required (otherwise we'd silently destroy unrelated work).
            if target_mt > bak_mt and not force:
                refused.append(
                    {
                        "bak": str(bak.relative_to(project_root)),
                        "reason": "target newer than backup; pass --force to override",
                    }
                )
                continue
        shutil.copy2(bak, target)
        restored.append(str(target.relative_to(project_root)))
    return {"restored": restored, "refused": refused}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("project_root")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    out = revert(Path(args.project_root).resolve(), args.force)
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
