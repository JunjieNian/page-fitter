# SyncTeX mapping (forward and reverse)

The `synctex` CLI ships with every modern TeX Live distribution. It exposes
the `.synctex.gz` index produced by `latexmk -synctex=1`.

## Forward (`source → PDF`)

```bash
synctex view -i <line>:<col>:<file> -o <main.pdf>
```

Output is a key-value block like:

```
SyncTeX result begin
Output:/abs/path/main.pdf
Page:5
x:128.5
y:412.7
h:128.5
v:412.7
W:300.0
H:11.5
before:
offset:-1
middle:
after:
SyncTeX result end
```

`page` is 1-indexed. `(h, v)` is the point's PDF coordinate (TeX's reference frame). `(W, H)` is the bounding box of the smallest enclosing TeX node — usually a glyph run.

## Reverse (`PDF → source`)

```bash
synctex edit -o <page>:<x>:<y>:<main.pdf>
```

Output:

```
SyncTeX result begin
Input:/abs/path/main.tex
Line:142
Column:-1
Offset:0
Context:0
SyncTeX result end
```

`Column:-1` is the typical case — synctex rarely tracks columns. Treat
column data as advisory only.

## How `parse_synctex.py` uses these

`parse_synctex.py` builds two indices in memory:

```python
# forward: (abs_file, line) -> [list of (page, x, y, w, h)]
fwd: dict[tuple[str, int], list[tuple[int, float, float, float, float]]]

# reverse: (page, x_band, y_band) -> (abs_file, line)
rev: KDTree-like structure over PDF coordinates
```

Reverse lookup is approximate (KDTree nearest-neighbor) because PDF
coordinates from `parse_pdf.py` are bbox centers of text blocks, not
glyph anchors. We accept some imprecision — it is much cheaper than
running `synctex edit` per text block.

## Multi-file projects (`\input`, `\include`)

SyncTeX records absolute file paths. `parse_synctex.py` normalizes them
to paths *relative to the main file's directory* before storing, so the
output `state.json` is portable.

## When SyncTeX lies

1. **`\input` inside a macro definition.** SyncTeX records the macro call
   site, not the included file. Heuristic: if reverse-lookup says the
   source is line 1 of a file, distrust it and fall back to forward-lookup
   from neighboring text blocks.
2. **`tabular` / `align` cells.** SyncTeX records the cell as a single
   point; the inferred line is approximately right but column and offset
   are unreliable.
3. **Floats placed by LaTeX.** The point inside a figure has a SyncTeX
   record, but the *placement page* is not necessarily the page of the
   `\begin{figure}` source line. `parse_synctex.py` distinguishes
   `placement_page` (PDF page of the rendered float) from `source_page`
   (page where the float environment opens).

## Required tooling

- `synctex` CLI on `$PATH` (TeX Live ≥ 2018 ships it).
- `gunzip` for `.synctex.gz`. The CLI handles this transparently; the
  Python wrapper does too via `subprocess.run`.

## Failure modes

- `latexmk` ran without `-synctex=1` → `.synctex.gz` missing. `parse_synctex.py`
  detects this and aborts with the exact remediation command.
- `.synctex.gz` is older than the PDF → stale index. `parse_synctex.py`
  refuses and triggers `compile_once.py` rerun.
