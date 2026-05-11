#!/usr/bin/env python3
"""Single CLI entry point for the page-fitter skill.

Subcommands:
    analyze <main.tex> [--out <state-dir>] [--triage] [--page-limit N] [--force]
    verify  <main.tex> --edits e1,e3,e7
    revert  <main.tex> [--force]

Each subcommand orchestrates the per-layer scripts under ../{compile_state,
candidates,layout,scoring,verify}/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS / "compile_state"))
sys.path.insert(0, str(SCRIPTS / "candidates"))
sys.path.insert(0, str(SCRIPTS / "layout"))
sys.path.insert(0, str(SCRIPTS / "scoring"))
sys.path.insert(0, str(SCRIPTS / "verify"))

import snapshot  # noqa: E402
import generate_candidates  # noqa: E402
import paragraph_lines  # noqa: E402
import float_risk  # noqa: E402
import rank as rank_mod  # noqa: E402
import apply_edits as apply_mod  # noqa: E402
import recompile as recompile_mod  # noqa: E402
import revert as revert_mod  # noqa: E402


def _state_dir(main_tex: Path, override: str | None) -> Path:
    if override:
        d = Path(override).resolve()
    else:
        d = main_tex.parent / ".page-fitter"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_analyze(args) -> int:
    main_tex = Path(args.main_tex).resolve()
    sd = _state_dir(main_tex, args.out)

    state = snapshot.build_snapshot(main_tex, force=args.force, compiler=args.compiler)
    (sd / "state.json").write_text(json.dumps(state, indent=2))

    candidates = generate_candidates.generate_candidates(
        state, filter_near_boundary=(args.filter == "near-boundary")
    )
    (sd / "candidates.json").write_text(json.dumps(candidates, indent=2))

    layout = paragraph_lines.compute_layout(state, candidates, fast=args.triage)
    (sd / "layout.json").write_text(json.dumps(layout, indent=2))

    floats = float_risk.compute_float_risk(state, candidates)
    (sd / "floats.json").write_text(json.dumps(floats, indent=2))

    semantic = None
    sem_path = sd / "semantic.json"
    if sem_path.exists() and not args.triage:
        semantic = json.loads(sem_path.read_text())

    ranked = rank_mod.rank(
        state, candidates, layout, floats, semantic,
        triage=args.triage, page_limit=args.page_limit,
    )
    (sd / "ranked.json").write_text(json.dumps(ranked, indent=2))
    (sd / "report.md").write_text(rank_mod.render_report(ranked, triage=args.triage))

    summary = {
        "state_dir": str(sd),
        "report": str(sd / "report.md"),
        "ranked": str(sd / "ranked.json"),
        "summary": ranked["summary"],
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return 0


def cmd_verify(args) -> int:
    """Recompile and report page-count diff.

    By default this DOES NOT modify any source file — the agent is expected to
    have made edits with its own editing tool (using the analyze report as a
    guide). Pass `--apply-edits e1,e3,...` to fall back to the mechanical
    span-deleter (NOT recommended; it cannot do semantically-aware compression
    or grammar fixups).
    """
    main_tex = Path(args.main_tex).resolve()
    sd = _state_dir(main_tex, args.out)

    state_path = sd / "state.json"
    if not state_path.exists():
        sys.stderr.write(f"state.json missing in {sd}. Run `analyze` first.\n")
        return 2
    state = json.loads(state_path.read_text())
    old_pages = state["pdf"]["page_count"]

    apply_result = None
    if args.apply_edits:
        ranked_path = sd / "ranked.json"
        if not ranked_path.exists():
            sys.stderr.write(f"ranked.json missing in {sd}. Run `analyze` first.\n")
            return 2
        ranked = json.loads(ranked_path.read_text())
        ids = [s.strip() for s in args.apply_edits.split(",") if s.strip()]
        if not ids:
            sys.stderr.write("--apply-edits must list at least one ID.\n")
            return 2
        apply_log = sd / "applied.log"
        apply_result = apply_mod.apply_edits(ranked, main_tex.parent, ids, apply_log)

    rc_argv = [str(main_tex), "--old-page-count", str(old_pages)]
    if args.compiler:
        rc_argv += ["--compiler", args.compiler]
    rc_result = recompile_mod.main(rc_argv)
    if apply_result is not None:
        sys.stdout.write(json.dumps({"applied": apply_result}, indent=2) + "\n")
    return rc_result


def cmd_revert(args) -> int:
    main_tex = Path(args.main_tex).resolve()
    out = revert_mod.revert(main_tex.parent, args.force)
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="page-fitter")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="Run the full 4-layer analysis pipeline.")
    a.add_argument("main_tex")
    a.add_argument("--out", help="state directory (default: <project>/.page-fitter)")
    a.add_argument("--triage", action="store_true", help="Skip LLM semantic-cost pass; use type-class medians.")
    a.add_argument("--page-limit", type=int, default=None)
    a.add_argument("--force", action="store_true", help="Force recompile even if state.json is fresh.")
    a.add_argument("--filter", choices=["near-boundary"], default=None)
    a.add_argument("--compiler", default=None,
                   help="Override compiler command (e.g. 'pdflatex' or 'xelatex --shell-escape'). "
                        "Auto-detects latexmk/pdflatex/xelatex/lualatex if omitted. "
                        "Can also be set via PAGE_FITTER_LATEX_CMD.")
    a.set_defaults(func=cmd_analyze)

    v = sub.add_parser(
        "verify",
        help="Recompile and report page-count diff. By default does NOT modify source — "
             "the agent is expected to have made the edits itself.",
    )
    v.add_argument("main_tex")
    v.add_argument("--out", help="state directory (default: <project>/.page-fitter)")
    v.add_argument("--compiler", default=None,
                   help="Override compiler command (same options as for `analyze`).")
    v.add_argument("--apply-edits", default=None,
                   help="(Opt-in, NOT recommended) Comma-separated candidate IDs to "
                        "mechanically delete via apply_edits.py before recompiling. "
                        "Prefer letting the agent edit with semantic awareness instead.")
    v.set_defaults(func=cmd_verify)

    r = sub.add_parser("revert", help="Restore every .bak under the project root.")
    r.add_argument("main_tex")
    r.add_argument("--force", action="store_true")
    r.set_defaults(func=cmd_revert)

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
