"""chart-2-gdp-per-capita-relative-to-frontier.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-2-gdp-per-capita-relative-to-frontier.py

It writes chart-2-gdp-per-capita-relative-to-frontier.png and
chart-2-gdp-per-capita-relative-to-frontier.csv into the working directory.
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
# Maddison Project Database 2023 regional aggregates, real GDP per capita in
# constant 2011 international dollars, as exported by Our World in Data.
# ======================================================================

RAW = """\
Year,Western offshoots,Western Europe,East Asia,Eastern Europe,Middle East and North Africa,Latin America,South and South East Asia,Sub Saharan Africa
1820,2513.0454,2170.7048,911.1599,1044.5385,885.8996,956.9071,919.2012,1188.0
1830,2886.7632,2314.693,846.0,,,925.0,934.8959,
1840,3167.8643,2528.1648,849.0,,,1081.0,938.7899,
1850,3474.4102,2670.193,899.6576,1290.5618,,1067.8584,926.9601,
1860,4214.441,3028.8774,,,,1588.0,888.649,
1870,4647.454,3287.7605,993.6216,1518.355,1085.2244,1292.8846,850.245,1286.0
1880,6019.124,3584.9082,,,,1441.5989,1062.8734,
1890,6480.9556,4079.0337,1048.869,1582.6404,,1672.813,957.0396,
1900,7740.8506,4724.0073,1086.2826,2015.9938,,1713.7573,997.5472,
1910,9354.691,5121.3467,1056.0726,2240.678,,2189.3704,1144.2612,1687.8292
1920,9741.423,4869.033,1215.6156,1374.9872,,2332.3687,1117.5267,
1930,10297.123,6389.672,1296.0483,2506.88,1600.0,2687.6016,1308.0571,
1940,11620.501,7160.773,1496.2766,3216.907,2146.0,2984.4153,1261.4373,
1950,14773.206,7239.914,1109.4408,4133.084,2287.5552,3678.346,1069.7146,1326.6232
1960,17471.514,10928.713,1725.5217,5865.5776,3102.628,4698.2524,1294.9343,1578.2007
1970,23209.65,16096.743,3030.772,8330.067,4790.016,6193.1772,1545.8779,1968.3627
1980,28786.756,20870.26,4191.3184,9783.951,6731.1772,8611.507,1897.4258,2036.6299
1990,35619.383,25367.219,6089.8413,10091.273,6431.515,8054.83,2573.6833,1812.6813
2000,44321.316,32593.166,8152.877,8833.693,9658.656,10132.75,3427.3994,2009.1904
2010,48083.18,37420.33,12862.345,16320.271,16565.371,13356.442,5364.828,3204.6519
2015,51453.055,38740.285,16298.285,18062.734,18401.537,14328.678,6704.329,3523.8147
2016,51890.56,39299.83,17048.79,18301.775,18831.977,14074.377,7084.0864,3477.2732
2017,52692.227,40116.637,17909.393,18917.457,19067.09,14102.67,7407.7363,3474.0273
2018,53866.645,40640.984,18785.072,19560.426,19221.93,14103.097,7778.0244,3480.8083
2019,54730.81,41090.758,19580.744,20051.041,19088.29,13957.887,8027.9653,3488.1553
2020,52617.65,38162.535,19749.514,19578.574,18227.408,12865.496,7590.1543,3335.987
2021,55576.02,40164.14,21157.305,20696.99,19162.693,13610.789,7983.717,3398.5784
2022,56567.887,41323.023,21728.52,20656.266,19874.799,14028.038,8377.074,3436.5957
"""

STEM = "chart-2-gdp-per-capita-relative-to-frontier"
FRONTIER = "Western offshoots"

levels = pd.read_csv(io.StringIO(RAW), index_col="Year")
rel = levels.div(levels[FRONTIER], axis=0) * 100

# tidy long file alongside the chart
tidy = (levels.stack().rename("gdp_per_capita_2011_intl_usd").to_frame()
        .join(rel.stack().rename("pct_of_western_offshoots").to_frame()))
tidy.index.names = ["year", "region"]
tidy.round(4).to_csv(STEM + ".csv")

# ======================================================================
# CHART
# ======================================================================

BAND = "#F4F4F4"          # the sub-40 per cent band

# Seven series is more than the house palette carries, so the four house colours are
# joined by a light blue, a purple and near black. Hues are spread as far apart as the
# set allows, since six of the seven run together inside the band.
SERIES = [
    ("Western Europe",               BLUE),        # #283593
    ("East Asia",                    RED),         # #C62828
    ("South and South East Asia",    GOLD),        # #F9A825
    ("Latin America",                GREEN),       # #00897B
    ("Eastern Europe",               "#0288D1"),
    ("Middle East and North Africa", "#6A4C93"),
    ("Sub Saharan Africa",           "#1A1A1A"),
]
LW = 2.4

THRESHOLD = 40
X_END = 2022
LABEL_X = 2028
MIN_SEP = 3.4             # least vertical room between two end labels, in points of the y scale

TITLE = ("90% of the global population live in regions below 40% of frontier "
         "per capita income")
SUBTITLE = ("GDP per capita as percent of Western offshoots "
            "(US, Canada, Australia and New Zealand)")
SOURCE = "Bolt and van Zanden, Maddison Project Database 2023."
NOTE = ("Regional aggregates are those published in the database. GDP per capita is measured in "
        "constant 2011 international dollars. Observations are decadal to 2010 and annual from 2015, and "
        "several regions have no reading for parts of the nineteenth and early twentieth "
        "centuries, so the lines run straight across those gaps. The share in the title refers "
        "to 2022, when Western Europe is the only region above the 40 percent line: it and the "
        "Western offshoots together hold roughly a tenth of the world's people, which leaves about "
        "90 percent living in regions below the line.")


def declutter(points, min_sep):
    """Nudge crowded end labels apart, downwards only. Pushing the top label of a
    cluster up would carry it across the 40 per cent line the chart is about."""
    order = sorted(points, key=lambda t: t[0], reverse=True)
    ys = [y for y, _ in order]
    for i in range(1, len(ys)):
        ys[i] = min(ys[i], ys[i - 1] - min_sep)
    return [(y, lab) for y, (_, lab) in zip(ys, order)]


rc()
fig, ax = plt.subplots(figsize=(10.6, 6.5), dpi=DPI)
fig.subplots_adjust(left=0.045, right=0.735, top=0.965, bottom=0.09)

ax.axhspan(0, THRESHOLD, color=BAND, zorder=0)
ax.axhline(THRESHOLD, color=GREY, lw=1.0, ls=(0, (4, 3)), zorder=1)
ends = []
for name, colour in SERIES:
    s = rel[name].dropna()
    ax.plot(s.index, s.values, color=colour, lw=LW, solid_capstyle="round", zorder=3)
    ends.append((s.values[-1], (name, colour)))

for y, (name, colour) in declutter(ends, MIN_SEP):
    ax.text(LABEL_X, y, name, color=colour, fontsize=LABEL_PT, va="center", ha="left",
            fontweight="bold")

ax.set_xlim(1820, X_END)
ax.set_ylim(0, 90)
ax.set_xticks([1820, 1850, 1900, 1950, 2000, X_END])
ax.set_yticks([0, 20, 40, 60, 80])
ax.set_yticklabels(["0", "20", "40", "60", "80"])
ax.get_yticklabels()[2].set_fontweight("bold")
style_ax(ax)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E6E6E6", lw=0.8)

for t in ax.texts:
    t.set_clip_on(False)

fig.savefig("_plot.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
