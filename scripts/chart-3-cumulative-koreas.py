"""chart-3-cumulative-koreas.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-3-cumulative-koreas.py

It writes chart-3-cumulative-koreas.png and chart-3-cumulative-koreas.csv into the working directory.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines
import matplotlib.patches
import numpy as np
import pandas as pd

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
# History: WDI GDP in current US dollars (NY.GDP.MKTP.CD, 13 July 2026 extract), to 2025.
# Projection: IMF World Economic Outlook, April 2026, China and Korea GDP in current US dollars
# (NGDPD), 2026 to 2031.
# ======================================================================

HIST = """\
year,china_added_bn,korea_gdp_bn
1977,21.0,39.1
1978,-25.4,52.8
1979,28.8,68.1
1980,12.9,66.5
1981,4.7,74.3
1982,9.3,79.9
1983,25.6,89.6
1984,29.3,99.7
1985,49.6,103.8
1986,-8.8,120.0
1987,-27.9,152.2
1988,39.4,205.5
1989,35.5,254.2
1990,13.2,292.1
1991,23.0,340.9
1992,44.0,366.9
1993,18.1,405.7
1994,120.4,479.2
1995,171.3,586.3
1996,130.3,631.2
1997,99.2,589.2
1998,69.4,397.3
1999,66.7,515.7
2000,119.9,597.5
2001,131.3,567.6
2002,134.8,650.0
2003,194.1,728.5
2004,300.3,823.3
2005,333.4,971.7
2006,473.9,1095.2
2007,812.6,1220.9
2008,1063.3,1091.6
2009,522.2,983.1
2010,1003.0,1192.8
2011,1479.2,1307.1
2012,1001.9,1335.3
2013,1069.5,1434.7
2014,931.4,1556.3
2015,606.3,1539.2
2016,175.2,1579.2
2017,1081.5,1710.2
2018,1610.2,1824.3
2019,412.4,1751.0
2020,436.2,1744.1
2021,3205.3,1942.3
2022,115.1,1799.4
2023,-46.4,1844.8
2024,459.3,1875.4
2025,768.4,1872.4
"""
h = pd.read_csv(io.StringIO(HIST))
h["pct"] = h["china_added_bn"] / h["korea_gdp_bn"] * 100
h = h[h["year"] >= 2000].reset_index(drop=True)
IMF_YEARS = np.arange(2026, 2032)
IMF_CHINA = np.array([19626.25, 20851.59, 21928.98, 23259.96, 24662.79, 26046.79, 27496.67])  # 2025 to 2031
IMF_KOREA = np.array([1931.01, 2010.46, 2094.33, 2181.45, 2266.93, 2357.31])                 # 2026 to 2031
imf_add = np.diff(IMF_CHINA)
imf_pct = imf_add / IMF_KOREA * 100
YEARS = np.concatenate([h["year"].values, IMF_YEARS])
PCT = np.concatenate([h["pct"].values, imf_pct])
ADD = np.concatenate([h["china_added_bn"].values, imf_add])
KOR = np.concatenate([h["korea_gdp_bn"].values, IMF_KOREA])
IS_IMF = YEARS >= 2026
LEVEL0 = 1103.8          # China's GDP in 1999, bn current US dollars (WDI), so levels can be rebuilt from the additions
GRID = "#E6E6E6"

# House type for the square pack (base 15, ticks 14, legend 14, axis labels 15). The composed
# canvas is about 1640 px wide against REF_W 1980, so the title and caption point sizes are
# raised by that ratio to land at the house pixel sizes (54 px title, 24 px caption).
AXIS_PT, TICK_PT, LEGEND_PT, LABEL_PT, EMPH_PT = 15, 14, 14, 14, 17
TITLE_PT, CAP_PT = TITLE_PT * 1980 / 1640, CAP_PT * 1980 / 1640
TITLE = ("Despite slower growth, China continues to add a Korea to the global economy every "
         "other year")
SOURCE = ("World Bank World Development Indicators, 13 July 2026 (NY.GDP.MKTP.CD), to 2025; IMF World "
          "Economic Outlook, April 2026 (NGDPD), 2026 to 2031.")

def square_axes(figsize=(8.6, 7.4), left=0.11, right=0.90, top=0.965, bottom=0.10):
    rc()
    fig, ax = plt.subplots(figsize=figsize, dpi=DPI)
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=5, width=1.0, color=GREY, direction="out")
    return fig, ax

def finish(fig, stem, subtitle, note):
    fig.savefig("_plot_" + stem + ".png", dpi=DPI, facecolor="white", bbox_inches="tight")
    compose("_plot_" + stem + ".png", stem + ".png", globals().get("TITLE"), subtitle, SOURCE, note)
    print("wrote", stem + ".png")

STEM = "chart-3-cumulative-koreas"
TITLE = ("Since 2000 China has grown by ten of today's Koreas, and the line is still rising")
SUBTITLE = ("China's increase in GDP since 2000 as a multiple of Korea's GDP in the same year, current "
            "US dollars, actual to 2025 and IMF projection to 2030")
NOTE = ("Each point compares China's cumulative expansion since 2000 with Korea's economy of that "
        "same year, so the measure is always a count of that year's Koreas. China's 2000 level, the "
        "starting point, is in 2000 dollars.")
keep = YEARS <= 2030
YEARS, ADD, KOR, IS_IMF = YEARS[keep], ADD[keep], KOR[keep], IS_IMF[keep]
lvl = LEVEL0 + np.cumsum(ADD)                 # China's level 2000 to 2030
k0 = lvl[YEARS == 2000][0]
cum = (lvl - k0) / KOR
pd.DataFrame({"year": YEARS, "koreas_of_same_year": np.round(cum, 2), "imf": IS_IMF}).to_csv(STEM + ".csv", index=False)

fig, ax = square_axes(figsize=(9.8, 5.9), right=0.86)
ax.fill_between(YEARS[YEARS <= 2025], cum[YEARS <= 2025], color=INK, alpha=0.08, lw=0, zorder=2)
ax.fill_between(YEARS[YEARS >= 2025], cum[YEARS >= 2025], color=RED, alpha=0.10, lw=0, zorder=2)
ax.plot(YEARS[YEARS <= 2025], cum[YEARS <= 2025], color=INK, lw=2.6, solid_capstyle="round", zorder=4)
ax.plot(YEARS[YEARS >= 2025], cum[YEARS >= 2025], color=RED, lw=2.6, ls=(0, (4, 2)), zorder=4)
for yr in [2010, 2020, 2025, 2030]:
    v = cum[YEARS == yr][0]
    col = RED if yr > 2025 else INK
    ax.plot(yr, v, marker="o", ms=10, mfc=col, mec="white", mew=1.5, ls="none", zorder=6, clip_on=False)
    if yr == 2030:
        ax.text(yr + 0.35, v, f"{v:.1f}", fontsize=EMPH_PT, color=col, ha="left", va="center",
                fontweight="bold", zorder=6, clip_on=False)
    else:
        ax.text(yr - 0.3, v + 0.5, f"{v:.1f}", fontsize=EMPH_PT, color=col, ha="right", va="bottom",
                fontweight="bold", zorder=6)
ax.text(2025.4, 0.6, "IMF projection", fontsize=LABEL_PT, color=RED, ha="left", va="center", zorder=5)
ax.axhline(0, color=GREY, lw=1.0, zorder=2)
ax.set_xlim(2000, 2030)
ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2025, 2030])
ax.set_ylim(0, 12.5)
ax.set_yticks([0, 3, 6, 9, 12])
ax.set_ylabel("Koreas of the same year", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
finish(fig, STEM, SUBTITLE, NOTE)
