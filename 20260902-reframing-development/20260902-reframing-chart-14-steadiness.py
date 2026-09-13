"""chart-14-steadiness.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-14-steadiness.py

It writes chart-14-steadiness.png and chart-14-steadiness.csv into the working
directory.

A NOTE ON THE NUMBERS
---------------------
The two bars for each income band are read off the source chart. The net rate is
not read off separately: it is computed as the sum of the two, so the marker sits
exactly where the arithmetic puts it. On the source chart the marker is drawn a
little away from that point in three of the five bands, by up to a tenth of a
percentage point, which is within what can be read off a printed chart but means
the two cannot both be right. Deriving the net keeps the chart internally
consistent, and the note says that is what has been done.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
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
# DATA
# Broadberry and Wallis (2017), as printed on the source chart.
# ======================================================================

RAW = """\
band,growing,shrinking
"Over $20,000",3.22,-0.38
"$10,000 to $20,000",3.80,-0.85
"$5,000 to $10,000",4.00,-1.10
"$2,000 to $5,000",3.28,-1.25
"Under $2,000",2.45,-1.65
"""

# Two-line tick labels, in the order of the table above. They are kept out of the
# embedded CSV because a newline inside an unquoted CSV field splits the record.
LABELS = ["Rich countries\n(over $20,000)", "$10,000 to\n$20,000", "$5,000 to\n$10,000",
          "$2,000 to\n$5,000", "Poor countries\n(under $2,000)"]

STEM = "chart-14-steadiness"
df = pd.read_csv(io.StringIO(RAW))
df["net"] = (df["growing"] + df["shrinking"]).round(2)
df.to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================

# Green for growing, red for shrinking: the two directions read as good and bad
# without the reader having to consult the legend. Both are house colours; the pair
# is taken from the four-colour palette rather than palette(2), which returns blue.
GROW, SHRINK = GREEN, RED
MARK = "#FFFFFF"          # the net rate; it always falls inside the green bar
GRID = "#E6E6E6"
BARW = 0.52

TITLE = "Slow and steady wins the race"
SUBTITLE = ("Contribution of growing and shrinking to the economic performance of countries, "
            "1950 to 2011")
SOURCE = "Broadberry, S., and Wallis, J. J. (2017)."
NOTE = ("Each bar is a frequency times a rate: the contribution of growing is the share of years "
        "an economy grew multiplied by its average rate in those years, and the contribution of "
        "shrinking is the same for the years it shrank. The net rate plotted by the marker is the "
        "sum of the two rather than a separately reported figure.")

rc()
fig, ax = plt.subplots(figsize=(10.2, 6.0), dpi=DPI)
fig.subplots_adjust(left=0.075, right=0.99, top=0.90, bottom=0.155)

x = np.arange(len(df))
ax.bar(x, df["growing"], BARW, color=GROW, zorder=3)
ax.bar(x, df["shrinking"], BARW, color=SHRINK, zorder=3)
ax.axhline(0, color=GREY, lw=1.0, zorder=4)

ax.scatter(x, df["net"], marker="x", s=150, linewidths=1.8, color=MARK, zorder=6)
for xi, v in zip(x, df["net"]):
    ax.text(xi, v - 0.30, "{:.2f}".format(v), color=MARK, fontsize=LABEL_PT, fontweight="bold",
            ha="center", va="top", zorder=6)

ax.set_xticks(x)
ax.set_xticklabels(LABELS, linespacing=1.7)
ax.set_xlim(-0.65, len(df) - 0.35)
ax.set_ylim(-2.2, 4.6)
ax.set_yticks([-2, -1, 0, 1, 2, 3, 4])
ax.set_ylabel("percent a year", labelpad=8)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, lw=0.8)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)
ax.tick_params(axis="x", pad=8)

handles = [Line2D([], [], marker="s", ls="", ms=10, color=GROW, label="Contribution of growing"),
           Line2D([], [], marker="s", ls="", ms=10, color=SHRINK, label="Contribution of shrinking"),
           Line2D([], [], marker="x", ls="", ms=10, mew=1.8, color=MARK,
                  label="Net rate of growth",
                  # white on white paper would vanish, so the legend mark carries the
                  # green of the bar it sits on in the chart
                  path_effects=[pe.Stroke(linewidth=6, foreground=GROW), pe.Normal()])]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=3,
          frameon=False, fontsize=LEGEND_PT, handletextpad=0.4, columnspacing=2.2,
          borderpad=0.0, borderaxespad=0.0)

fig.savefig("_plot14.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot14.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
