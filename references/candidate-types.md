# Candidate types and semantic-cost rubric (load-bearing)

> This file is the spec for `scripts/candidates/generate_candidates.py` and
> `scripts/candidates/classify.py`, and the rubric the agent applies when
> filling in `semantic_cost` per candidate.

## Editable-unit taxonomy

Each candidate belongs to exactly one type. The taxonomy is tight on
purpose — broader categories are too noisy for the type-class median in
triage mode.

### 1. `discourse_transition`

Discourse / transition markers that add no semantic content:

- `Furthermore,` `Moreover,` `In addition,` `It is worth noting that,`
- `As mentioned above,` `As we have seen,`
- `In other words,` `That is to say,`

Pattern: matches a small regex set in `parse_latex.py`. Always offered as
"delete entirely."

### 2. `caption_tail`

A figure/table caption's clauses *after* the first independent clause.

```
\caption{The architecture of our model. As shown, the encoder feeds...}
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                       candidate (the tail)
```

Captions tolerate aggressive trimming because the figure carries the
content. Always offered as "compress to first sentence."

### 3. `cite_cluster`

Adjacent `\cite{a}\cite{b}\cite{c}` that can be merged into `\cite{a,b,c}`.
Saves zero semantic content; saves a few characters. Low layout impact
unless the cluster is on a near-overflow line.

### 4. `sentence_descriptive`

A sentence that describes setup or context but does not state a claim,
result, or proof step.

Heuristic detector: no first-person plural ("we"), no numeric result, no
`\ref{*:thm}` or `\ref{*:lem}` references, no comparative ("better than",
"outperforms").

### 5. `sentence_claim`

A sentence that states a result or claim. Higher semantic cost — losing
one of these usually costs the paper an explicit selling point.

Heuristic detector: contains a numeric result, OR a comparative, OR a
"we show / we prove / we demonstrate" clause.

### 6. `sentence_proof_step`

A sentence inside a proof environment (`\begin{proof}` … `\end{proof}`,
or a `\paragraph{Proof.}` block). High semantic cost — proofs are
hard-to-trim by definition.

### 7. `section_opening`

The first sentence after `\section` / `\subsection`. Often
roadmap/throat-clearing ("In this section, we describe …"), often
deletable, but high *risk* of confusing the reader.

### 8. `display_equation`

A `\begin{equation}` or `\[ … \]` that occupies its own line(s). High
semantic cost; only suggest deletion if it's a duplicate or trivially
inline-able.

## Semantic-cost rubric (1–5)

Used by the agent in full `analyze` mode. Per-candidate, not per-type.

| Cost | Meaning | Examples |
|------|---------|----------|
| 1 | "Pure filler — paper improves with deletion." | Empty transitions, redundant cite clusters, throat-clearing section openings. |
| 2 | "Mildly informative — paper unchanged or slightly worse." | Caption tails, descriptive sentences in setup paragraphs, non-load-bearing examples. |
| 3 | "Has content but is replaceable or compressible." | Section openings carrying a small roadmap, descriptive sentences in main-body paragraphs, parenthetical asides with one numeric value. |
| 4 | "Load-bearing — paper meaningfully degrades." | Claim sentences, result statements, key motivating sentences in the intro. |
| 5 | "Essential — do not delete." | Proof steps, theorem statements, definitions, the central equation of a section, the only place a key term is defined. |

The agent assigns cost by reading the candidate plus a small window of
surrounding context. Cost 5 candidates are still surfaced in the
report's "not worth editing" bucket so the user can see them and rule
them out explicitly — they are NOT silently filtered.

## Triage-mode type-class medians

Used by `--triage` (no LLM pass).

| Type | Median cost |
|------|-------------|
| `discourse_transition` | 1 |
| `caption_tail` | 2 |
| `cite_cluster` | 1 |
| `sentence_descriptive` | 2 |
| `sentence_claim` | 4 |
| `sentence_proof_step` | 5 |
| `section_opening` | 3 |
| `display_equation` | 5 |

(Identical to the table in `boundary-scoring.md`; kept here as the
authoritative source for the triage code path. If they diverge, this
file wins.)

## Float-adjacency tag

Independently of type, every candidate carries `float_adjacent: bool`
set by `classify.py` if the candidate is within 3 source lines of a
`\begin{figure}`, `\begin{table}`, `\begin{algorithm}`, or
`\begin{equation}` environment. The boundary-leverage scorer treats
this as *risk*, not bonus (see `references/float-placement.md`).

## What is NOT a candidate

Hard exclusions in `parse_latex.py`:

- Anything inside `\begin{abstract}` — abstracts are usually word-counted, not page-counted, and trimming them is the user's manual call.
- Anything inside `\begin{proof}` is included only as type 6 — proofs are surfaced but with floor cost 5.
- `\title`, `\author`, `\date`, `\thanks`, `\maketitle`.
- Anything inside a `\begin{thebibliography}` — bibliography compression is a separate concern (use `bibcompress` or similar).
- Anything inside an `\IfFinal{...}{...}` or similar conditional — too ambiguous to score.
