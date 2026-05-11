# Workflow: `verify` (recompile + report)

The agent has already edited the `.tex` files in Step 6 of `SKILL.md`. This
workflow runs the only re-compile of the session and reports the page-count
change. It does NOT touch source files by default.

## 🚧 GATE

- `analyze` (or `triage`) has been run; `.page-fitter/state.json` exists.
- ⛔ Step 5 has occurred: the user has approved a subset of candidate IDs.
- Step 6 has occurred: the AGENT has applied those edits using its editor
  tool (Edit/Write/MultiEdit), making `.bak` copies for every touched file
  before editing.

## Steps

### 1. Recompile

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py verify <main.tex>
```

`recompile.py` invokes the auto-detected compiler
(`latexmk` → `pdflatex` → `xelatex` → `lualatex`, overridable with
`--compiler` or `PAGE_FITTER_LATEX_CMD`) on the now-edited source, and
captures the new page count from the resulting PDF.

### 2. Report

The CLI prints:

```
{
  "old_page_count": 3,
  "new_page_count": 2,
  "delta": -1,
  "pdf": "/abs/path/main.pdf"
}
```

Interpretation:

- `delta < 0` → success; the agent's edits achieved a real PDF-page reduction.
- `delta == 0` → the edits collapsed lines but not pages. Surface this honestly to the user; suggest one more high-leverage edit.
- `delta > 0` → a float almost certainly reflowed unfavorably. Offer to revert and re-rank with that float's neighbors penalized; consult `references/float-placement.md`.

### 3. Cleanup decision (user-driven)

The agent does NOT auto-delete `.bak` files. Ask the user:

- "Keep `.bak` files for safety, or remove them?" — wait for explicit response.

## Opt-in: mechanical `--apply-edits`

A legacy code path exists for users who explicitly want a fully scripted run:

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py verify <main.tex> \
  --apply-edits c001,c003,c007
```

This calls `apply_edits.py` to mechanically delete the candidate spans
before recompiling. It is **NOT recommended**:

- It cannot fix grammar (e.g., capitalization after a deleted "Furthermore,").
- It cannot do semantic compression (e.g., "It is worth noting that, X" → "X").
- It is fragile against unresolved macros (pylatexenc may misparse
  `\lipsum[N][M]`-style optional args, so the candidate's span includes
  trailing macro residue and deleting it corrupts the document).

Use it only as a sanity check, never as the primary editing path.

## Revert

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py revert <main.tex>
```

`revert.py` restores every `.bak` under the project root. Refuses to run if
the corresponding `.tex` has been modified since the `.bak` was made AND
`--force` is not passed.

## ✅ Checkpoint

- New PDF page count printed.
- `applied.log` populated only if `--apply-edits` was used.
- `.bak` files exist for every file the agent touched in Step 6.
