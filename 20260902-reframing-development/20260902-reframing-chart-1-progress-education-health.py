"""chart-1-progress-education-health.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-1-progress-education-health.py

It writes chart-1-progress-education-health.png and
chart-1-progress-education-health.csv into the working directory.
"""

import io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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
# World Development Indicators, as tabulated in UNDP's Asia-Pacific Human
# Development Dashboard (July 2025), panels 1-5 and 1-6.
# ======================================================================

RAW = """\
region,indicator,earlier_year,earlier,later_year,later
Latin America & Caribbean,Adult literacy,1990,88.6,Latest,95.2
Asia and the Pacific,Adult literacy,1990,66.0,Latest,87.7
Arab States,Adult literacy,1990,53.9,Latest,81.2
sub-Saharan Africa,Adult literacy,1990,51.0,Latest,65.3
Latin America & Caribbean,Short-cycle tertiary completion,1990,11.2,Latest,20.1
Asia and the Pacific,Short-cycle tertiary completion,1990,6.6,Latest,17.7
Arab States,Short-cycle tertiary completion,1990,16.4,Latest,18.5
sub-Saharan Africa,Short-cycle tertiary completion,1990,1.5,Latest,9.3
Latin America & Caribbean,Under-five mortality,1980,80.9,2022,14.9
Asia and the Pacific,Under-five mortality,1980,105.8,2022,21.0
Arab States,Under-five mortality,1980,134.1,2022,26.2
sub-Saharan Africa,Under-five mortality,1980,199.7,2022,68.1
Latin America & Caribbean,Life expectancy at birth,1980,63.6,2022,73.7
Asia and the Pacific,Life expectancy at birth,1980,60.5,2022,72.9
Arab States,Life expectancy at birth,1980,57.3,2022,71.2
sub-Saharan Africa,Life expectancy at birth,1980,48.3,2022,60.6
"""

STEM = "chart-1-progress-education-health"
data = pd.read_csv(io.StringIO(RAW))
data.to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================

RED, BLUE = palette(2)            # earlier year, later year
LINK = "#C9C9C9"                  # the arrow between the two dots
GRID = "#DEDEDE"

# rows, top to bottom, the same order in every panel
ROWS = ["Latin America & Caribbean", "Asia and the Pacific",
        "Arab States", "sub-Saharan Africa"]
WRAPPED = {"Latin America & Caribbean": "Latin America\n& Caribbean",
           "Asia and the Pacific": "Asia and\nthe Pacific",
           "sub-Saharan Africa": "sub-Saharan\nAfrica"}
Y = {r: y for r, y in zip(ROWS, [3, 2, 1, 0])}

# indicator, units line, x limits, ticks
PANELS = [
    ("Adult literacy",
     "% of people aged 15 and above, 1990 and latest", (40, 108), [40, 60, 80, 100]),
    ("Short-cycle tertiary completion",
     "% of people aged 25 and above, 1990 and latest", (-3.5, 25), [0, 5, 10, 15, 20]),
    ("Under-five mortality",
     "deaths per 1,000 live births, 1980 and 2022", (-16, 232), [0, 50, 100, 150, 200]),
    ("Life expectancy at birth",
     "years, 1980 and 2022", (42.5, 80), [50, 60, 70, 80]),
]

TITLE = "The world has made substantial long-term progress"
SUBTITLE = ("Adult literacy, short-cycle tertiary completion, under-five mortality and life "
            "expectancy, by developing region")
SOURCE = "World Bank, World Development Indicators."
NOTE = ("The two education panels compare 1990 with the latest available year, which differs by "
        "economy, while the two health panels compare 1980 with 2022. The completion measure is "
        "cumulative: it counts everyone aged 25 and above who has completed at least a short-cycle "
        "tertiary programme, ISCED level 5, and so includes those who went on to a bachelor's "
        "degree or higher.")


def whole(v):
    """Round half up. Python's format() rounds half to even, which would print the
    Arab States' 18.5 as 18 and Asia and the Pacific's 60.5 as 60."""
    return "{:.0f}".format(math.floor(v + 0.5))


def panel(ax, indicator, units, xlim, ticks):
    lo, hi = xlim
    pad = 0.022 * (hi - lo)
    rows = data[data["indicator"] == indicator]
    for _, r in rows.iterrows():
        y, a, b = Y[r["region"]], r["earlier"], r["later"]
        ax.plot([a, b], [y, y], color=LINK, lw=3.0, solid_capstyle="round", zorder=2)
        ax.scatter([a], [y], s=95, color=RED, zorder=3, clip_on=False)
        ax.scatter([b], [y], s=95, color=BLUE, zorder=3, clip_on=False)
        # both values are labelled, each on the outer side of its own dot, so no label
        # ever sits on the connector. Mortality falls, so its two sides are reversed.
        rising = b >= a
        ax.text(a - pad if rising else a + pad, y, whole(a), color=RED,
                fontsize=LABEL_PT, va="center", ha="right" if rising else "left",
                fontweight="bold", zorder=4)
        ax.text(b + pad if rising else b - pad, y, whole(b), color=BLUE,
                fontsize=LABEL_PT, va="center", ha="left" if rising else "right",
                fontweight="bold", zorder=4)

    ax.set_yticks([Y[r] for r in ROWS])
    ax.set_yticklabels([WRAPPED.get(r, r) for r in ROWS])
    ax.set_ylim(-0.55, 3.55)
    ax.set_xlim(lo, hi)
    ax.set_xticks(ticks)
    ax.set_xlabel(units, labelpad=9)
    ax.set_title(indicator, loc="left", fontsize=AXIS_PT + 1.5, fontweight="bold",
                 color=INK, pad=14)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)


rc()
fig, axes = plt.subplots(2, 2, figsize=(11.7, 7.6), dpi=DPI)
fig.subplots_adjust(left=0.105, right=0.995, top=0.875, bottom=0.085,
                    wspace=0.30, hspace=0.62)

for ax, spec in zip(axes.ravel(), PANELS):
    panel(ax, *spec)
for ax in (axes[0, 1], axes[1, 1]):
    ax.set_yticklabels([])

handles = [Line2D([], [], marker="o", ls="", ms=9, color=RED, label="Earlier year"),
           Line2D([], [], marker="o", ls="", ms=9, color=BLUE, label="Later year")]
# the legend sits on its own line, centred, above the row of panel titles
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.0),
           ncol=2, frameon=False, handletextpad=0.4, columnspacing=2.2,
           fontsize=LEGEND_PT, borderpad=0.0, borderaxespad=0.0)

fig.savefig("_plot1.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot1.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
