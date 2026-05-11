#!/usr/bin/env python3
"""Walk a LaTeX project's AST via pylatexenc.

Yields editable nodes. We do NOT try to be a perfect LaTeX parser;
pylatexenc handles the bulk and we accept the rest as "skip and warn."

CLI:
    python parse_latex.py <main.tex> [--out <json>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _import_pylatexenc():
    try:
        from pylatexenc.latexwalker import (
            LatexCharsNode,
            LatexEnvironmentNode,
            LatexGroupNode,
            LatexMacroNode,
            LatexWalker,
        )
        return LatexWalker, LatexEnvironmentNode, LatexMacroNode, LatexCharsNode, LatexGroupNode
    except ImportError:  # pragma: no cover
        sys.stderr.write("pylatexenc (`pip install pylatexenc`) is required.\n")
        raise


HARD_EXCLUDE_ENVS = {"abstract", "thebibliography"}
PROOF_ENVS = {"proof"}


def _read_inputs(main_tex: Path) -> dict[str, str]:
    """Return {relative_path: text} for the main file plus any \\input{}/\\include{}."""
    project_root = main_tex.parent
    seen: dict[str, str] = {}
    queue = [main_tex]
    while queue:
        f = queue.pop()
        rel = str(f.relative_to(project_root))
        if rel in seen:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            continue
        seen[rel] = txt
        # naive include detection (sufficient for v1)
        for m in re.finditer(r"\\(?:input|include)\{([^}]+)\}", txt):
            target = m.group(1)
            if not target.endswith(".tex"):
                target = target + ".tex"
            queue.append((project_root / target).resolve())
    return seen


def _line_of_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def walk_file(rel_path: str, source: str):
    """Yield editable-node dicts from one tex file."""
    LatexWalker, *_ = _import_pylatexenc()
    walker = LatexWalker(source)
    nodelist, _, _ = walker.get_latex_nodes()
    yield from _walk_nodes(rel_path, source, nodelist, env_stack=[])


def _walk_nodes(rel_path, source, nodes, env_stack):
    _, LatexEnvironmentNode, LatexMacroNode, LatexCharsNode, LatexGroupNode = _import_pylatexenc()
    for node in nodes:
        if isinstance(node, LatexEnvironmentNode):
            env_name = node.environmentname
            if env_name in HARD_EXCLUDE_ENVS:
                continue
            new_stack = env_stack + [env_name]
            # surface caption macros inside figure/table envs by recursing
            yield from _walk_nodes(rel_path, source, node.nodelist, new_stack)
            continue

        if isinstance(node, LatexMacroNode):
            mname = node.macroname
            if mname == "caption":
                # Find the (last non-None) argument node — usually a LatexGroupNode
                # for `\caption{...}`. Emit the absolute file span of the inner text.
                arg_node = None
                if node.nodeargd and node.nodeargd.argnlist:
                    for a in node.nodeargd.argnlist:
                        if a is not None:
                            arg_node = a
                if arg_node is not None and getattr(arg_node, "pos", None) is not None:
                    gpos = arg_node.pos
                    glen = getattr(arg_node, "len", None) or 0
                    if glen and source[gpos:gpos + 1] == "{":
                        inner_start = gpos + 1
                        inner_end = gpos + glen - 1
                    else:
                        inner_start = gpos
                        inner_end = gpos + glen
                    inner_text = source[inner_start:inner_end]
                    if inner_text.strip():
                        yield {
                            "kind": "caption",
                            "file": rel_path,
                            "line": _line_of_offset(source, inner_start),
                            "col_start": inner_start,
                            "col_end": inner_end,
                            "text": inner_text,
                            "env_stack": list(env_stack),
                        }
                continue
            if mname in {"cite", "citep", "citet"}:
                pos = node.pos
                yield {
                    "kind": "cite",
                    "file": rel_path,
                    "line": _line_of_offset(source, pos),
                    "col_start": pos,
                    "col_end": getattr(node, "pos_end", pos + 1),
                    "text": _macro_arg_text(node) or "",
                    "env_stack": list(env_stack),
                }
                continue
            # fall through to recurse into macro args (for \emph{...} etc.)
            for arg in (node.nodeargd.argnlist if node.nodeargd else []):
                if arg is None:
                    continue
                if hasattr(arg, "nodelist"):
                    yield from _walk_nodes(rel_path, source, arg.nodelist, env_stack)
            continue

        if isinstance(node, LatexCharsNode):
            text = node.chars
            if not text.strip():
                continue
            pos = node.pos
            yield {
                "kind": "chars",
                "file": rel_path,
                "line": _line_of_offset(source, pos),
                "col_start": pos,
                "col_end": pos + len(text),
                "text": text,
                "env_stack": list(env_stack),
            }
            continue

        if isinstance(node, LatexGroupNode):
            yield from _walk_nodes(rel_path, source, node.nodelist, env_stack)


def _macro_arg_text(macro_node) -> str:
    if not macro_node.nodeargd or not macro_node.nodeargd.argnlist:
        return ""
    pieces = []
    for arg in macro_node.nodeargd.argnlist:
        if arg is None:
            continue
        if hasattr(arg, "latex_verbatim"):
            try:
                pieces.append(arg.latex_verbatim())
                continue
            except Exception:
                pass
        if hasattr(arg, "chars"):
            pieces.append(arg.chars)
    return " ".join(pieces).strip()


def parse_project(main_tex: Path) -> dict:
    files = _read_inputs(main_tex)
    nodes = []
    for rel, src in files.items():
        try:
            for n in walk_file(rel, src):
                nodes.append(n)
        except Exception as e:
            sys.stderr.write(f"warning: parse error in {rel}: {e}\n")
    return {"files": list(files.keys()), "nodes": nodes}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("main_tex")
    p.add_argument("--out")
    args = p.parse_args(argv)
    parsed = parse_project(Path(args.main_tex).resolve())
    text = json.dumps(parsed, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
