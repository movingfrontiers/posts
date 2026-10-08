"""chart-10-global-current-accounts.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-10-global-current-accounts.py

It writes chart-10-global-current-accounts.png and chart-10-global-current-accounts.csv into the working directory.
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
# POST-PACK TYPE AND AXES
# ======================================================================
GRID = "#E6E6E6"
AXIS_PT, TICK_PT, LEGEND_PT, LABEL_PT, EMPH_PT = 15, 14, 14, 14, 17
TITLE_PT, CAP_PT = TITLE_PT * 1980 / 1640, CAP_PT * 1980 / 1640

def post_axes(figsize=(9.8, 5.9), left=0.11, right=0.97, top=0.965, bottom=0.10):
    rc()
    fig, ax = plt.subplots(figsize=figsize, dpi=DPI)
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=5, width=1.0, color=GREY, direction="out")
    return fig, ax

def end_labels(ax, items, x, gap):
    """items: list of (y, text, colour). Stack labels at x without overlap."""
    order = sorted(items, key=lambda e: e[0], reverse=True)
    ys = [e[0] for e in order]
    for i in range(1, len(ys)):
        ys[i] = min(ys[i], ys[i - 1] - gap)
    for y, (_, txt, col) in zip(ys, order):
        ax.text(x, y, txt, color=col, fontsize=LABEL_PT, fontweight="bold", ha="left", va="center",
                clip_on=False, linespacing=1.05)

# DATA: IMF World Economic Outlook, April 2026 (WEO 9.0.0): current account balance (BCA, US$ bn)
# summed by group, and world GDP in current US dollars (NGDPD, US$ bn); actual to 2025, projection
# from 2026. Other East Asia is Japan, Korea, Taiwan, Singapore and Hong Kong; rest of world is every
# other economy in the WEO, and includes the global statistical discrepancy.
CRAW = """\
,china,us,other_east_asia,germany_netherlands,rest_of_world,world_gdp
2000,20.400,-401.900,167.200,-22.700,124.100,34340.700
2001,17.400,-394.100,128.800,6.400,97.400,34087.100
2002,35.400,-456.100,164.500,52.100,107.000,35167.200
2003,43.100,-522.300,220.200,67.900,160.100,39475.200
2004,68.900,-635.900,267.700,179.200,208.800,44430.300
2005,132.400,-749.200,248.600,180.300,309.700,48151.400
2006,231.800,-816.600,264.200,237.000,374.800,52185.400
2007,353.200,-736.500,331.400,277.800,140.500,58933.900
2008,420.600,-696.500,231.300,251.000,54.000,64727.500
2009,243.300,-379.700,271.900,230.600,-78.800,61316.300
2010,237.800,-432.000,356.700,254.000,-0.900,67114.700
2011,136.100,-455.300,260.300,304.900,164.000,74540.200
2012,215.400,-418.200,207.600,322.100,124.700,75990.900
2013,148.200,-339.500,225.600,325.300,202.100,78261.700
2014,236.000,-370.100,241.000,364.100,102.800,80461.000
2015,293.000,-408.500,382.200,314.800,-244.300,75935.100
2016,191.300,-396.200,437.500,372.300,-165.300,77184.800
2017,188.700,-367.600,441.200,371.700,-70.800,82081.800
2018,24.100,-439.000,398.900,424.000,80.500,87167.900
2019,102.900,-442.000,381.300,374.900,58.600,88478.300
2020,248.800,-593.500,410.000,301.900,13.100,86191.600
2021,352.900,-858.600,525.400,409.200,418.600,98435.200
2022,443.400,-993.100,348.500,231.200,454.800,102670.400
2023,263.400,-928.000,410.500,358.800,305.900,107245.600
2024,423.900,-1185.300,554.300,383.200,417.200,111598.600
2025,729.100,-1116.000,650.900,339.800,178.800,118175.500
2026,725.400,-1199.700,617.500,339.300,118.000,126295.300
2027,716.300,-1227.800,644.200,347.400,86.300,131890.700
2028,693.900,-1250.900,664.200,358.300,99.300,138128.900
2029,718.600,-1316.000,689.200,369.900,105.600,144669.100
2030,749.300,-1338.700,711.900,379.900,105.400,151388.800
2031,781.700,-1388.600,730.900,389.000,70.600,158391.700
"""

STEM = "chart-10-global-current-accounts"
TITLE = "China's surplus is one side of a global imbalance centred on the United States"
SUBTITLE = ("Current account balances, percent of world GDP, actual 2000 to 2025 and IMF projection to "
            "2031")
SOURCE = "IMF World Economic Outlook, April 2026 (BCA, NGDPD)."
NOTE = ("Other East Asia is Japan, Korea, Taiwan, Singapore and Hong Kong. Rest of world is every other "
        "economy and includes the global statistical discrepancy.")
d = pd.read_csv(io.StringIO(CRAW), index_col=0)
G = ["china", "other_east_asia", "germany_netherlands", "rest_of_world", "us"]
NAMES = {"china": "China", "other_east_asia": "other East Asia", "germany_netherlands": "Germany and\nNetherlands",
         "rest_of_world": "rest of world", "us": "United States"}
COLS = {"china": RED, "other_east_asia": GOLD, "germany_netherlands": GREEN, "rest_of_world": GREY, "us": BLUE}
p = d[G].div(d["world_gdp"], axis=0) * 100
p.round(3).to_csv(STEM + ".csv")

fig, ax = post_axes()
Y = p.index.values
pos = np.zeros(len(Y)); neg = np.zeros(len(Y))
for g in G:
    v = p[g].values
    base = np.where(v >= 0, pos, neg)
    ax.bar(Y, v, bottom=base, width=0.78, color=COLS[g], lw=0, zorder=3, alpha=0.55 if g == "rest_of_world" else 1)
    pos += np.where(v >= 0, v, 0); neg += np.where(v < 0, v, 0)
ax.axhline(0, color=INK, lw=1.0, zorder=4)
ax.axvspan(2025.5, 2031.5, color=GREY, alpha=0.08, lw=0, zorder=1)
ax.text(2025.8, 2.05, "IMF projection", fontsize=LABEL_PT, color=SUB_INK, ha="left", va="center")
handles = [matplotlib.patches.Patch(color=COLS[g], alpha=0.55 if g == "rest_of_world" else 1,
                                    label=NAMES[g].replace("\n", " ")) for g in G]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False,
          handlelength=1.2, columnspacing=1.4)
ax.set_xlim(1999.4, 2031.6)
ax.set_xticks([2001, 2006, 2011, 2016, 2021, 2026, 2031])
ax.set_ylim(-2.0, 2.2)
ax.set_yticks([-2, -1, 0, 1, 2])
ax.set_ylabel("percent of world GDP", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.savefig("_plot_p10.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot_p10.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
