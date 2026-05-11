# page-fitter

A Claude Code skill for trimming LaTeX papers to fit hard page limits
(NeurIPS 9p, ACL 8p, ICML, etc.) **by impact on the rendered PDF**, not by
source length.

## Why?

Deleting many lines from `.tex` may shrink the PDF by zero pages, while
deleting half a sentence at the right spot can collapse a paragraph by one
line and cascade into half a page. `page-fitter` reverse-maps the current
PDF state to LaTeX source via SyncTeX, ranks candidate edits by their
*PDF-height impact* and *page-boundary leverage*, and explicitly flags
"not worth editing" regions a naive LLM would otherwise suggest.

## Quickstart

```bash
# from a fresh Claude Code session, in your LaTeX project:
/page-fitter
```

Or call the CLI directly:

```bash
python3 scripts/cli/page_fitter.py analyze main.tex
# review report.md, pick edit IDs, then:
python3 scripts/cli/page_fitter.py verify main.tex --edits e1,e3,e7
```

## Install

```bash
pip install -r requirements.txt
# globally register the skill (symlink lives outside the project):
ln -s "$(pwd)" ~/.claude/skills/page-fitter
```

## Pipeline

`compile-state snapshot → candidate enumeration → layout analysis →
boundary-leverage scoring → ⛔ user selection → verification compile`

See `SKILL.md` for the full workflow and `references/architecture.md` for
the design rationale.

## Out of scope (v1)

- Trained ML model for layout-gain prediction (heuristics only).
- Sentence-paraphrasing — `page-fitter` *suggests* edits; rewriting is the
  user's job (or a separate writing skill).
- Build systems other than `latexmk` (no Tectonic, no `make`).
