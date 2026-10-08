"""chart-4-share-of-world-gdp.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-4-share-of-world-gdp.py

It writes chart-4-share-of-world-gdp.png and chart-4-share-of-world-gdp.csv into the working directory.
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
# IMF World Economic Outlook, April 2026: world and China GDP in current US dollars (NGDPD),
# 1999 to 2031; actual to 2025, projection from 2026.
# ======================================================================

WRAW = """\
year,world_usd_bn,china_usd_bn
1999,33174.9,1101.1
2000,34340.7,1220.3
2001,34087.1,1351.4
2002,35167.2,1486.6
2003,39475.2,1680.9
2004,44430.3,1979.0
2005,48151.4,2326.6
2006,52185.4,2798.8
2007,58933.9,3613.6
2008,64727.5,4655.6
2009,61316.3,5176.5
2010,67114.7,6138.9
2011,74540.2,7628.4
2012,75990.9,8682.5
2013,78261.7,9787.5
2014,80461.0,10702.5
2015,75935.1,11305.6
2016,77184.8,11452.0
2017,82081.8,12516.2
2018,87167.9,14107.9
2019,88478.3,14593.5
2020,86191.6,15110.2
2021,98435.2,18183.5
2022,102670.4,18337.8
2023,107245.6,18366.9
2024,111598.6,18945.1
2025,118175.5,19626.2
2026,126295.3,20851.6
2027,131890.7,21929.0
2028,138128.9,23260.0
2029,144669.1,24662.8
2030,151388.8,26046.8
"""
w = pd.read_csv(io.StringIO(WRAW)).set_index("year")
GRID = "#E6E6E6"
AXIS_PT, TICK_PT, LEGEND_PT, LABEL_PT, EMPH_PT = 15, 14, 14, 14, 17
TITLE_PT, CAP_PT = TITLE_PT * 1980 / 1640, CAP_PT * 1980 / 1640

STEM = "chart-4-share-of-world-gdp"
TITLE = ("Every five years, China has been adding 4 to 7 percent of world GDP to the global economy")
SUBTITLE = ("China's increase in GDP over each five-year period as a share of world GDP in the period's "
            "final year, current US dollars, actual to 2025 and IMF projection to 2030, percent")
SOURCE = ("IMF World Economic Outlook, April 2026 (NGDPD, China and world).")
NOTE = ("Both numerator and denominator are valued in the final year's dollars, apart from China's "
        "starting level, which is in the dollars of the year before the period. One full square is one "
        "percent of world GDP; a partial square is a fraction of one.")
PER = [(2001, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2025), (2026, 2030)]
vals, share, labs = [], [], []
for a, b in PER:
    inc = w.loc[b, "china_usd_bn"] - w.loc[a - 1, "china_usd_bn"]
    vals.append(inc / w.loc[b, "world_usd_bn"] * 100)
    share.append(inc / (w.loc[b, "world_usd_bn"] - w.loc[a - 1, "world_usd_bn"]) * 100)
    labs.append(f"{a} to {b}")
pd.DataFrame({"period": labs, "china_increase_pct_of_world_gdp_final_year": np.round(vals, 2),
              "china_share_of_world_increase_pct": np.round(share, 1)}).to_csv(STEM + ".csv", index=False)

rc()
fig, ax = plt.subplots(figsize=(9.8, 5.35), dpi=DPI)
fig.subplots_adjust(left=0.20, right=0.985, top=0.97, bottom=0.03)
import matplotlib.patches as mpatches
S, G, RS = 0.60, 0.12, 0.72          # square side, gap, row spacing (data units; the figure is sized so units are square)
for i, (v, lab) in enumerate(zip(vals, labs)):
    y = (len(vals) - 1 - i) * RS
    colour = RED if lab.startswith("2026") else INK
    full, frac = int(v), v - int(v)
    for k in range(full):
        ax.add_patch(mpatches.FancyBboxPatch((k * (S + G), y - S / 2), S, S, boxstyle="round,pad=0,rounding_size=0.08",
                                             color=colour, lw=0, zorder=3))
    if frac > 0.02:
        ax.add_patch(mpatches.FancyBboxPatch((full * (S + G), y - S / 2), S, S, boxstyle="round,pad=0,rounding_size=0.08",
                                             facecolor="white", edgecolor=colour, lw=1.4, zorder=3))
        ax.add_patch(mpatches.Rectangle((full * (S + G), y - S / 2), S * frac, S, color=colour, lw=0, zorder=4))
    ax.text((full + (1 if frac > 0.02 else 0)) * (S + G) + 0.1, y, f"{v:.1f}%", fontsize=EMPH_PT,
            color=colour, ha="left", va="center", fontweight="bold", zorder=5)
ax.set_yticks([k * RS for k in range(len(vals))])
ax.set_yticklabels(labs[::-1])
ax.set_xlim(-0.1, 7.7)
ax.set_ylim(-0.5, (len(vals) - 1) * RS + 0.9)
ax.axhline(-0.5, color=GREY, lw=1.0, zorder=2)          # baseline spanning the full width, so both block charts share one canvas
ax.set_xticks([])
ax.text(0, (len(vals) - 1) * RS + 0.42, "percent of world GDP, measured in the final year", fontsize=LABEL_PT,
        color=SUB_INK, ha="left", va="bottom")
ax.set_axisbelow(True)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)

fig.savefig("_plot17k.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot17k.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
