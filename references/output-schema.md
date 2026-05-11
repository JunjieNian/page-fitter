# Output schema

Every Python script in this skill speaks a documented JSON contract on
stdin/stdout (or via `--out` files). This file is the authoritative spec.

## `state.json` (Layer 1 output)

```jsonc
{
  "schema_version": "1.0",
  "main_tex": "main.tex",                 // relative to project root
  "project_root": "/abs/path/to/project",
  "pdf": {
    "path": "main.pdf",
    "page_count": 10,
    "pages": [
      {
        "page": 1,
        "width": 612.0, "height": 792.0,  // PDF points
        "columns": [
          { "x_min": 72.0, "x_max": 295.0, "text_width": 223.0 },
          { "x_min": 317.0, "x_max": 540.0, "text_width": 223.0 }
        ],
        "baseline_skip": 12.6,
        "blocks": [
          {
            "block_id": "p1.b3",
            "bbox": [72.0, 612.0, 295.0, 720.0],
            "column": 0,
            "kind": "paragraph",          // paragraph | heading | caption | display_math | float
            "line_bboxes": [ [72.0, 612.0, 295.0, 624.0], ... ],
            "synctex": { "file": "main.tex", "first_line": 142, "last_line": 156 }
          }
        ]
      }
    ]
  },
  "synctex": {
    "available": true,
    "forward_index_size": 5821,
    "warnings": []
  },
  "log": {
    "overfull_hbox": [
      { "file": "main.tex", "line": 203, "overflow_pt": 4.7 }
    ],
    "underfull_vbox": [],
    "deferred_floats": [
      { "source_file": "main.tex", "source_line": 88, "placement_page": 4 }
    ]
  }
}
```

## `candidates.json` (Layer 2 output)

```jsonc
{
  "schema_version": "1.0",
  "candidates": [
    {
      "id": "c001",
      "type": "discourse_transition",     // see candidate-types.md
      "src_loc": {
        "file": "main.tex",
        "line": 142,
        "col_start": 4,
        "col_end": 27,
        "text": "Furthermore,"
      },
      "pdf_loc": {
        "page": 3,
        "column": 1,
        "x": 320.0, "y": 488.5,
        "block_id": "p3.b7"
      },
      "tags": {
        "float_adjacent": false,
        "in_abstract": false,
        "in_proof": false,
        "is_argument_load_bearing": false,
        "algorithm_local": false
      },
      "edit_action": "delete_span",       // delete_span | merge_cites | compress_to_first_sentence
      "edit_payload": null
    }
  ]
}
```

## `layout.json` (Layer 3 output, paragraph_lines)

```jsonc
{
  "schema_version": "1.0",
  "by_candidate": {
    "c001": {
      "host_paragraph": "p3.b7",
      "paragraph_line_count": 5,
      "last_line_fill_ratio": 0.92,
      "est_line_delta": -1.0,
      "confidence": "high",               // high | medium | low
      "P_reduce_line": 0.78
    }
  }
}
```

## `floats.json` (Layer 3 output, float_risk)

```jsonc
{
  "schema_version": "1.0",
  "by_candidate": {
    "c001": {
      "float_risk": 0.0,
      "near_floats": [],
      "downstream_is_float_or_heading": false
    },
    "c014": {
      "float_risk": 0.6,
      "near_floats": ["fig:arch"],
      "downstream_is_float_or_heading": true
    }
  }
}
```

## `semantic.json` (Layer 4 input, agent-produced)

```jsonc
{
  "schema_version": "1.0",
  "by_candidate": {
    "c001": { "semantic_cost": 1, "rationale": "Pure transition." },
    "c014": { "semantic_cost": 4, "rationale": "Names the contribution." }
  }
}
```

## `ranked.json` (Layer 4 output)

```jsonc
{
  "schema_version": "1.0",
  "scored": [
    {
      "id": "c001",
      "score": 1.42,
      "bucket": "high_leverage",          // high_leverage | marginal | not_worth
      "components": {
        "P_reduce_line": 0.78,
        "est_height_saved_pt": 12.6,
        "boundary_leverage": 2.4,
        "semantic_cost": 1,
        "float_risk": 0.0
      },
      "confidence": "high",
      "rationale": "Last page, 92% full last line, transition phrase."
    }
  ],
  "summary": {
    "total_candidates": 73,
    "high_leverage": 8,
    "marginal": 11,
    "not_worth": 54,
    "current_page_count": 10,
    "page_limit": 9                       // user-supplied or inferred from \documentclass
  }
}
```

## `report.md` (Layer 4 human-facing output)

```markdown
# page-fitter report

Current: 10 pages — limit: 9 — need to lose: 1 page (≈ 32 lines).

## High-leverage edits (top 10)

| ID | File:Line | Type | Gain | Leverage | Cost | Confidence | Rationale |
| -- | --------- | ---- | ---- | -------- | ---- | ---------- | --------- |
| c001 | main.tex:142 | transition | -1.0 line | 2.4 | 1 | high | Last page, 92% full last line. |
| ... |

## Marginal edits

...

## Not worth editing

| ID | File:Line | Why |
| -- | --------- | --- |
| c042 | sec/method.tex:88 | Adjacent to deferred figure (float_risk=0.7). |
| c057 | main.tex:301 | Last-line fill 6% — small deletion will not collapse a line. |
```

## `applied.log` (Step 6 record)

Plain text, append-only:

```
2026-05-09T10:14:22Z  c001  main.tex:142  delete_span  hash=ab12cd
2026-05-09T10:14:22Z  c014  sec/method.tex:88  compress_to_first_sentence  hash=ef34
```

## Conventions

- All `bbox` arrays are `[x_min, y_min, x_max, y_max]` in PDF points, with the
  PDF coordinate origin at the **top-left** (we normalize PyMuPDF's bottom-left
  internally; readers should not care).
- All `line` numbers are 1-indexed.
- All file paths in JSON are relative to `project_root`.
- All scripts emit `schema_version: "1.0"`. Bumps require updating this file.
