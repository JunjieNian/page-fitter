# Line breaking: paragraph-line approximation

We do not reimplement Knuth-Plass. We approximate just enough to answer:

> Given that paragraph P currently renders as K lines, and we delete a
> contiguous span of N words from it, will it render as K, K−1, or fewer?

## The single most predictive feature: `last_line_fill_ratio`

For paragraph P, with the host column's text width `col_w`, and last-line
bbox width `last_w` (from PyMuPDF), define:

```
last_line_fill_ratio(P) = last_w / col_w        ∈ [0, 1]
```

Empirical rule of thumb (validated on a small NeurIPS / ACL sample —
confirm before claiming numerical accuracy in a report):

| `last_line_fill_ratio` | Probability a small deletion (≤ 1 line of words) drops one rendered line |
|------------------------|-----------------------------------------------------------------|
| ≥ 0.85 | high (0.7+) |
| 0.50 – 0.85 | medium (0.3 – 0.6) |
| 0.25 – 0.50 | low (0.1 – 0.25) |
| < 0.25 | ≈ 0 — **explicitly mark as "not worth editing"** |

The intuition: the last line is "almost full" → trimming a small amount
of glue from anywhere in the paragraph can let the last word climb up.
Conversely, a 5%-full last line is a near-empty line of glue at the end;
deleting words elsewhere just makes that empty more empty.

## The Knuth-Plass-lite estimator

`line_breaking_approx.py` does this, only when not in `--fast` mode:

1. Extract per-character widths for the document's main font from
   PyMuPDF (`page.get_text("rawdict")` gives glyph widths).
2. For paragraph P, compute total glyph width `W_total` and estimate the
   "glue mass" `G = K · col_w − W_total` where K is the current line count.
3. For deletion candidate c with glyph width `W_c`, predict
   `K' = ceil((W_total − W_c) / col_w)` modulo a small overhead constant
   for justified-spacing slack.
4. Confidence band:
   - `high` if `(W_total − W_c) / col_w` is within 0.15 of an integer;
   - `medium` if within 0.30;
   - `low` otherwise.

This ignores hyphenation, `\hbox` rigidity, and ligature kerning. We
explicitly accept this imprecision and surface it via the confidence band.

## Why not a full Knuth-Plass implementation?

A faithful reimplementation must replicate TeX's badness penalties,
overfull/underfull thresholds, and the document class's specific
`\tolerance` and `\emergencystretch`. That is more code than the rest of
the skill combined, and would still mis-predict whenever a package
(`microtype`, font-spec-driven kerning, etc.) modifies the engine. Empirically,
`last_line_fill_ratio` plus the lite estimator captures ≥ 80% of the
practical signal.

## Multi-paragraph cascade

Deleting the last line of paragraph P does not just save one baseline-skip.
If P is followed by paragraph Q, and Q now has room to pull up its
opening, the cascade can save 2 or more lines. `boundary-scoring.md`
captures this as `downstream_paragraph_pullable`.

`paragraph_lines.py` does NOT model cascade by itself — it produces
per-paragraph metrics and lets `boundary_leverage.py` combine them.

## Confidence band propagation

Every `est_line_delta` value emitted by `line_breaking_approx.py` carries
a confidence enum (`high/medium/low`). `rank.py` MUST surface this in the
report; suppressing it is a violation of `SKILL.md` rule 8.
