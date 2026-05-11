# Workflow: `analyze` (full 4-layer pass)

The default workflow — produces a complete ranked-edit report.

## 🚧 GATE

- User has pointed at a LaTeX project (a `.tex` main file or a directory containing one).
- The project compiles cleanly with `latexmk -pdf`. If the build is broken, the agent must STOP and ask the user to fix the build first; broken-build repair is out of scope.
- `pip install -r requirements.txt` has been run in the active environment.

## Steps

### 1. Compile-state snapshot

```bash
python3 ${SKILL_DIR}/scripts/cli/page_fitter.py analyze <main.tex> --out .page-fitter/
```

Internal sequence:

1. `compile_once.py` — runs `latexmk -synctex=1 -interaction=nonstopmode -pdf <main.tex>` IF `.page-fitter/state.json` is missing or any source `.tex` is newer than it.
2. `parse_pdf.py` — extracts per-page text-block bboxes, clusters them into columns by x-coordinate, and records baseline-skips.
3. `parse_synctex.py` — wraps `synctex view` (forward) and `synctex edit` (reverse) into a Python dict keyed by `(file, line)`.
4. `parse_log.py` — pulls `Overfull \hbox`, `Underfull \vbox`, and `LaTeX Warning: Float ... not on page` lines.
5. `snapshot.py` — bundles into `state.json` (schema in `references/output-schema.md`).

### 2. Candidate enumeration

```bash
python3 ${SKILL_DIR}/scripts/candidates/generate_candidates.py .page-fitter/state.json \
    --out .page-fitter/candidates.json
```

`parse_latex.py` walks the `pylatexenc` AST; `generate_candidates.py` emits one candidate per editable unit (sentence, caption tail, transition, mergeable cite, redundant `\paragraph` lead-in, …). `classify.py` tags each candidate with `type` and structural flags.

### 3. Layout analysis

```bash
python3 ${SKILL_DIR}/scripts/layout/paragraph_lines.py \
    .page-fitter/state.json .page-fitter/candidates.json \
    --out .page-fitter/layout.json

python3 ${SKILL_DIR}/scripts/layout/float_risk.py \
    .page-fitter/state.json .page-fitter/candidates.json \
    --out .page-fitter/floats.json
```

Computes per candidate:

- `paragraph_line_count`
- `last_line_fill_ratio` — **the most predictive single feature**
- `est_line_delta` (with confidence band) via `line_breaking_approx.py`
- `float_risk` — risk penalty, NOT a leverage bonus

### 4. Semantic-cost scoring (LLM-in-the-loop)

The agent reads `candidates.json` and assigns `semantic_cost ∈ {1..5}` per the rubric in `references/candidate-types.md`. Output: `.page-fitter/semantic.json`.

Triage mode (`--triage`) skips this and uses type-class medians.

### 5. Final ranking

```bash
python3 ${SKILL_DIR}/scripts/scoring/rank.py \
    .page-fitter/state.json .page-fitter/candidates.json \
    .page-fitter/layout.json .page-fitter/floats.json \
    .page-fitter/semantic.json \
    --out .page-fitter/report.md --json .page-fitter/ranked.json
```

`report.md` is the human-facing artifact. Three buckets:

1. **High-leverage edits** (top 10).
2. **Marginal edits** (next 10).
3. **Not worth editing** — locations where layout analysis predicts <0.3 line saved or where float risk dominates.

### 6. Surface to user

The agent presents `report.md` (rendering it inline if the host UI supports markdown). Then transitions to `verify.md` only after explicit user selection — see ⛔ Step 5 in `SKILL.md`.

## ✅ Checkpoint

- `.page-fitter/state.json`, `candidates.json`, `layout.json`, `floats.json`, `ranked.json`, `report.md` all exist.
- `ranked.json` has at least one candidate scored above the `not-worth` threshold (otherwise the paper is already line-tight; report this honestly to the user).
