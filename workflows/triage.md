# Workflow: `triage` (fast top-N)

A faster variant of `analyze` for iteration: skips the per-candidate
LLM semantic-cost pass, using type-class median costs from
`references/candidate-types.md`. Useful when the user wants a
quick "what's near a page break right now?" answer between writing
sessions.

## 🚧 GATE

- Same as `analyze.md`.
- The user has explicitly opted into triage mode (typically by saying "quick pass" / "triage" / "fast" / `--triage`).

## Steps

### 1. Compile-state snapshot

Same as `analyze.md` Step 1. If `.page-fitter/state.json` is fresh, reuse.

### 2. Candidate enumeration (filtered)

```bash
python3 ${SKILL_DIR}/scripts/candidates/generate_candidates.py .page-fitter/state.json \
    --out .page-fitter/candidates.json --filter near-boundary
```

The `--filter near-boundary` flag drops candidates whose `pdf_loc.page` is not the last page or the last column of the second-to-last page. This is the dominant cost saver.

### 3. Layout analysis (last-line fill only)

```bash
python3 ${SKILL_DIR}/scripts/layout/paragraph_lines.py \
    .page-fitter/state.json .page-fitter/candidates.json \
    --out .page-fitter/layout.json --fast
```

`--fast` skips the Knuth-Plass approximation and uses only `last_line_fill_ratio` as the line-delta proxy:

```
P_reduce_line ≈ clamp(last_line_fill_ratio + word_width(c) − 1.0, 0, 1)
```

`float_risk.py` is still run; float reflow is too risky to ignore even in triage.

### 4. Ranking with type-class costs

```bash
python3 ${SKILL_DIR}/scripts/scoring/rank.py \
    .page-fitter/state.json .page-fitter/candidates.json \
    .page-fitter/layout.json .page-fitter/floats.json \
    --triage \
    --out .page-fitter/report.md --json .page-fitter/ranked.json
```

`--triage` makes `rank.py` consult the type→median-cost table (embedded in `candidate-types.md`) instead of expecting `semantic.json`.

### 5. Surface to user

Same as `analyze.md` Step 6 — but the report MUST carry a banner:

> **Triage mode** — semantic cost is type-class median, not per-candidate. Re-run without `--triage` for a higher-confidence ranking before applying multi-edit batches.

The ⛔ BLOCKING gate still applies.

## When NOT to use triage

- Final pre-submission pass — use full `analyze`.
- Papers where one section's importance dominates (e.g., the user already said "don't touch §4") — semantic cost matters too much.
- Camera-ready trim — the asymmetry between "lose a sentence in intro" vs. "lose a sentence in proof" cannot be captured by type-class medians.
