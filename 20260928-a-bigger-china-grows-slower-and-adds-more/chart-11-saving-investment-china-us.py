"""chart-11-saving-investment-china-us.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-11-saving-investment-china-us.py

It writes chart-11-saving-investment-china-us.png and chart-11-saving-investment-china-us.csv into the working directory.
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

def post_axes(figsize=(9.8, 5.9), left=0.11, right=0.86, top=0.965, bottom=0.10):
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

# DATA: IMF World Economic Outlook, April 2026 (WEO 9.0.0): gross national saving (NGSD_NGDP) and
# total investment (NID_NGDP), percent of GDP, and the current account balance (BCA_NGDPD), China and
# United States; actual to 2025, projection from 2026.
SRAW = """\
,china_saving,china_investment,china_ca,us_saving,us_investment,us_ca
2000,35.400,33.730,1.670,20.740,23.680,-3.920
2001,36.910,35.620,1.290,19.580,22.180,-3.720
2002,38.530,36.150,2.380,18.300,21.720,-4.170
2003,42.060,39.500,2.560,17.350,21.750,-4.560
2004,45.230,41.740,3.480,17.660,22.650,-5.200
2005,45.730,40.040,5.690,18.050,23.380,-5.750
2006,47.900,39.610,8.280,19.130,23.540,-5.910
2007,49.910,40.130,9.770,17.350,22.560,-5.090
2008,51.120,42.090,9.030,14.980,21.040,-4.720
2009,49.740,45.040,4.700,13.800,17.770,-2.620
2010,50.380,46.500,3.870,15.290,18.670,-2.870
2011,48.340,46.560,1.780,16.240,19.030,-2.920
2012,48.250,45.770,2.480,18.290,19.950,-2.570
2013,47.250,45.740,1.510,18.480,20.380,-2.010
2014,47.400,45.200,2.210,19.570,20.900,-2.100
2015,45.230,42.640,2.590,19.610,21.420,-2.230
2016,43.840,42.170,1.670,18.470,20.890,-2.110
2017,44.180,42.670,1.510,18.880,21.160,-1.870
2018,43.600,43.430,0.170,19.130,21.570,-2.120
2019,43.340,42.630,0.700,19.330,21.670,-2.050
2020,43.920,42.270,1.650,18.230,21.440,-2.780
2021,44.650,42.710,1.940,17.580,21.410,-3.620
2022,44.790,42.380,2.420,18.190,22.030,-3.810
2023,42.560,41.130,1.430,17.030,21.570,-3.340
2024,42.840,40.610,2.240,16.490,21.530,-4.050
2025,42.520,38.800,3.720,16.800,21.360,-3.630
2026,42.310,38.830,3.480,17.700,21.400,-3.700
2027,42.090,38.820,3.270,17.860,21.490,-3.630
2028,42.270,39.290,2.980,17.790,21.350,-3.570
2029,42.510,39.590,2.910,17.550,21.160,-3.620
2030,42.500,39.620,2.880,17.410,20.960,-3.550
2031,42.460,39.610,2.840,17.230,20.780,-3.560
"""

STEM = "chart-11-saving-investment-china-us"
TITLE = "China saves more than it invests, the United States invests more than it saves"
SUBTITLE = ("Gross national saving and total investment, percent of GDP, actual 2000 to 2025 and IMF "
            "projection to 2031")
SOURCE = "IMF World Economic Outlook, April 2026 (NGSD_NGDP, NID_NGDP)."
NOTE = ("The gap between saving and investment equals the current account balance, up to the "
        "statistical discrepancy.")
d = pd.read_csv(io.StringIO(SRAW), index_col=0)
d.to_csv(STEM + ".csv")
Y = d.index.values

fig, ax = post_axes()
ax.fill_between(Y, d.china_investment, d.china_saving, where=d.china_saving >= d.china_investment,
                color=RED, alpha=0.14, lw=0, zorder=2)
ax.fill_between(Y, d.us_saving, d.us_investment, where=d.us_investment >= d.us_saving,
                color=BLUE, alpha=0.14, lw=0, zorder=2)
for col, colour, ls in [("china_saving", RED, "-"), ("china_investment", RED, (0, (4, 2))),
                        ("us_saving", BLUE, "-"), ("us_investment", BLUE, (0, (4, 2)))]:
    ax.plot(Y, d[col], color=colour, lw=2.6, ls=ls, solid_capstyle="round", zorder=4)
ax.axvspan(2025.5, 2031, color=GREY, alpha=0.08, lw=0, zorder=1)
ax.text(2025.8, 55.5, "IMF projection", fontsize=LABEL_PT, color=SUB_INK, ha="left", va="center")
end_labels(ax, [(d.china_saving.iloc[-1], "China, saving", RED), (d.china_investment.iloc[-1], "China,\ninvestment", RED),
                (d.us_investment.iloc[-1], "US,\ninvestment", BLUE), (d.us_saving.iloc[-1], "US, saving", BLUE)], 2031.6, 4.5)
ax.text(2014.5, 50.8, "China's surplus", fontsize=LABEL_PT, color=RED, ha="center", va="center")
ax.text(2016.0, 14.6, "US deficit", fontsize=LABEL_PT, color=BLUE, ha="center", va="center")
ax.set_xlim(2000, 2031)
ax.set_xticks([2001, 2006, 2011, 2016, 2021, 2026, 2031])
ax.set_ylim(10, 57)
ax.set_yticks([10, 20, 30, 40, 50])
ax.set_ylabel("percent of GDP", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.savefig("_plot_p11.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot_p11.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
