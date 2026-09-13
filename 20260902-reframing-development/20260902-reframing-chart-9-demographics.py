"""chart-9-demographics.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-9-demographics.py

It writes chart-9-demographics.png and chart-9-demographics.csv into the working
directory.

TWO CHOICES WORTH KNOWING ABOUT
-------------------------------
* The two panels share one vertical scale. In the chart this is drawn from, the
  right-hand panel was scaled to its own data, which made the elderly cohorts
  look as tall as the youth cohorts when they are not, and left a stray "1e-9"
  exponent on the axis because the values were already in billions. With a
  common scale the comparison is honest, and the thing worth seeing appears: by
  2100 the 60-and-over line ends above the under-25 line.
* Colour is keyed to how broad a cohort is, not to which panel it sits in: blue
  is the widest band in each panel (under 25, and 60 and over), gold the middle
  one, red the narrowest. So the reader learns the key once and it holds across
  both panels.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
# DATA
# UN World Population Prospects, 2024 revision, world totals in billions.
# ======================================================================

RAW_YOUTH = """\
Year,Under_5,Under_15,Under_25
1950,0.35,0.86,1.32
1960,0.48,1.15,1.71
1970,0.55,1.38,2.08
1980,0.58,1.56,2.45
1990,0.65,1.80,2.78
2000,0.63,1.86,2.98
2010,0.67,1.95,3.18
2017,0.70,2.01,3.25
2020,0.68,2.04,3.28
2030,0.67,1.93,3.31
2040,0.67,1.96,3.25
2050,0.66,1.93,3.26
2060,0.64,1.87,3.20
2070,0.62,1.80,3.12
2080,0.59,1.74,3.03
2090,0.57,1.70,2.95
2100,0.55,1.68,2.87
"""

RAW_OLDER = """\
Year,Aged_60_plus,Aged_70_plus,Aged_80_plus
1950,0.20,0.08,0.02
1960,0.23,0.10,0.03
1970,0.29,0.13,0.04
1980,0.38,0.16,0.05
1990,0.48,0.21,0.07
2000,0.61,0.27,0.09
2010,0.77,0.35,0.13
2020,1.05,0.47,0.16
2030,1.40,0.67,0.23
2040,1.78,0.93,0.34
2050,2.10,1.18,0.46
2060,2.38,1.39,0.58
2070,2.59,1.55,0.70
2080,2.79,1.69,0.77
2090,2.90,1.82,0.88
2100,3.00,1.89,0.94
"""

STEM = "chart-9-demographics"
youth = pd.read_csv(io.StringIO(RAW_YOUTH))
older = pd.read_csv(io.StringIO(RAW_OLDER))

# one tidy table beside the chart
tidy = pd.concat([
    youth.melt(id_vars="Year", var_name="series", value_name="billions").assign(panel="under"),
    older.melt(id_vars="Year", var_name="series", value_name="billions").assign(panel="aged"),
])
tidy["series"] = tidy["series"].str.replace("_", " ", regex=False)
tidy = tidy.rename(columns={"Year": "year"})[["year", "panel", "series", "billions"]]
tidy.sort_values(["panel", "series", "year"]).to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================

RED, BLUE, GOLD = palette(3)
GOLD_INK = "#B8860B"      # house gold is too light to read as a small bold label
PROJ_FROM = 2025
PROJ_FILL = "#F2F2F2"
GRID = "#E6E6E6"

# panel: frame, table, and the three series widest first
PANELS = [
    ("Population under age thresholds", youth,
     [("Under_25", "Under 25", BLUE, BLUE),
      ("Under_15", "Under 15", GOLD, GOLD_INK),
      ("Under_5", "Under 5", RED, RED)]),
    ("Population aged 60, 70 and 80 and above", older,
     [("Aged_60_plus", "60 and over", BLUE, BLUE),
      ("Aged_70_plus", "70 and over", GOLD, GOLD_INK),
      ("Aged_80_plus", "80 and over", RED, RED)]),
]

# the year each youth cohort tops out in this series, and where its label sits
PEAKS = [("Under_5", 2017, 0.06), ("Under_15", 2020, 0.10), ("Under_25", 2030, 0.10)]

XLIM = (1950, 2100)
YLIM = (0, 3.55)
LABEL_X = 2103

TITLE = "The world has reached Peak Youth, with elderly cohorts expanding rapidly"
SUBTITLE = "World population by age group, billions, 1950 to 2100"
SOURCE = "UN World Population Prospects, 2024 revision."
NOTE = "Values from 2025 are the medium variant projection, shaded."

FIGW, FIGH = 11.6, 5.7

rc()
fig, axes = plt.subplots(1, 2, figsize=(FIGW, FIGH), dpi=DPI)
fig.subplots_adjust(left=0.058, right=0.915, top=0.905, bottom=0.115, wspace=0.26)

for ax, (heading, tab, series) in zip(axes, PANELS):
    ax.axvspan(PROJ_FROM, XLIM[1], color=PROJ_FILL, zorder=0)
    for col, label, colour, ink in series:
        ax.plot(tab["Year"], tab[col], color=colour, lw=2.6, solid_capstyle="round", zorder=3)
        ax.text(LABEL_X, tab[col].iloc[-1], label, color=ink, fontsize=LABEL_PT,
                fontweight="bold", va="center", ha="left", clip_on=False, zorder=4)

    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_xticks([1960, 1980, 2000, 2020, 2040, 2060, 2080, 2100])
    ax.set_yticks([0, 1, 2, 3])
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_title(heading, loc="left", fontsize=AXIS_PT + 1.5, fontweight="bold", color=INK,
                 pad=12)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    # low in the shaded band, where neither panel has a line running
    ax.text(PROJ_FROM + 2.5, 0.075, "projected", fontsize=LABEL_PT, color=SUB_INK,
            style="italic", ha="left", va="bottom", zorder=2)

# peak markers, on the youth panel only: the elderly cohorts do not turn over this century
ax = axes[0]
for col, year, dy in PEAKS:
    v = float(youth.loc[youth["Year"] == year, col].iloc[0])
    colour = dict((c[0], c[2]) for c in PANELS[0][2])[col]
    ax.scatter([year], [v], s=48, color=colour, zorder=5)
    ax.text(year - 2, v + dy, str(year), color=INK, fontsize=LABEL_PT, fontweight="bold",
            ha="right", va="bottom", zorder=5)

axes[0].set_ylabel("billions", labelpad=8)

fig.savefig("_plot9.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot9.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
