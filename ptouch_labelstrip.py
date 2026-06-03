#!/usr/bin/env python3
"""
ptouch-labelstrip.py - render a strip of fixed-width, centre-aligned labels
to a 1-bit PNG suitable for: ptouch-print --image strip.png

CSV format: one label per row, each column is one text line.
    ESP32,WROOM-32     -> two-line label, both lines centred
    10k 0805           -> one-line label
Empty cells are ignored, so ragged rows are fine.

------------------------------------------------------------------------
WIDTH / SIZE IN MILLIMETRES  (H500 / P700 / E500 family print at 180 dpi)

    px = mm * 180 / 25.4  ~=  mm * 7.087
    mm = px * 25.4 / 180  ~=  px * 0.1411

    e.g. a 25 mm label face -> round(25 * 7.087) = 177 px
    Usable text width inside a cell = CELL_WIDTH_PX - 2 * INNER_PAD_X.
    Get TAPE_HEIGHT_PX for your actual tape from:  ptouch-print --info
------------------------------------------------------------------------
"""

import csv
import sys
from PIL import Image, ImageDraw, ImageFont

# ---- config -------------------------------------------------------------
TAPE_HEIGHT_PX = 76      # printable height in px. GET THE REAL VALUE FROM:
                         #   ptouch-print --info
                         # (12 mm tape on the H500/P700 family reports 76 px)
FONT_PATH      = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_FONT       = 64      # upper bound for the auto-fit search
MIN_FONT       = 6
INNER_PAD_X    = 10      # blank px left+right of text inside each cell
EDGE_MARGIN_PX = 16      # blank tape before first / after last label
SEP_WIDTH_PX   = 2       # vertical cut-guide line thickness
LINE_GAP_PX    = 2       # vertical gap between stacked text lines

CELL_WIDTH_PX  = None    # None = auto: the widest label sets the common width.
                         # Set an int (e.g. round(25 * 7.087) for 25 mm) to pin it.

FIT_MODE       = "uniform"  # "uniform": one font size for the whole strip; a
                            #   label wider than the cell OVERFLOWS its borders
                            #   (only relevant when CELL_WIDTH_PX is pinned too small).
                            # "shrink":  each label keeps the base size unless it
                            #   doesn't fit, in which case ONLY that label shrinks
                            #   to fit the cell width. Guarantees fit; sacrifices a
                            #   single consistent type size across the strip.
# -------------------------------------------------------------------------


def load_labels(path):
    out = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            lines = [c.strip() for c in row if c.strip()]
            if lines:
                out.append(lines)
    return out


def fit_height(max_lines):
    """Largest size whose (ascent+descent) * max_lines fits the tape height."""
    avail = (TAPE_HEIGHT_PX - LINE_GAP_PX * (max_lines - 1)) // max_lines
    for size in range(MAX_FONT, MIN_FONT - 1, -1):
        font = ImageFont.truetype(FONT_PATH, size)
        asc, desc = font.getmetrics()
        if asc + desc <= avail:
            return font
    return ImageFont.truetype(FONT_PATH, MIN_FONT)


def fit_cell(draw, lbl, cell_w, base_size):
    """Largest size <= base_size that fits cell width for every line in lbl."""
    usable = cell_w - 2 * INNER_PAD_X
    for size in range(base_size, MIN_FONT - 1, -1):
        f = ImageFont.truetype(FONT_PATH, size)
        if all(text_w(draw, ln, f) <= usable for ln in lbl):
            return f
    return ImageFont.truetype(FONT_PATH, MIN_FONT)


def text_w(draw, s, font):
    return draw.textbbox((0, 0), s, font=font)[2]


def main():
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} labels.csv out.png")
    csv_path, out_path = sys.argv[1], sys.argv[2]

    labels = load_labels(csv_path)
    if not labels:
        sys.exit("no labels found in CSV")

    max_lines = max(len(l) for l in labels)
    base_font = fit_height(max_lines)
    scratch = ImageDraw.Draw(Image.new("1", (1, 1)))

    if CELL_WIDTH_PX:
        cell_w = CELL_WIDTH_PX
    else:
        widest = max(text_w(scratch, ln, base_font) for lbl in labels for ln in lbl)
        cell_w = widest + 2 * INNER_PAD_X

    n = len(labels)
    total_w = EDGE_MARGIN_PX * 2 + cell_w * n + SEP_WIDTH_PX * (n - 1)

    img = Image.new("1", (total_w, TAPE_HEIGHT_PX), 1)   # 1 = white
    draw = ImageDraw.Draw(img)

    x = EDGE_MARGIN_PX
    for i, lbl in enumerate(labels):
        if FIT_MODE == "shrink":
            font = fit_cell(scratch, lbl, cell_w, base_font.size)
        else:
            font = base_font
        asc, desc = font.getmetrics()
        line_h = asc + desc

        block_h = line_h * len(lbl) + LINE_GAP_PX * (len(lbl) - 1)
        y0 = (TAPE_HEIGHT_PX - block_h) // 2
        for j, ln in enumerate(lbl):
            w = text_w(draw, ln, font)
            if w > cell_w - 2 * INNER_PAD_X:
                print(f"warning: '{ln}' is wider than the cell; "
                      f"raise CELL_WIDTH_PX, lower MAX_FONT, or use FIT_MODE='shrink'",
                      file=sys.stderr)
            tx = x + (cell_w - w) // 2
            ty = y0 + j * (line_h + LINE_GAP_PX)
            draw.text((tx, ty), ln, font=font, fill=0)   # 0 = black
        x += cell_w
        if i < n - 1:                                    # cut-guide line
            draw.rectangle([x, 0, x + SEP_WIDTH_PX - 1, TAPE_HEIGHT_PX - 1], fill=0)
            x += SEP_WIDTH_PX

    img.save(out_path)
    print(f"wrote {out_path}  ({total_w}x{TAPE_HEIGHT_PX} px, {n} labels, "
          f"cell={cell_w}px, base_font={base_font.size}pt, mode={FIT_MODE})")
    print(f"print with:  ptouch-print --image {out_path}")


if __name__ == "__main__":
    main()
