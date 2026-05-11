# Float placement: a risk model

LaTeX floats (figures, tables, algorithms) are placed by the engine
according to placement specifiers (`htbp`) and a non-trivial set of
parameters (`\topfraction`, `\textfraction`, `\floatpagefraction`, …).
Trimming source near a float can move the float in **either direction**,
and the page-count effect of such a move is non-monotonic.

This is why `float_risk` is a **penalty**, not a bonus.

## Inputs to the risk model

`float_risk.py` consumes:

1. From `parse_log.py`:
   - `LaTeX Warning: Float too large for page` — this float is at risk of being deferred to a float-only page on any reflow.
   - `LaTeX Warning: 'h' float specifier changed to 'ht'` — the engine already overrode placement; the float is sensitive.
   - `LaTeX Warning: Float ... not on page` (`Float specifier changed`) — the float was deferred at all.

2. From `parse_pdf.py`:
   - The float's actual rendered page (`placement_page`).
   - The page where its source environment opens (`source_page`).
   - `placement_page − source_page` is the **deferral distance**; > 0 means the float was pushed forward.

3. From `parse_latex.py`:
   - The set of floats *opened in the source* but with `placement_page > N` (where N is the current PDF page count) — these are "trailing floats" that LaTeX has not yet placed.

## Computing `float_risk(c)` per candidate

```
float_risk(c) =
    ρ1  if c is within 3 source lines of a float environment
  + ρ2  if any float opened upstream of c is currently deferred
  + ρ3  if c is on the same page as a float that already moved during the last compile
```

Defaults: `ρ1 = 0.4`, `ρ2 = 0.6`, `ρ3 = 0.8`. Risk caps at 1.0.

In the boundary-leverage formula, `float_risk` enters via the
`downstream_is_float_or_heading` indicator (it forces it to 1) AND as a
multiplicative dampener on `boundary_leverage`:

```
boundary_leverage(c) ← boundary_leverage(c) × (1 − 0.5 · float_risk(c))
```

So a candidate adjacent to a known-deferred float gets up to 50% leverage
shaved off.

## Two-column documents

Two-column templates (NeurIPS, ACL `acl_natbib.bst`, ICML, IEEE) introduce
column floats via `figure*` / `table*` and per-column floats via `figure`
/ `table`. `parse_pdf.py` clusters columns; `float_risk.py` distinguishes
single-column floats (where the risk is column-local) from spanning
floats (where the risk is page-wide).

## Special case: algorithm packages

`algorithm` / `algorithm2e` floats are usually placed `H` (here, no
float-mechanism) via `\usepackage{float}`. These have **zero deferral
risk** but **high local-line-count sensitivity** (a few inserted lines
can push the entire algorithm to overflow). `classify.py` tags them
`float_adjacent` AND `algorithm_local`; `float_risk` is set to `ρ1` only.

## How to read a "float-induced page increase"

If the verification compile in Step 6 reports `new_page_count >
old_page_count`, the most common cause is:

- An edit allowed a previously-deferred float to land "earlier", which
  in turn reflowed text onto a new column/page.
- An edit made a paragraph short enough that its surrounding `htbp`
  float chose a different placement.

The recommended response is to revert (`page_fitter.py revert`), look at
which floats changed page in the new PDF (`recompile.py` records this
diff), and re-rank with that float's neighbors flagged `algorithm_local`
or with manually-bumped `float_risk`.

## Out-of-scope mitigations (v1)

- Automatically rewriting `[htbp]` to `[H]`. Too aggressive; the user must approve.
- Suggesting `\FloatBarrier` insertions. Same reason.
- Modeling `\afterpage{...}` deferral. Possible in v2.
