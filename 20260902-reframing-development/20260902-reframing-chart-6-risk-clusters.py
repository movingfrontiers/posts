"""chart-6-risk-clusters.py

Self-contained: the Moving Frontiers house style, the content and the figure in
one file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-6-risk-clusters.py

It writes chart-6-risk-clusters.png and chart-6-risk-clusters.csv into the
working directory.

WHAT THIS IS
------------
A schematic, not a plot of data. Three circles of equal size, set at the corners
of an equilateral triangle so that every pair overlaps by the same amount and
all three meet in the middle. Neither the area of a circle nor the size of an
overlap stands for a quantity; the geometry says only that the three clusters
are of comparable weight and that they interact. That is stated in the note, so
a reader does not read a measurement into the picture.

Each cluster takes one house colour at low opacity, and the bullet mark in front
of every item is drawn in its cluster's colour, which is what ties a list to the
circle it belongs to. The lists sit beside the circle they describe.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
import pandas as pd

# ======================================================================
# HOUSE STYLE  (moving_frontiers_style.py, inlined)
# ======================================================================

import os
import numpy as np
import matplotlib
from PIL import Image, ImageDraw, ImageFont

DPI = 200

# ---- colours: the main elements, by how many series the chart has ----
RED, GOLD, GREEN, BLUE = "#C62828", "#F9A825", "#00897B", "#283593"
PALETTE = {1: [BLUE],
           2: [RED, BLUE],
           3: [RED, BLUE, GOLD],
           4: [RED, GOLD, GREEN, BLUE]}
GREY = "#888888"          # axes, rules, de-emphasised marks


def palette(n):
    assert n in PALETTE, "the house palette covers one to four series"
    return PALETTE[n]


# ---- spacing, in pixels at 200 dpi, every gap ink to ink ----
GAP_TITLE_SUB = 25        # subtitle below the title
GAP_SUB_PLOT  = 70        # plot below the subtitle
GAP_PLOT_CAP  = 60        # caption below the plot
GAP_CAP_MARK  = 20        # watermark below the last caption line
MARK_RIGHT    = 15        # watermark right edge, inside the content right edge
BORDER        = 70        # empty space around the whole canvas

# Canvas width is allowed to differ from chart to chart: each canvas is just the plot
# plus the border. Pass content_w=<px> to compose() to pad a narrow plot out to a
# common width instead, which is optional.
CONTENT_W     = None

# Type is fixed, not scaled to the chart. Sizing the title from the plot width made
# it depend on how much white space matplotlib happened to leave, so a narrow chart
# got a smaller title than a wide one in the same pack.
# TYPE SCALES WITH THE CANVAS, so that a chart shown at a fixed display width, a
# phone column say, always shows the same apparent type whatever its own pixel width.
# The point sizes below are the sizes at REF_W; a canvas half again as wide gets type
# half again as large, and the two look identical once both are scaled to the column.
# Sizing type from the plot width, as an earlier version did, is not the same thing and
# was a bug: it made the title depend on how much white space matplotlib happened to
# leave around the axes rather than on how large the image is.
REF_W      = 1980         # reference canvas width the point sizes below refer to
TITLE_PT   = 19.44        # title, 54px at REF_W
SUB_FRAC   = 0.68         # subtitle as a share of the title
CAP_PT     = 8.5          # caption, 24px at REF_W
MARK_MULT  = 1.2          # watermark as a share of the caption
LEADING    = 1.32

# Type inside the plot. Set once here and applied by rc(), so every chart in a pack
# carries the same tick labels, axis titles and annotations. A build script that
# passes its own fontsize= breaks that, so use these constants instead.
AXIS_PT    = 13           # axis titles
TICK_PT    = 12           # tick labels, both axes
LEGEND_PT  = 12           # legend entries
LABEL_PT   = 11.5         # in-plot labels and data values
EMPH_PT    = 15           # emphasised data values, bold

INK        = "#2D2D2D"    # title
SUB_INK    = "#646464"    # subtitle
CAP_INK    = "#555555"    # caption
MARK_INK   = "#999999"    # watermark
MARK_TEXT  = "movingfrontiers.substack.com"
CREDIT     = ""


def rc():
    """Matplotlib defaults for the plot itself."""
    matplotlib.pyplot.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": AXIS_PT,
        "axes.labelsize": AXIS_PT, "xtick.labelsize": TICK_PT,
        "ytick.labelsize": TICK_PT, "legend.fontsize": LEGEND_PT,
        "axes.edgecolor": GREY, "axes.linewidth": 1.0,
        "figure.facecolor": "white", "axes.facecolor": "white"})


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _font(px, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for p in (os.path.join(matplotlib.get_data_path(), "fonts", "ttf", name),
              "/usr/share/fonts/truetype/dejavu/" + name):
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    raise FileNotFoundError(name)


def _ink(font, s):
    """Ink top and bottom of a string relative to its baseline."""
    b = font.getbbox(s, anchor="ls")
    return b[1], b[3]


def _ink_left(font, s):
    """How far the first glyph's ink sits from the pen position. Usually zero, but a
    few capitals carry a negative left side bearing, so a line starting with one puts
    ink a pixel outside the border that verify() insists on. Drawing at x minus this
    lines the ink up with the border instead of the pen."""
    return font.getbbox(s, anchor="ls")[0]


def _wrap(font, paragraphs, width):
    """Greedy wrap. Also returns, for each line, which paragraph it came from, so a
    line that ends because its paragraph ended can be told apart from one that ends
    because the next word would not fit."""
    lines, owner = [], []
    for p, text in enumerate(paragraphs):
        cur = ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if not cur or font.getlength(t) <= width:
                cur = t
            else:
                lines.append(cur); owner.append(p); cur = w
        if cur:
            lines.append(cur); owner.append(p)
    return lines, owner


def _crop(img):
    g = np.array(img.convert("L"))
    r = np.where((g < 250).any(1))[0]
    c = np.where((g < 250).any(0))[0]
    return img.crop((c.min(), r.min(), c.max() + 1, r.max() + 1))


def compose(plot_png, out_png, title, subtitle, source, note=None, credit=CREDIT,
            content_w=CONTENT_W):
    """Title band above the plot, caption and watermark below, BORDER px all around."""
    plot = _crop(Image.open(plot_png).convert("RGB"))
    PW, H = plot.size
    W = max(PW, content_w or 0)          # the target is a floor, never a ceiling

    k = (W + 2 * BORDER) / REF_W         # type scales with the canvas, not the plot
    title_px = round(TITLE_PT * DPI / 72 * k)
    cap_px   = round(CAP_PT * DPI / 72 * k)
    f_title = _font(title_px, bold=True)
    f_sub   = _font(int(title_px * SUB_FRAC))
    f_cap   = _font(cap_px)
    f_mark  = _font(round(cap_px * MARK_MULT))

    tl, _ = _wrap(f_title, [title], W)
    sl, _ = _wrap(f_sub, [subtitle], W)
    paras = ["Source: " + source + (" " + credit if credit else "")]
    if note:
        paras.append("Note: " + note)
    cl, owner = _wrap(f_cap, paras, W)
    for i in range(len(cl) - 1):                       # lines must be maximally full
        if owner[i + 1] == owner[i]:
            nxt = cl[i + 1].split()[0]
            assert f_cap.getlength(cl[i] + " " + nxt) > W, \
                f"caption line {i} is not filled to the full width"

    tlh = int(f_title.size * LEADING)
    slh = int(f_sub.size * LEADING)
    clh = int(f_cap.size * LEADING)

    # walk down the page, each gap measured from the ink above it
    y, place = 0, []
    for i, s in enumerate(tl):
        base = y - _ink(f_title, s)[0] if i == 0 else place[-1][0] + tlh
        place.append((base, s, f_title, INK, "left"))
    y = place[-1][0] + _ink(f_title, tl[-1])[1]
    for i, s in enumerate(sl):
        base = (y + GAP_TITLE_SUB - _ink(f_sub, s)[0]) if i == 0 else place[-1][0] + slh
        place.append((base, s, f_sub, SUB_INK, "left"))
    y = place[-1][0] + _ink(f_sub, sl[-1])[1]

    plot_y = y + GAP_SUB_PLOT
    y = plot_y + H

    for i, s in enumerate(cl):
        base = (y + GAP_PLOT_CAP - _ink(f_cap, s)[0]) if i == 0 else place[-1][0] + clh
        place.append((base, s, f_cap, CAP_INK, "left"))
    y = place[-1][0] + _ink(f_cap, cl[-1])[1]
    place.append((y + GAP_CAP_MARK - _ink(f_mark, MARK_TEXT)[0],
                  MARK_TEXT, f_mark, MARK_INK, "right"))
    y = place[-1][0] + _ink(f_mark, MARK_TEXT)[1]

    canvas = Image.new("RGB", (W + 2 * BORDER, y + 2 * BORDER), "white")
    canvas.paste(plot, (BORDER, plot_y + BORDER))     # left, with the title and caption
    d = ImageDraw.Draw(canvas)
    for base, s, f, col, align in place:
        if align == "right":
            x = BORDER + W - MARK_RIGHT - f.getlength(s)
        else:
            x = BORDER - _ink_left(f, s)
        d.text((x, base + BORDER), s, font=f, fill=col, anchor="ls")
    canvas.save(out_png)
    verify(out_png)
    return out_png


def verify(png):
    """Blank pixel rows between each block, and the border, must match the constants."""
    a = np.array(Image.open(png).convert("L"))
    Hh, Ww = a.shape
    ink = a < 250
    rows = np.where(ink.any(1))[0]
    cols = np.where(ink.any(0))[0]
    bands, start, prev = [], rows[0], rows[0]
    for r in rows[1:]:
        if r - prev > 3:
            bands.append((start, prev)); start = r
        prev = r
    bands.append((start, prev))
    gaps = [bands[i + 1][0] - bands[i][1] - 1 for i in range(len(bands) - 1)]
    assert GAP_SUB_PLOT in gaps, f"no {GAP_SUB_PLOT}px gap below the subtitle"
    assert GAP_PLOT_CAP in gaps, f"no {GAP_PLOT_CAP}px gap above the caption"
    assert gaps[-1] == GAP_CAP_MARK, \
        f"gap above the watermark is {gaps[-1]}px, expected {GAP_CAP_MARK}"
    assert (rows[0], Hh - 1 - rows[-1], cols[0]) == (BORDER, BORDER, BORDER), \
        f"top, bottom and left borders are {(rows[0], Hh - 1 - rows[-1], cols[0])}, " \
        f"expected {BORDER}"
    assert Ww - 1 - cols[-1] >= BORDER, \
        f"right border is {Ww - 1 - cols[-1]}, expected at least {BORDER}"
    wm_cols = np.where(ink[bands[-1][0]:bands[-1][1] + 1, :].any(0))[0]
    assert Ww - 1 - wm_cols.max() >= BORDER + MARK_RIGHT - 3, "watermark right margin is wrong"
    return gaps
# ======================================================================
# CONTENT
# UNDP 2024 Regional Human Development Report for Asia and the Pacific.
# ======================================================================

RAW = """\
cluster,item
Headwinds to growth and jobs,Depletion of hydrocarbon resources
Headwinds to growth and jobs,Demographic change
Headwinds to growth and jobs,Technological change
Headwinds to growth and jobs,New patterns in globalisation
Headwinds to growth and jobs,Sovereign debt distress
Headwinds to growth and jobs,Cost-of-living crises
Existential threats,Climate change
Existential threats,Biodiversity loss
Existential threats,Pandemics
Existential threats,Antimicrobial resistance
Existential threats,Artificial intelligence
Growing governance risks,Shrinking civic space
Growing governance risks,Democratic backsliding
Growing governance risks,Erosion of institutional norms
Growing governance risks,State capture and corruption
Growing governance risks,Polarisation and inequality
Growing governance risks,Mis- and disinformation
"""

STEM = "chart-6-risk-clusters"
df = pd.read_csv(io.StringIO(RAW))
df.to_csv(STEM + ".csv", index=False)

# ======================================================================
# FIGURE
# ======================================================================

R = 1.0                   # circle radius
D = 1.15                  # distance between centres, so every pair overlaps alike
FILL_ALPHA = 0.20
STEP = 0.305              # line pitch inside a list
ITEM_PT = 12.5            # list items, a step up from the house LABEL_PT
DOT_S = 44                # the bullet mark
DOT_GAP = 0.185           # from the mark to the start of its text

# House gold is too light to read as a heading or as a small mark, so the gold cluster
# writes in the darker gold the pack already uses for that purpose. The fill stays gold.
MARK = {GOLD: "#B8860B"}

# cluster: colour, circle centre, heading and where it sits, list anchor and top
CLUSTERS = [
    ("Headwinds to growth and jobs", GOLD, (0.0, 0.664),
     "HEADWINDS\nTO GROWTH\nAND JOBS", (0.0, 1.00), (1.72, 2.00)),
    ("Existential threats", RED, (-D / 2, -0.332),
     "EXISTENTIAL\nTHREATS", (-0.86, -0.42), (-3.77, -0.20)),
    ("Growing governance risks", BLUE, (D / 2, -0.332),
     "GROWING\nGOVERNANCE\nRISKS", (0.86, -0.42), (1.72, -0.32)),
]

TITLE = "Three clusters of risks are driving turbulence"
SUBTITLE = "Risks shaping development prospects in Asia and the Pacific"
SOURCE = "UNDP 2024 Regional Human Development Report for Asia and the Pacific."
NOTE = None

FIGW, FIGH = 12.6, 6.65
XLIM = (-4.7, 4.7)
YLIM = (-YL, YL) if (YL := FIGH / FIGW * 4.7) else None

rc()
fig = plt.figure(figsize=(FIGW, FIGH), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_aspect("equal")
ax.set_xlim(*XLIM)
ax.set_ylim(*YLIM)
ax.axis("off")

# The circles and their headings move left by a fixed number of pixels; the lists stay
# where they are, which closes the gap on the left and opens the one on the right.
SHIFT_PX = -40
SHIFT = SHIFT_PX / DPI / (FIGW / (XLIM[1] - XLIM[0]))       # pixels to x units

for name, colour, centre, heading, hpos, (lx, ly) in CLUSTERS:
    ax.add_patch(Circle((centre[0] + SHIFT, centre[1]), R, facecolor=colour, alpha=FILL_ALPHA,
                        edgecolor="none", zorder=2))
    mark = MARK.get(colour, colour)
    ax.text(hpos[0] + SHIFT, hpos[1], heading, color=mark, fontsize=AXIS_PT, fontweight="bold",
            ha="center", va="center", linespacing=1.45, zorder=4)

    items = df.loc[df["cluster"] == name, "item"].tolist()
    for j, item in enumerate(items):
        y = ly - j * STEP
        ax.scatter([lx], [y], s=DOT_S, color=mark, edgecolors="none", zorder=4)
        ax.text(lx + DOT_GAP, y, item, color=INK, fontsize=ITEM_PT, ha="left", va="center",
                zorder=4)

fig.savefig("_plot6.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot6.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
