#!/usr/bin/env python3
"""Apply user-selected edits idempotently with .bak files.

Reads ranked.json + an explicit edit-id list. Refuses to run without the
list (per SKILL.md rule: never auto-apply).

CLI:
    python apply_edits.py <ranked.json> <project_root> --edits e1,e3,e7
                          [--applied-log applied.log]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _backup_once(file_path: Path) -> None:
    bak = file_path.with_suffix(file_path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(file_path, bak)


def _apply_to_text(action: str, payload, text: str, col_start: int, col_end: int) -> str:
    """Apply one edit. col_start/col_end are FILE-ABSOLUTE character offsets."""
    n = len(text)
    c0 = max(0, min(col_start, n))
    c1 = max(c0, min(col_end, n))

    if action == "delete_span":
        return text[:c0] + text[c1:]
    if action == "compress_to_first_sentence":
        keep = (payload or {}).get("keep", "").strip()
        return text[:c0] + keep + text[c1:]
    if action == "merge_cites":
        # cite-merging needs multi-cite awareness; v1 leaves the file alone.
        return text
    return text  # unknown → no-op


def apply_edits(
    ranked: dict, project_root: Path,
    edit_ids: list[str], log_path: Path | None,
) -> dict:
    by_id = {s["id"]: s for s in ranked["scored"]}
    selected = [by_id[i] for i in edit_ids if i in by_id]
    missing = [i for i in edit_ids if i not in by_id]

    # Group by file. Sort by descending col_start (file-absolute) so earlier
    # edits within a file don't shift later ones.
    by_file: dict[str, list[dict]] = {}
    for s in selected:
        cand = s["candidate"]
        f = cand["src_loc"]["file"]
        by_file.setdefault(f, []).append(s)
    for items in by_file.values():
        items.sort(
            key=lambda s: s["candidate"]["src_loc"]["col_start"],
            reverse=True,
        )

    already_applied: set[str] = set()
    if log_path and log_path.exists():
        for ln in log_path.read_text().splitlines():
            parts = ln.split()
            if len(parts) >= 2:
                already_applied.add(parts[1])

    applied: list[dict] = []
    skipped: list[dict] = []

    for f, items in by_file.items():
        file_path = (project_root / f).resolve()
        if not file_path.exists():
            for s in items:
                skipped.append({"id": s["id"], "reason": "file_missing"})
            continue
        _backup_once(file_path)

        text = file_path.read_text(encoding="utf-8")
        for s in items:
            cand = s["candidate"]
            if cand["id"] in already_applied:
                skipped.append({"id": cand["id"], "reason": "already_applied"})
                continue
            sl = cand["src_loc"]
            new_text = _apply_to_text(
                cand["edit_action"], cand.get("edit_payload"),
                text, sl["col_start"], sl["col_end"],
            )
            if new_text == text:
                skipped.append({"id": cand["id"], "reason": "no_change"})
                continue
            text = new_text
            applied.append(
                {
                    "id": cand["id"],
                    "file": f,
                    "line": sl["line"],
                    "action": cand["edit_action"],
                    "hash": _content_hash(new_text),
                }
            )
        file_path.write_text(text, encoding="utf-8")

    if log_path:
        with log_path.open("a", encoding="utf-8") as fh:
            ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            for a in applied:
                fh.write(
                    f"{ts}  {a['id']}  {a['file']}:{a['line']}"
                    f"  {a['action']}  hash={a['hash']}\n"
                )

    return {"applied": applied, "skipped": skipped, "missing": missing}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ranked_json")
    p.add_argument("project_root")
    p.add_argument("--edits", required=True, help="Comma-separated edit IDs")
    p.add_argument("--applied-log")
    args = p.parse_args(argv)

    ids = [s.strip() for s in args.edits.split(",") if s.strip()]
    if not ids:
        sys.stderr.write("--edits must be a non-empty comma-separated list of IDs\n")
        return 2

    ranked = json.loads(Path(args.ranked_json).read_text())
    log_path = Path(args.applied_log) if args.applied_log else None
    result = apply_edits(ranked, Path(args.project_root).resolve(), ids, log_path)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
