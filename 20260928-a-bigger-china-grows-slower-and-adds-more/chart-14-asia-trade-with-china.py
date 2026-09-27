"""chart-14-asia-trade-with-china.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-14-asia-trade-with-china.py

It writes chart-14-asia-trade-with-china.png and chart-14-asia-trade-with-china.csv into the working directory.
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

# DATA: China's merchandise exports to and imports from Japan, Korea, Taiwan, ASEAN, India and
# Australia combined, US$ bn, monthly, January 2012 to August 2026. General Administration of Customs
# of China, via the China International Trade Monitor workbook (sheet M_Region). China's imports from a
# partner are that partner's exports to China, valued cif.
MRAW = """\
,china_exports_to_partners,china_imports_from_partners
2012-01-01,42.063,50.126
2012-02-01,34.469,62.297
2012-03-01,48.222,68.845
2012-04-01,45.504,61.455
2012-05-01,49.771,66.984
2012-06-01,47.718,63.220
2012-07-01,46.622,65.423
2012-08-01,45.939,67.098
2012-09-01,51.783,71.270
2012-10-01,50.025,62.266
2012-11-01,51.421,68.011
2012-12-01,52.739,70.845
2013-01-01,51.648,65.907
2013-02-01,36.953,51.514
2013-03-01,49.418,75.216
2013-04-01,53.219,71.901
2013-05-01,51.867,67.389
2013-06-01,49.398,60.987
2013-07-01,50.805,70.268
2013-08-01,52.455,67.040
2013-09-01,52.499,72.165
2013-10-01,53.245,65.940
2013-11-01,55.709,71.906
2013-12-01,55.228,76.660
2014-01-01,59.984,71.811
2014-02-01,32.392,55.330
2014-03-01,52.613,68.481
2014-04-01,55.411,70.655
2014-05-01,55.939,65.846
2014-06-01,52.279,66.018
2014-07-01,57.877,69.823
2014-08-01,56.337,66.662
2014-09-01,57.096,82.811
2014-10-01,58.529,70.798
2014-11-01,60.606,65.826
2014-12-01,62.551,74.923
2015-01-01,60.093,60.034
2015-02-01,49.678,48.297
2015-03-01,46.594,62.767
2015-04-01,51.992,62.290
2015-05-01,54.357,57.627
2015-06-01,54.656,63.664
2015-07-01,55.600,65.788
2015-08-01,54.040,59.232
2015-09-01,58.260,64.382
2015-10-01,55.813,59.254
2015-11-01,58.412,64.302
2015-12-01,60.646,70.445
2016-01-01,52.868,50.691
2016-02-01,37.312,42.126
2016-03-01,51.715,58.446
2016-04-01,51.265,57.081
2016-05-01,53.907,57.681
2016-06-01,51.957,59.651
2016-07-01,52.075,58.270
2016-08-01,53.429,63.647
2016-09-01,53.650,66.613
2016-10-01,52.721,62.065
2016-11-01,57.660,69.567
2016-12-01,59.797,76.871
2017-01-01,54.948,59.150
2017-02-01,37.410,59.721
2017-03-01,58.129,69.333
2017-04-01,55.295,64.931
2017-05-01,56.778,65.539
2017-06-01,55.055,69.730
2017-07-01,54.772,66.400
2017-08-01,56.575,72.396
2017-09-01,58.212,80.287
2017-10-01,57.016,73.054
2017-11-01,67.062,83.587
2017-12-01,65.977,81.680
2018-01-01,61.412,80.024
2018-02-01,49.696,61.218
2018-03-01,57.627,80.664
2018-04-01,63.747,77.010
2018-05-01,65.212,82.119
2018-06-01,62.729,78.371
2018-07-01,62.372,85.359
2018-08-01,61.949,83.412
2018-09-01,65.564,90.151
2018-10-01,64.492,84.112
2018-11-01,69.509,80.936
2018-12-01,67.883,70.573
2019-01-01,68.241,77.253
2019-02-01,43.355,57.028
2019-03-01,67.536,74.638
2019-04-01,60.296,79.637
2019-05-01,66.745,76.178
2019-06-01,66.385,73.312
2019-07-01,68.126,80.838
2019-08-01,65.447,83.415
2019-09-01,67.587,85.404
2019-10-01,68.553,80.337
2019-11-01,73.612,83.422
2019-12-01,76.717,85.667
2020-01-01,66.239,68.001
2020-02-01,31.185,64.485
2020-03-01,69.543,78.633
2020-04-01,65.453,77.051
2020-05-01,63.785,71.939
2020-06-01,64.344,82.826
2020-07-01,71.593,85.138
2020-08-01,70.500,84.061
2020-09-01,73.667,98.796
2020-10-01,73.864,86.767
2020-11-01,81.903,92.423
2020-12-01,89.201,98.357
2021-01-01,84.866,92.372
2021-02-01,62.577,76.304
2021-03-01,80.436,107.221
2021-04-01,87.072,104.767
2021-05-01,83.949,102.221
2021-06-01,85.404,108.671
2021-07-01,84.991,103.796
2021-08-01,87.748,111.467
2021-09-01,89.949,115.213
2021-10-01,90.909,101.417
2021-11-01,101.294,118.054
2021-12-01,103.352,114.096
2022-01-01,104.013,107.219
2022-02-01,65.175,82.333
2022-03-01,92.977,105.498
2022-04-01,91.887,98.198
2022-05-01,102.886,97.477
2022-06-01,108.285,102.386
2022-07-01,108.979,101.500
2022-08-01,101.583,100.586
2022-09-01,106.920,107.401
2022-10-01,100.073,94.861
2022-11-01,100.043,96.929
2022-12-01,104.486,97.241
2023-01-01,94.465,77.670
2023-02-01,78.757,81.013
2023-03-01,109.073,94.923
2023-04-01,95.563,86.683
2023-05-01,86.588,86.561
2023-06-01,89.562,93.388
2023-07-01,87.924,87.074
2023-08-01,88.827,90.785
2023-09-01,95.255,97.224
2023-10-01,88.297,96.811
2023-11-01,95.119,96.599
2023-12-01,99.263,98.078
2024-01-01,100.174,91.210
2024-02-01,68.322,73.494
2024-03-01,99.545,91.291
2024-04-01,96.227,92.153
2024-05-01,97.883,92.426
2024-06-01,98.683,89.412
2024-07-01,94.354,94.011
2024-08-01,94.735,93.154
2024-09-01,93.841,98.543
2024-10-01,96.992,97.761
2024-11-01,103.246,95.041
2024-12-01,108.795,104.279
2025-01-01,102.367,81.263
2025-02-01,72.018,75.749
2025-03-01,108.972,94.360
2025-04-01,110.826,96.194
2025-05-01,108.460,90.740
2025-06-01,108.180,90.420
2025-07-01,106.206,94.391
2025-08-01,108.625,93.269
2025-09-01,104.962,106.125
2025-10-01,101.505,95.611
2025-11-01,112.428,97.439
2025-12-01,119.830,106.852
2026-01-01,119.208,103.324
2026-02-01,98.608,89.374
2026-03-01,120.419,124.980
2026-04-01,128.197,127.148
2026-05-01,135.203,122.032
2026-06-01,143.695,131.156
2026-07-01,139.372,137.620
2026-08-01,139.089,137.542
"""

STEM = "chart-14-asia-trade-with-china"
TITLE = "Asia used to sell more to China than it bought from it, but since 2023 the balance has reversed"
SUBTITLE = ("China's trade with Japan, Korea, Taiwan, ASEAN, India and Australia combined, twelve-month "
            "sums, US$ billions, 2012 to August 2026")
SOURCE = ("General Administration of Customs of China, trade by partner, via the China International "
          "Trade Monitor, to August 2026.")
NOTE = "Asia's exports to China are China's recorded imports from these partners, valued cif."
m = pd.read_csv(io.StringIO(MRAW), index_col=0, parse_dates=True)
s = m.rolling(12).sum().dropna()
s.round(1).to_csv(STEM + ".csv")
X = s.index
a, b = s.china_imports_from_partners.values, s.china_exports_to_partners.values

fig, ax = post_axes(right=0.84)
ax.fill_between(X, b, a, where=a >= b, color=GOLD, alpha=0.25, lw=0, zorder=2, interpolate=True)
ax.fill_between(X, b, a, where=a < b, color=RED, alpha=0.18, lw=0, zorder=2, interpolate=True)
ax.plot(X, a, color=BLUE, lw=2.8, zorder=4)
ax.plot(X, b, color=RED, lw=2.8, zorder=4)
end_labels(ax, [(a[-1], "Asia's exports\nto China", BLUE), (b[-1], "China's exports\nto Asia", RED)],
           X[-1] + pd.Timedelta(days=60), 110)
ax.text(pd.Timestamp("2015-06-01"), 870, "Asia in surplus\nwith China", fontsize=LABEL_PT, color="#B8860B",
        ha="center", va="center", linespacing=1.1)
ax.text(pd.Timestamp("2024-06-01"), 1300, "China in surplus", fontsize=LABEL_PT, color=RED, ha="center", va="center")
for d, col, v, dy in [("2022-06-01", BLUE, None, 60), ("2025-12-01", BLUE, None, -70)]:
    pt = pd.Timestamp(d); v = s.loc[pt, "china_imports_from_partners"]
    ax.plot(pt, v, marker="o", ms=10, mfc=col, mec="white", mew=1.5, ls="none", zorder=6)
    ax.text(pt, v + dy, f"{v:,.0f}", fontsize=EMPH_PT, color=col, fontweight="bold", ha="center",
            va="bottom" if dy > 0 else "top", zorder=6)
ax.set_xlim(X[0], X[-1])
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in (2014, 2016, 2018, 2020, 2022, 2024, 2026)])
ax.set_xticklabels(["2014", "2016", "2018", "2020", "2022", "2024", "2026"])
ax.set_ylim(400, 1600)
ax.set_yticks([400, 800, 1200, 1600])
ax.set_yticklabels(["400", "800", "1,200", "1,600"])
ax.set_ylabel("US$ billions, twelve-month sum", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.savefig("_plot_p13.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot_p13.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
