---
name: page-fitter
description: >
  Layout-aware LaTeX page-trimming advisor. When a paper is over the page limit
  (NeurIPS 9p, ACL 8p, ICML, etc.), this skill ranks edits by their PDF-height
  impact and page-boundary leverage rather than by source length. Use when the
  user asks to "缩减页数 / fit page limit / shorten LaTeX paper / trim paper /
  删行 / 控页 / 压页 / page-fitter" or otherwise needs to reduce the rendered
  page count of a LaTeX document by surgical edits.
---

# Page Fitter Skill

> A layout-aware trimming advisor for LaTeX papers under hard page limits.
> Reverse-maps PDF state to source via SyncTeX, ranks edits by *rendered-line
> impact* and *page-boundary leverage*, and explicitly identifies "not worth
> editing" regions.

**Core Pipeline**: `Compile-state Snapshot → Candidate Enumeration → Layout Analysis → Boundary-Leverage Scoring → ⛔ User Selection → Agent Edits Source → Verification Compile`

> **Editing model.** The Python scripts produce *analysis*, not edits. After Step 5, the **agent** (LLM) reads the report, makes prose edits to the `.tex` files using its own editor tool — preserving grammar, doing semantic compression, merging adjacent fragments, etc. — and then runs `verify` to recompile and confirm the page count. The legacy mechanical span-deleter (`--apply-edits`) is opt-in and NOT recommended: it can only do raw deletions and is fragile in the presence of macros pylatexenc cannot resolve.

> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> This workflow is a strict serial pipeline. Violating any rule constitutes execution failure.
>
> 1. **SERIAL EXECUTION** — Steps 1→6 run in order; each step's output is the next step's input. Non-BLOCKING adjacent steps may proceed without waiting for the user to say "continue."
> 2. **BLOCKING = HARD STOP** — Steps marked ⛔ BLOCKING require a full stop; the AI MUST wait for an explicit user response and MUST NOT pick edits on the user's behalf.
> 3. **NO AUTO-APPLY** — The skill NEVER edits source files in Steps 1–4. Edits are made by the AGENT in Step 6, only after the user has explicitly approved them in Step 5. The mechanical `--apply-edits` flag is opt-in and not the primary path.
> 4. **NO CROSS-PHASE BUNDLING** — Do not generate the ranked report (Step 4 output) before the layout analysis (Step 3) has produced its `state.json` layer.
> 5. **GATE BEFORE ENTRY** — Each Step has prerequisites (🚧 GATE) listed at the top of the workflow file; verify them before starting.
> 6. **NO SPECULATIVE COMPILE** — Do not run `latexmk` more than once per analysis pass. The verification compile in Step 6 is the only re-compile.
> 7. **SYNCTEX IS THE SPINE** — Every candidate edit MUST carry both a source location (`file:line:col`) and a PDF location (`page, column, y`). Edits without SyncTeX backing are FORBIDDEN to score.
> 8. **HEURISTICS ARE CONFIDENCE-TAGGED** — Every line-savings prediction in the report MUST carry a confidence band (`high / medium / low`). Reporting a point estimate without a band is FORBIDDEN.

> [!IMPORTANT]
> ## 🌐 Language & Communication Rule
>
> - **Response language**: match the user's input. Chinese-language paper → Chinese report; English-language paper → English report.
> - **`state.json` schema**: field names are always English (see `references/output-schema.md`). Field *values* may be in the user's language.

> [!IMPORTANT]
> ## 🔌 Compatibility With Generic Coding Skills
>
> - `page-fitter` is a single-purpose advisor, not a paper-editor. It SUGGESTS deletions/compressions; the user (or a separate writing skill) executes prose rewrites.
> - Do NOT scaffold tests/, .worktrees/, branch workflows, or generic engineering structure on the user's LaTeX project.
> - On conflict with a generic coding skill, follow this skill unless the user explicitly says otherwise.

## Main Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/cli/page_fitter.py` | Single CLI entry point — `analyze | verify | revert` subcommands |
| `${SKILL_DIR}/scripts/compile_state/compile_once.py` | `latexmk -synctex=1 -interaction=nonstopmode` (conditional) |
| `${SKILL_DIR}/scripts/compile_state/parse_pdf.py` | PyMuPDF: per-page text-block bboxes, column clustering |
| `${SKILL_DIR}/scripts/compile_state/parse_synctex.py` | Wraps `synctex view` / `synctex edit` for forward+reverse mapping |
| `${SKILL_DIR}/scripts/compile_state/parse_log.py` | Extracts overfull/underfull boxes and float-defer warnings |
| `${SKILL_DIR}/scripts/compile_state/snapshot.py` | Bundles layers 1–3 into a single `state.json` |
| `${SKILL_DIR}/scripts/candidates/parse_latex.py` | `pylatexenc` walker → AST of editable nodes |
| `${SKILL_DIR}/scripts/candidates/generate_candidates.py` | Produces sentence/caption/transition/etc. candidates |
| `${SKILL_DIR}/scripts/candidates/classify.py` | Tags each candidate (type, float-adjacent, semantic-load) |
| `${SKILL_DIR}/scripts/layout/paragraph_lines.py` | Per-paragraph line count + last-line fill ratio |
| `${SKILL_DIR}/scripts/layout/line_breaking_approx.py` | Knuth-Plass-lite line predictor (after-deletion line delta) |
| `${SKILL_DIR}/scripts/layout/float_risk.py` | Marks candidates near pending floats |
| `${SKILL_DIR}/scripts/scoring/layout_gain.py` | Estimated rendered-line savings |
| `${SKILL_DIR}/scripts/scoring/boundary_leverage.py` | Distance-to-page-break leverage score |
| `${SKILL_DIR}/scripts/scoring/rank.py` | Final ordering + report writer |
| `${SKILL_DIR}/scripts/verify/apply_edits.py` | Idempotent edit applier (writes `.bak`) |
| `${SKILL_DIR}/scripts/verify/recompile.py` | Verification compile + page-count diff |
| `${SKILL_DIR}/scripts/verify/revert.py` | Restore from `.bak` |

## Reference Index

| Reference | Path | Purpose |
|-----------|------|---------|
| Architecture | `references/architecture.md` | 4-layer design rationale |
| SyncTeX mapping | `references/synctex-mapping.md` | Forward/reverse SyncTeX usage |
| Line-breaking | `references/line-breaking.md` | Paragraph line approximation |
| Boundary scoring | `references/boundary-scoring.md` | **Load-bearing** — the scoring formula |
| Candidate types | `references/candidate-types.md` | **Load-bearing** — editable-unit taxonomy + semantic-cost rubric |
| Float placement | `references/float-placement.md` | Float reflow risk model |
| Output schema | `references/output-schema.md` | `state.json` and `report.md` formats |

## Standalone Workflows

| Workflow | Path | Purpose |
|----------|------|---------|
| `analyze` | `workflows/analyze.md` | Full 4-layer analysis pipeline (default) |
| `triage` | `workflows/triage.md` | Quick "top-N edits only" mode |
| `verify` | `workflows/verify.md` | Apply user-selected edits + verification compile |

---

## Workflow

### Step 1: Compile-state Snapshot

🚧 **GATE**: User has provided a path to a LaTeX project (a `.tex` main file or a directory containing one). The project must compile cleanly with `latexmk` — broken-build repair is OUT OF SCOPE.

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py analyze <main.tex> [--out <state-dir>]
```

The CLI dispatches Step 1 internally:

1. If `<state-dir>/state.json` exists AND is newer than every source file → reuse, skip recompile.
2. Otherwise call `compile_once.py` (`latexmk -synctex=1 -interaction=nonstopmode -pdf <main.tex>`).
3. Parse outputs:
   - `parse_pdf.py` → per-page text-block bboxes, column clustering, baseline skips.
   - `parse_synctex.py` → bi-directional source⇄PDF map.
   - `parse_log.py` → overfull/underfull boxes, deferred floats.
4. `snapshot.py` writes `state.json` (schema in `references/output-schema.md`).

**✅ Checkpoint** — `state.json` exists and is internally consistent (every text block in `parse_pdf` maps to at least one source line via SyncTeX).

---

### Step 2: Candidate Enumeration

🚧 **GATE**: Step 1 complete; `state.json` available.

```bash
python3 ${SKILL_DIR}/scripts/candidates/generate_candidates.py <state.json> --out candidates.json
```

This pass walks the LaTeX AST (`parse_latex.py`) and emits one candidate per editable unit:

- **Sentences** inside paragraphs.
- **Caption tail clauses** (after the first independent clause).
- **Transition / discourse markers** ("Furthermore,", "It is worth noting that," etc.).
- **Citation clusters** that can be merged (`\cite{a}\cite{b}` → `\cite{a,b}`).
- **Equation labels / cross-refs** that can be inlined.
- **\paragraph headings + their body's leading throat-clearing**.

Each candidate is tagged by `classify.py` with `type`, `float_adjacent`, `in_abstract`, `is_argument_load_bearing`, and the SyncTeX-derived `pdf_loc`.

**✅ Checkpoint** — `candidates.json` produced; no candidate lacks both `src_loc` and `pdf_loc`.

---

### Step 3: Layout Analysis

🚧 **GATE**: Step 2 complete.

```bash
python3 ${SKILL_DIR}/scripts/layout/paragraph_lines.py <state.json> <candidates.json> --out layout.json
python3 ${SKILL_DIR}/scripts/layout/float_risk.py <state.json> <candidates.json> --out floats.json
```

Per candidate, compute:

- `paragraph_line_count` — how many rendered lines its host paragraph occupies.
- `last_line_fill_ratio` — fraction of the column width filled by the host paragraph's last line. **The single most predictive feature** (see `references/line-breaking.md`).
- `est_line_delta` — Knuth-Plass-lite prediction of `(lines_after − lines_before)`, with a confidence band.
- `float_risk` — penalty if a deferred float is downstream of this candidate.

**✅ Checkpoint** — `layout.json` and `floats.json` produced.

---

### Step 4: Boundary-Leverage Scoring

🚧 **GATE**: Step 3 complete.

```bash
python3 ${SKILL_DIR}/scripts/scoring/rank.py <state.json> <candidates.json> <layout.json> <floats.json> --out report.md --json ranked.json
```

Apply the formula (full spec in `references/boundary-scoring.md`):

```
score(c) = P_reduce_line(c) × est_height_saved(c)
        × boundary_leverage(c) / max(semantic_cost(c), ε)
```

`semantic_cost(c)` is filled in by the agent (LLM judgment per the rubric in `references/candidate-types.md`) before this script is called, OR — if the user is in triage mode — defaults to the type-class median.

The output `report.md` is a three-bucket ranked list:

1. **High-leverage edits** (top 10).
2. **Marginal edits** (next 10).
3. **Not worth editing** — locations a naive LLM would suggest but layout analysis rejects (e.g., long paragraphs with 5%-full last lines).

**✅ Checkpoint** — `report.md` rendered; agent surfaces it to the user.

---

### Step 5: ⛔ BLOCKING — User Selection

🚧 **GATE**: Step 4 complete; `report.md` shown to user.

> ⛔ **BLOCKING** — STOP HERE. Wait for explicit user response.

The agent presents the report and asks the user to:

- Approve a subset of high-leverage / marginal edits (by ID), OR
- Request re-ranking with a different objective (e.g., "minimize edits in §4 — that's the contribution section"), OR
- Abort.

The agent MUST NOT silently apply any edit at this gate.

---

### Step 6: Agent Edits Source Files

🚧 **GATE**: Step 5 complete; user has approved a subset of candidate IDs.

The AGENT (not a script) now opens the corresponding `.tex` files and applies the approved edits using its own editor tool. For each approved candidate, the agent should:

- Read the host paragraph for context (do not edit blindly from the report).
- Choose the edit form that best preserves grammar:
  - `discourse_transition` → delete the phrase AND fix the following capitalization if needed.
  - `caption_tail` → keep the first sentence; delete the rest of the caption.
  - `section_opening` → consider compressing rather than deleting outright.
  - `sentence_descriptive` → may delete; double-check the surrounding logical flow.
  - `sentence_claim` / `sentence_proof_step` → DO NOT delete; ask the user to confirm in plain language first.
- Preserve the `.bak` discipline: before editing any file for the first time in a session, copy it to `<file>.bak` so `revert` works.

When the agent is done with all approved edits, proceed to Step 7.

> ⚠️ **Anti-pattern**: do NOT use `--apply-edits` to skip this step. The mechanical applier deletes raw spans and cannot fix capitalization, grammar, or accidental macro corruption (e.g. when pylatexenc fails to consume `\lipsum`'s optional args).

### Step 7: Verification Compile

🚧 **GATE**: Step 6 complete; the agent has finished applying edits to source.

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py verify <main.tex>
```

This runs `recompile.py` only (no source modification) and reports `old_page_count → new_page_count`. If the page count went up, see `references/float-placement.md` — a float likely reflowed.

If the user is unhappy, `page_fitter.py revert <main.tex>` restores from any `.bak` files the agent created in Step 6.

**✅ Checkpoint** — Verification report shown. Skill terminates.

---

## Quick Reference

- **One-shot full run**: `python3 ${SKILL_DIR}/scripts/cli/page_fitter.py analyze <main.tex>`
- **Triage mode** (skip semantic-cost LLM pass; use type-class medians): add `--triage`.
- **Verify edits**: `python3 ${SKILL_DIR}/scripts/cli/page_fitter.py verify <main.tex> --edits <ids>`
- **Revert**: `python3 ${SKILL_DIR}/scripts/cli/page_fitter.py revert <main.tex>`

### Compiler portability

The skill auto-detects, in order: `latexmk` → `pdflatex` → `xelatex` → `lualatex`. If you have a non-standard toolchain, override with either:

- `--compiler "<cmd>"` flag — e.g. `--compiler "pdflatex"`, `--compiler "xelatex --shell-escape"`, or a full path like `--compiler "/opt/texlive/bin/lualatex"`.
- `PAGE_FITTER_LATEX_CMD` environment variable (same string as `--compiler`).

If `latexmk` is chosen, it runs once with `-pdf -synctex=1 -interaction=nonstopmode -halt-on-error`. Single-engine fallbacks (pdflatex/xelatex/lualatex) run twice so cross-references settle.

For the full design rationale, read `references/architecture.md`.
