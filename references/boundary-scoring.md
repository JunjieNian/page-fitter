# Boundary-scoring formula (load-bearing)

> This file is the **specification** for `scripts/scoring/rank.py`.
> Any change to the formula MUST be reflected here first; deviations are bugs.

## The formula

For each candidate `c`:

```
score(c) = P_reduce_line(c)
        × est_height_saved(c)
        × boundary_leverage(c)
        / max(semantic_cost(c), ε)
```

with `ε = 0.5` (so a candidate with `semantic_cost = 1` does not blow up the score).

## Term-by-term spec

### `P_reduce_line(c)` — probability ≥ 1 rendered line removed

```
P_reduce_line(c) = clamp(
    last_line_fill_ratio(host_paragraph(c))
  + (W_c / col_w)
  − 1.0,
    0.0,
    1.0
)
```

Where `W_c` is the glyph-width of the deletion candidate, `col_w` is the
host column text width. This is a back-of-envelope approximation;
`line_breaking_approx.py` may override it with a Knuth-Plass-lite value.

### `est_height_saved(c)` — in baseline-skips

```
est_height_saved(c) = est_line_delta(c) × baseline_skip(host_page)
```

`baseline_skip(host_page)` comes from `parse_pdf.py` (it is the median
y-spacing between consecutive lines on that page).

`est_line_delta(c)` is signed and may be 0; if 0, `score(c) = 0` and the
candidate goes into the "not worth editing" bucket.

### `boundary_leverage(c)` — distance-to-page-break weighting

```
boundary_leverage(c) = 1
                    + α · near_last_page(c)
                    + β · near_column_break(c)
                    + γ · downstream_paragraph_pullable(c)
                    − δ · downstream_is_float_or_heading(c)
```

Default coefficients (tunable):

| Symbol | Default | Meaning |
|--------|---------|---------|
| α | 2.0 | Boost for being on the last page or last column |
| β | 0.6 | Boost for being near a column break (two-column docs) |
| γ | 0.8 | Boost when collapsing a line lets the next paragraph pull up |
| δ | 1.5 | Penalty when the next structural element is a float or section heading (won't pull up) |

Indicator functions:

- `near_last_page(c) = 1` if `pdf_loc.page` is the last page, else 0.
- `near_column_break(c) = 1` if the host paragraph's last line is in the
  bottom 15% of its column AND the document is two-column.
- `downstream_paragraph_pullable(c) = 1` if the next text block in PDF
  order is another paragraph (not a float, heading, list, or display
  equation), 0 otherwise.
- `downstream_is_float_or_heading(c) = 1` if the next block is a float
  caption, heading, or display equation.

`α + γ − δ` can go negative when a candidate is on the last page but
followed by a heading: the heading won't pull up, so removing a line
just leaves whitespace. The penalty is intentional — the seed
conversation called this out as the "not worth editing" signal.

### `semantic_cost(c)` — 1 (cheap) … 5 (load-bearing)

Per-type rubric in `references/candidate-types.md`. In full
`analyze` mode, the agent assigns this per candidate. In `--triage`
mode, the type-class median is used:

| Type | Median cost |
|------|-------------|
| Discourse / transition phrase | 1 |
| Caption tail clause | 2 |
| Mergeable cite cluster | 1 |
| Sentence — descriptive | 2 |
| Sentence — claim or result | 4 |
| Sentence — proof step | 5 |
| Section opening sentence | 3 |
| Display equation | 5 |

## Three-bucket cutoffs

After scoring all candidates:

- **High-leverage**: top 10 by `score`, AND `score > 0.6`, AND confidence is `high` or `medium`.
- **Marginal**: next 10, OR any candidate with `0.2 < score ≤ 0.6`.
- **Not worth editing**: `score ≤ 0.2`, OR confidence is `low` AND score is in the bottom half, OR `est_line_delta(c) == 0`.

The thresholds are rules of thumb. They will need tuning across paper
templates (NeurIPS vs. ACL vs. springer LNCS), and the v1 plan ships
them as constants in `rank.py` with comments pointing back to this file.

## What the formula deliberately does NOT do

- It does not model multi-edit interactions. Each candidate is scored
  independently. A user applying 5 edits in the same paragraph may see
  diminishing returns; the verification pass in Step 6 will reveal this.
- It does not estimate page-count delta directly — only line-count delta.
  Translation to page-count is left to `recompile.py`.
- It does not consider citation-density / readability. That is the
  user's call when picking edits.
