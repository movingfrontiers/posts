"""chart-11-china-annual-addition.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-11-china-annual-addition.py

It writes chart-11-china-annual-addition.png and chart-11-china-annual-addition
.csv into the working directory.

WHY THIS IS A TIME SERIES AND NOT THREE BARS
--------------------------------------------
Earlier cuts picked 1990, 2007 and 2025 and read a story off the three. Single
year additions in current dollars are far too volatile for that: China added
3,205 billion dollars in 2021, 115 billion in 2022 and minus 46 billion in 2023.
Any claim about the trend can be reversed by choosing a different pair of years,
so the whole series is drawn and the reader can see the shape.

What is plotted is a three-year centred average. The single-year ratios are kept
in the csv. Most of the year-to-year movement is the exchange rate and the price
level rather than the flow of new output, which is why the average is the line
drawn.

HOW THE NUMBERS ARE BUILT
-------------------------
A year's addition is that year's GDP less the preceding year's, on the World Bank
WDI series for GDP in current US dollars (NY.GDP.MKTP.CD). Each benchmark economy
is measured in the same year as the addition it is compared with, so part of any
common dollar movement cancels in the ratio, but only the part common to all the
economies shown.

VINTAGES. China, Germany, Brazil and Korea come from a WDI extract dated 13 July
2026. The United States and Japan come from the same WDI series retrieved through
FRED, dated 30 June 2026 and 7 July 2026. The three sit in the same release
window; if a later extract covers all six at once it should replace this table.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
# World Bank WDI, GDP in current US dollars (NY.GDP.MKTP.CD).
# ======================================================================

RAW = """\
year,china_added_bn,korea_gdp_bn,brazil_gdp_bn,japan_gdp_bn,germany_gdp_bn
1990,13.2,292.1,385.0,3253.0,1778.2
1991,23.0,340.9,342.5,3724.9,1875.8
1992,44.0,366.9,328.2,4064.5,2141.4
1993,18.1,405.7,368.3,4632.5,2079.0
1994,120.4,479.2,525.4,5104.1,2215.3
1995,171.3,586.3,769.3,5639.6,2593.1
1996,130.3,631.2,850.4,5021.4,2506.6
1997,99.2,589.2,883.2,4579.8,2218.8
1998,69.4,397.3,863.7,4150.4,2247.8
1999,66.7,515.7,599.6,4689.0,2213.9
2000,119.9,597.5,655.4,5042.4,1967.0
2001,131.3,567.6,560.0,4438.8,1966.4
2002,134.8,650.0,509.8,4245.9,2102.4
2003,194.1,728.5,558.2,4573.4,2534.7
2004,300.3,823.3,669.3,4941.5,2852.3
2005,333.4,971.7,891.6,4875.6,2893.4
2006,473.9,1095.2,1107.6,4648.1,3046.3
2007,812.6,1220.9,1397.1,4624.7,3484.1
2008,1063.3,1091.6,1695.9,5160.2,3808.2
2009,522.2,983.1,1667.0,5336.8,3478.5
2010,1003.0,1192.8,2208.8,5811.6,3467.1
2011,1479.2,1307.1,2616.2,6279.4,3823.6
2012,1001.9,1335.3,2465.2,6333.8,3596.5
2013,1069.5,1434.7,2472.8,5272.3,3807.0
2014,931.4,1556.3,2456.0,4985.8,3964.9
2015,606.3,1539.2,1802.2,4534.4,3425.1
2016,175.2,1579.2,1795.7,5110.4,3536.8
2017,1081.5,1710.2,2063.5,5038.2,3765.4
2018,1610.2,1824.3,1916.9,5154.3,4055.4
2019,412.4,1751.0,1873.3,5245.8,3959.9
2020,436.2,1744.1,1476.1,5189.2,3941.4
2021,3205.3,1942.3,1670.6,5225.9,4355.3
2022,115.1,1799.4,1951.9,4448.0,4201.0
2023,-46.4,1844.8,2191.1,4384.9,4562.2
2024,459.3,1875.4,2185.8,4190.0,4685.6
2025,768.4,1872.4,2279.9,4435.2,5050.9
"""

STEM = "chart-11-china-annual-addition"
df = pd.read_csv(io.StringIO(RAW))

BENCH = ["korea", "brazil", "japan", "germany"]
for b in BENCH:
    df[b + "_pct"] = (df["china_added_bn"] / df[b + "_gdp_bn"] * 100).round(2)
    df[b + "_pct_3yr"] = df[b + "_pct"].rolling(3, center=True, min_periods=1).mean().round(2)
df.to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================

# Four benchmarks, so the four house colours cover it exactly. Ordered by 2025
# size, smallest economy first, which is also the order the lines finish in.
SERIES = [("korea", "Korea", BLUE, BLUE),
          ("brazil", "Brazil", RED, RED),
          ("japan", "Japan", GREEN, GREEN),
          ("germany", "Germany", GOLD, "#B8860B")]
GRID = "#E6E6E6"
LABEL_X = 2026.3
MIN_SEP = 4.2             # least vertical room between two end labels, in points of the y scale

TITLE = ("China's slower growth still adds a current Korea to the global economy every "
         "three years")
SUBTITLE = ("China's annual increase in GDP, measured against the whole economies of Korea, "
            "Brazil, Japan and Germany, current US dollars")
SOURCE = "World Bank World Development Indicators, GDP in current US dollars (NY.GDP.MKTP.CD)."
NOTE = ("A year's addition is that year's GDP less the preceding year's, so it reflects output, "
        "domestic inflation and the exchange rate together. All lines are three-year centred "
        "averages. Each benchmark economy is measured in the same year as the addition it is "
        "compared with.")


def declutter(points, min_sep):
    """Nudge crowded end labels apart, downwards from the highest, so the top of a
    cluster keeps its own position."""
    order = sorted(points, key=lambda t: t[0], reverse=True)
    ys = [y for y, _ in order]
    for i in range(1, len(ys)):
        ys[i] = min(ys[i], ys[i - 1] - min_sep)
    return [(y, lab) for y, (_, lab) in zip(ys, order)]


rc()
fig, ax = plt.subplots(figsize=(10.6, 5.4), dpi=DPI)
fig.subplots_adjust(left=0.072, right=0.845, top=0.965, bottom=0.11)

YEARS = df["year"].values
ax.axhline(0, color=GREY, lw=1.0, zorder=2)
ends = []
for col, name, colour, ink in SERIES:
    ax.plot(YEARS, df[col + "_pct_3yr"], color=colour, lw=2.5, solid_capstyle="round", zorder=4)
    ends.append((df[col + "_pct_3yr"].iloc[-1], (name, ink)))
for y, (name, ink) in declutter(ends, MIN_SEP):
    ax.text(LABEL_X, y, name, color=ink, fontsize=LABEL_PT, fontweight="bold", va="center",
            ha="left", clip_on=False, zorder=5)

ax.set_xlim(1990, 2025)
ax.set_xticks([1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025])
ax.set_ylim(-4, 100)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel("percent of that economy's GDP", labelpad=8)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, lw=0.8)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)

fig.savefig("_plot11.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot11.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
