# ptouch-labelstrip

Render a strip of fixed-width, centre-aligned labels to a 1-bit PNG for
printing on Brother P-touch label printers via
[`ptouch-print`](https://dominic.familie-radermacher.ch/projekte/ptouch-print/).

Built for tidy, uniform electronics-drawer labels: every cell the same width,
text centred, thin vertical lines between cells as cut guides, and the whole
batch printed in a single pass so you only waste tape margin once.

```
python3 ptouch-labelstrip.py drawer_labels.csv strip.png
ptouch-print --image strip.png
```

## Why a PNG instead of `ptouch-print --text`?

`ptouch-print` has no width, alignment, or fixed-cell options — its text mode
auto-sizes each block to its own content. Rendering the strip yourself as one
monochrome PNG and printing it with `--image` gives full control over width,
centring, and separators.

## Requirements

- Python 3
- [Pillow](https://pypi.org/project/Pillow/) (`pip install pillow`)
- `ptouch-print` (built from source recommended; distro snaps are often stale)
- A TrueType font (defaults to DejaVu Sans Bold)

## CSV format

One label per row; each column is one text line. Ragged rows are fine.

```csv
ESP32,WROOM-32
10k,0805
100nF,X7R
BSS138,SOT-23
```

`ESP32,WROOM-32` → a two-line label with both lines centred.
`10k,0805` → likewise. A single value → a one-line label.

## Configuration

Edit the constants at the top of `ptouch-labelstrip.py`:

| Constant | What it does |
|----------|--------------|
| `TAPE_HEIGHT_PX` | Printable height in px. **Get the real value from `ptouch-print --info`** for your tape. |
| `CELL_WIDTH_PX`  | `None` = auto (widest label sets the common width). Set an int to pin every cell. |
| `FIT_MODE`       | `"uniform"` = one font size for the whole strip (overflows if a pinned cell is too narrow); `"shrink"` = shrink only the labels that don't fit. |
| `FONT_PATH`      | Path to any `.ttf`/`.otf`. |
| `MAX_FONT` / `MIN_FONT` | Bounds for the auto-fit search. |
| `INNER_PAD_X`    | Blank px left+right of text inside each cell. |
| `EDGE_MARGIN_PX` | Blank tape before the first / after the last label. |
| `SEP_WIDTH_PX`   | Cut-guide line thickness. |
| `LINE_GAP_PX`    | Gap between stacked text lines. |

### Sizing in millimetres

The H500 / P700 / E500 family prints at **180 dpi**:

```
px = mm × 180 / 25.4  ≈  mm × 7.087     (e.g. 25 mm → 177 px)
mm = px × 25.4 / 180  ≈  px × 0.1411
```

Usable text width inside a cell is `CELL_WIDTH_PX − 2 × INNER_PAD_X`.

## Notes

- Output is a true bilevel (mode `"1"`) PNG, which satisfies `ptouch-print`'s
  two-colour requirement and matches the printer's native output. If a build
  rejects it, convert to a 2-entry palette (`img.convert("P")`).
- `ptouch-print` treats image **height** as the across-tape dimension and
  **width** as length along the tape — which is how the strip is built.
- The printed separator lines are your cut guides: print the strip, then cut
  at each line.
- Tested against the `ptouch-print` master branch. Note its multi-line `--text`
  syntax changed at v1.7 — irrelevant here since this uses `--image`.

---

*Code and README written with Claude Opus 4.8 (Anthropic), then reviewed and
adapted by a human.*
