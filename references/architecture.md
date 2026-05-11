# Architecture: the four layers

`page-fitter` is a layered advisor. Each layer's output is the input to the
next; every layer is a separately-callable Python module so the agent can
debug and re-run pieces.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 4 — Boundary-leverage scoring                                    │
│   scoring/rank.py + scoring/boundary_leverage.py + scoring/layout_gain │
│   IN : state.json + candidates.json + layout.json + floats.json        │
│        + semantic.json (or triage type-class medians)                  │
│   OUT: report.md, ranked.json                                          │
├────���───────────────────────────────────────────────────────────────────┤
│ Layer 3 — Layout analysis                                              │
│   layout/paragraph_lines.py + line_breaking_approx.py + float_risk.py  │
│   IN : state.json + candidates.json                                    │
│   OUT: layout.json (last-line fill, est_line_delta, paragraph metrics) │
│        floats.json (float-adjacency penalty)                           │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 2 — Candidate enumeration                                        │
│   candidates/parse_latex.py → generate_candidates.py → classify.py     │
│   IN : state.json + main.tex + included .tex files                     │
│   OUT: candidates.json (list of editable units, each with src+pdf loc) │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 1 — Compile-state snapshot                                       │
│   compile_state/{compile_once, parse_pdf, parse_synctex, parse_log,    │
│                  snapshot}.py                                          │
│   IN : main.tex (latexmk), main.pdf, main.synctex.gz, main.log         │
│   OUT: state.json                                                      │
└────────────────────────────────────────────────────────────────────────┘
```

## Why four layers and not one big script?

1. **Re-runnability.** Layer 1 is expensive (involves `latexmk`); layers 2–4 are cheap. Edits to the scoring formula should not force a recompile.
2. **Confidence isolation.** Layer 3's heuristics carry confidence bands; layer 4 must propagate them. Mashing layers together loses this.
3. **LLM-in-the-loop point.** Semantic cost (used by layer 4) is the *only* place where the agent's judgment enters; isolating it prevents the LLM from contaminating layout estimates with prose-quality opinions.
4. **Debuggability.** A user complaint of the form "this candidate was ranked too high" can always be traced to one specific layer — the structural decomposition is a UX feature, not just an engineering one.

## Why SyncTeX is a separate sub-module of layer 1

`parse_synctex.py` is the spine of the whole system. Every layer downstream
of it queries `(file, line) → (page, x, y)` (forward) or
`(page, x, y) → (file, line)` (reverse). If SyncTeX data is missing or
stale, no later layer can produce trustworthy output. `snapshot.py`
therefore validates that every PDF text block has at least one source-line
preimage; otherwise it aborts with a clear error.

## Why `state.json` is a single bundled file (not a directory)

A single JSON file is trivially diffable, cacheable by mtime, and easy to
attach to a bug report. The size (a few hundred KB for a 9-page paper) is
small enough that the convenience wins.

## Why heuristics over a trained model (v1)

Out of scope per the seed conversation. A trained layout-gain predictor
needs hundreds of (edit, page-delta) pairs collected across templates;
v1 ships heuristics with explicit confidence bands. The architecture
admits a layer-3 model swap later — `est_line_delta` is computed by a
single function in `line_breaking_approx.py`.

## What is explicitly NOT in this architecture

- A persistent server or daemon. Each invocation is one CLI run.
- A long-lived database. `.page-fitter/` is per-project state, regenerable.
- An automatic edit-applier. Step 5 in `SKILL.md` is a hard-blocking gate,
  enforced both at the workflow level and inside `apply_edits.py`
  (which refuses to run unless given an explicit `--edits` list).
