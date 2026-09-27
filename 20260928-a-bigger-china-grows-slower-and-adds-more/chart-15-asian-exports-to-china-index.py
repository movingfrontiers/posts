"""chart-15-asian-exports-to-china-index.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-15-asian-exports-to-china-index.py

It writes chart-15-asian-exports-to-china-index.png and chart-15-asian-exports-to-china-index.csv into the working directory.
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

# DATA: China's imports by country of origin (= each partner's exports to China), US$ bn, monthly,
# January 2019 to August 2026. General Administration of Customs of China, via the China International
# Trade Monitor workbook (sheet M_Region).
IRAW = """\
,Japan,Korea,Taiwan,ASEAN,India,Australia
2019-01-01,13.747,14.863,14.564,22.231,1.779,10.070
2019-02-01,11.089,11.331,9.833,15.807,1.200,7.768
2019-03-01,14.084,14.773,13.579,21.648,1.479,9.075
2019-04-01,15.540,15.831,13.512,23.174,1.720,9.860
2019-05-01,13.176,14.763,14.089,22.833,1.522,9.794
2019-06-01,14.003,13.151,13.442,21.625,1.231,9.860
2019-07-01,14.595,14.476,14.832,23.869,1.450,11.616
2019-08-01,14.366,14.490,15.611,25.487,1.530,11.931
2019-09-01,15.158,14.964,15.566,27.254,1.438,11.024
2019-10-01,14.140,14.787,15.278,25.213,1.441,9.477
2019-11-01,15.295,15.233,16.731,25.939,1.534,8.690
2019-12-01,16.331,14.890,15.764,26.592,1.647,10.443
2020-01-01,10.188,12.126,11.777,21.556,1.285,11.070
2020-02-01,12.194,11.901,11.850,19.348,1.309,7.882
2020-03-01,14.758,14.511,15.125,23.917,1.390,8.932
2020-04-01,14.712,13.534,15.445,22.308,1.095,9.956
2020-05-01,12.465,12.982,14.820,21.542,1.378,8.751
2020-06-01,15.253,14.339,16.220,25.235,2.224,9.556
2020-07-01,15.334,15.173,17.294,24.131,2.423,10.783
2020-08-01,14.236,14.372,18.651,25.883,2.110,8.808
2020-09-01,17.187,17.535,21.136,30.853,2.108,9.977
2020-10-01,14.914,14.875,19.013,25.895,1.963,10.106
2020-11-01,16.386,16.137,20.366,28.345,1.675,9.514
2020-12-01,18.335,15.913,20.332,32.356,1.909,9.513
2021-01-01,15.358,15.803,18.852,29.918,2.206,10.235
2021-02-01,13.010,13.566,14.557,23.211,1.688,10.273
2021-03-01,19.245,17.811,21.261,33.097,2.647,13.159
2021-04-01,18.457,17.523,19.382,31.374,3.166,14.865
2021-05-01,16.651,17.123,19.193,33.125,2.527,13.601
2021-06-01,18.515,17.787,21.502,33.736,2.462,14.670
2021-07-01,17.293,16.910,20.888,30.811,2.668,15.226
2021-08-01,16.746,18.538,22.853,32.779,2.429,18.123
2021-09-01,18.129,19.867,23.961,36.186,2.034,15.037
2021-10-01,16.386,18.185,20.383,31.870,2.033,12.561
2021-11-01,18.738,20.748,24.661,38.468,2.374,13.065
2021-12-01,17.625,19.696,23.968,39.647,1.793,11.367
2022-01-01,16.468,19.259,22.956,34.540,1.731,12.266
2022-02-01,13.863,15.016,17.052,25.729,1.412,9.261
2022-03-01,17.364,19.017,22.231,33.990,1.722,11.174
2022-04-01,15.665,16.539,20.881,32.771,1.364,10.977
2022-05-01,14.377,16.609,19.610,32.452,1.531,12.899
2022-06-01,15.882,16.497,20.219,35.525,1.793,12.470
2022-07-01,15.707,16.764,19.694,33.762,1.567,14.007
2022-08-01,15.449,17.020,19.668,34.480,1.491,12.477
2022-09-01,16.519,18.042,21.843,37.976,1.355,11.667
2022-10-01,14.668,15.650,19.440,33.323,1.104,10.676
2022-11-01,14.153,15.370,17.419,37.039,1.186,11.762
2022-12-01,14.715,14.379,19.226,36.613,1.236,11.071
2023-01-01,10.768,11.923,13.332,27.560,1.272,12.816
2023-02-01,12.589,12.391,14.187,27.886,1.450,12.511
2023-03-01,15.231,13.883,16.909,33.253,1.931,13.716
2023-04-01,13.183,12.236,15.296,30.723,1.817,13.427
2023-05-01,12.404,12.822,15.086,31.074,1.581,13.594
2023-06-01,13.605,13.956,17.068,34.084,1.431,13.244
2023-07-01,13.405,12.907,16.872,29.990,1.413,12.487
2023-08-01,12.836,13.299,18.218,32.459,1.591,12.382
2023-09-01,14.257,15.372,18.610,35.333,1.419,12.233
2023-10-01,13.456,14.265,18.893,36.729,1.514,11.955
2023-11-01,14.114,15.017,18.425,34.670,1.599,12.773
2023-12-01,14.973,14.479,17.503,35.754,1.538,13.831
2024-01-01,11.811,14.504,16.729,31.347,2.013,14.807
2024-02-01,10.345,11.739,12.642,25.703,1.692,11.372
2024-03-01,13.942,15.047,15.366,31.970,2.015,12.952
2024-04-01,13.693,14.486,17.486,32.355,1.709,12.424
2024-05-01,12.605,15.233,17.722,32.982,1.508,12.377
2024-06-01,12.159,14.839,16.742,32.446,1.321,11.906
2024-07-01,12.742,15.617,19.302,33.327,1.365,11.658
2024-08-01,12.675,14.927,20.175,34.082,1.300,9.996
2024-09-01,13.243,15.765,20.662,36.828,1.204,10.840
2024-10-01,13.557,16.331,21.814,34.036,1.210,10.813
2024-11-01,13.763,16.086,19.251,33.618,1.353,10.969
2024-12-01,15.921,17.330,20.026,37.698,1.431,11.872
2025-01-01,9.968,13.673,17.088,28.585,1.325,10.624
2025-02-01,11.055,12.412,14.843,27.998,1.296,8.144
2025-03-01,13.515,14.774,20.667,35.092,1.604,8.709
2025-04-01,14.031,15.541,19.712,33.164,1.732,12.015
2025-05-01,12.499,14.550,19.275,31.244,1.516,11.656
2025-06-01,13.479,14.988,17.149,32.541,1.515,10.749
2025-07-01,14.925,15.697,19.390,31.406,1.705,11.268
2025-08-01,14.063,15.454,19.014,32.776,1.499,10.463
2025-09-01,16.008,17.825,22.235,36.509,1.486,12.062
2025-10-01,14.359,16.331,19.835,32.463,1.912,10.712
2025-11-01,14.700,17.087,20.256,32.096,1.917,11.382
2025-12-01,16.391,18.851,21.335,35.706,2.242,12.327
2026-01-01,14.387,18.598,20.523,33.901,2.225,13.692
2026-02-01,12.002,16.743,17.546,30.023,1.529,11.531
2026-03-01,18.272,23.455,23.641,41.235,2.041,16.336
2026-04-01,16.982,25.222,24.174,42.687,2.283,15.800
2026-05-01,16.144,26.708,23.060,40.056,2.021,14.043
2026-06-01,18.054,27.726,24.193,41.171,2.195,17.818
2026-07-01,19.294,31.046,26.481,42.715,2.672,15.411
2026-08-01,16.877,32.158,26.896,44.236,2.242,15.134
"""

STEM = "chart-15-asian-exports-to-china-index"
TITLE = "Through 2025 most of Asia sold less to China than in 2021, but 2026 has brought a rebound"
SUBTITLE = ("Exports to China by partner, twelve-month sums, index December 2021 = 100, 2019 to August "
            "2026")
SOURCE = ("General Administration of Customs of China, imports by country of origin, via the China "
          "International Trade Monitor, to August 2026.")
NOTE = "Exports to China are China's recorded imports from each partner, in current US dollars, valued cif."
m = pd.read_csv(io.StringIO(IRAW), index_col=0, parse_dates=True)
s = m.rolling(12).sum().dropna()
ix = s / s.loc["2021-12-01"] * 100
ix.round(1).to_csv(STEM + ".csv")
X = ix.index
COLS = {"Korea": RED, "ASEAN": GOLD, "Taiwan": GREEN, "Australia": GREY, "Japan": BLUE, "India": INK}
INKS = {"ASEAN": "#B8860B", "Australia": SUB_INK}

fig, ax = post_axes(right=0.86)
ax.axhline(100, color=GREY, lw=1.2, ls=(0, (4, 3)), zorder=2)
ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2025-12-01"), color=GREY, alpha=0.08, lw=0, zorder=1)
ax.text(pd.Timestamp("2023-12-15"), 134, "2022 to 2025", fontsize=LABEL_PT, color=SUB_INK, ha="center", va="center")
for c, col in COLS.items():
    ax.plot(X, ix[c], color=col, lw=2.6, zorder=4 if c != "India" else 3)
end_labels(ax, [(ix[c].iloc[-1], f"{c} {ix[c].iloc[-1]:.0f}", INKS.get(c, col)) for c, col in COLS.items()],
           X[-1] + pd.Timedelta(days=45), 6.5)
ax.set_xlim(X[0], X[-1])
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2020, 2027)])
ax.set_xticklabels([str(y) for y in range(2020, 2027)])
ax.set_ylim(55, 140)
ax.set_yticks([60, 80, 100, 120, 140])
ax.set_ylabel("index, December 2021 = 100", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.savefig("_plot_p14.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot_p14.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
