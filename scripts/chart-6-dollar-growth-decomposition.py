"""chart-6-dollar-growth-decomposition.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-6-dollar-growth-decomposition.py

It writes chart-6-dollar-growth-decomposition.png and chart-6-dollar-growth-decomposition.csv into the working directory.
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
# China, 1990 to 2025, from the World Bank WDI extract of 13 July 2026: real GDP
# growth (NY.GDP.MKTP.KD.ZG), population growth (SP.POP.GROW), the GDP deflator
# (NY.GDP.DEFL.KD.ZG), the period-average exchange rate (PA.NUS.FCRF), GNI per
# capita, Atlas method (NY.GNP.PCAP.CD), GDP in current US dollars (NY.GDP.MKTP.CD,
# billions), GDP and GNI in current yuan (NY.GDP.MKTP.CN, NY.GNP.MKTP.CN, billions)
# and GDP per capita in current yuan (NY.GDP.PCAP.CN). The threshold column is the World Bank high-income
# line applied to that data year, from the historical classification table; the
# 2025 line (14,375 dollars) is the July 2026 classification.
# ======================================================================

import io
import pandas as pd

RAW = """\
year,real_gdp_growth,pop_growth,deflator,cny_per_usd,atlas_gni_pc,gdp_usd_bn,gdp_lcu_bn,gni_lcu_bn,gdp_pc_lcu,hi_threshold
1990,3.923,1.467,5.728,4.7832,330,361.6,1891.0,1896.0,1666,7620
1991,9.376,1.364,6.713,5.3234,360,384.5,2207.1,2211.6,1918,7910
1992,14.298,1.226,8.202,5.5146,400,428.5,2729.6,2730.9,2343,8355
1993,13.926,1.150,15.188,5.7620,420,446.6,3582.0,3574.6,3040,8625
1994,13.083,1.130,20.630,8.6187,470,566.9,4886.2,4877.3,4100,8955
1995,11.015,1.087,13.651,8.3514,540,738.2,6164.9,6066.6,5117,9385
1996,9.973,1.048,6.509,8.3142,660,868.5,7221.1,7117.6,5931,9635
1997,9.298,1.023,1.648,8.2898,760,967.8,8022.5,7931.3,6522,9655
1998,7.924,0.960,-0.829,8.2790,800,1037.1,8586.4,8448.6,6914,9360
1999,7.741,0.866,-1.224,8.2782,860,1103.8,9137.9,9018.1,7294,9265
2000,8.574,0.788,2.112,8.2785,950,1223.8,10130.9,10009.5,8024,9265
2001,8.324,0.726,2.201,8.2771,1020,1355.0,11215.7,11057.0,8818,9205
2002,9.236,0.670,0.649,8.2770,1130,1489.8,12331.2,12207.5,9631,9075
2003,10.114,0.623,2.647,8.2770,1300,1683.9,13937.7,13853.1,10818,9385
2004,10.140,0.594,6.981,8.2768,1530,1984.2,16422.8,16380.3,12671,10065
2005,11.454,0.588,3.753,8.1943,1790,2317.6,18990.8,18858.8,14567,10725
2006,12.675,0.558,4.019,7.9734,2090,2791.5,22257.8,22216.8,16977,11115
2007,14.151,0.522,7.913,7.6075,2550,3604.1,27418.0,27479.1,20805,11455
2008,9.669,0.512,7.858,6.9487,3140,4667.3,32431.8,32630.3,24483,11905
2009,9.406,0.497,-0.085,6.8314,3740,5189.6,35452.2,35393.9,26631,12195
2010,10.592,0.483,6.933,6.7703,4410,6192.6,41925.3,41748.8,31341,12275
2011,9.462,0.546,8.015,6.4615,5130,7671.8,49570.8,49116.0,36855,12475
2012,7.858,0.678,2.404,6.3123,6010,8673.7,54751.1,54626.0,40431,12615
2013,7.778,0.666,2.298,6.1958,6860,9743.1,60366.0,59883.8,44281,12745
2014,7.461,0.630,1.092,6.1434,7600,10674.5,65578.3,65660.0,47802,12735
2015,6.982,0.581,0.135,6.2275,8040,11280.8,70251.1,69922.4,50912,12475
2016,6.774,0.573,1.479,6.6445,8360,11456.0,76119.3,75749.2,54849,12235
2017,6.891,0.605,4.146,6.7588,8830,12537.6,84738.3,84629.3,60691,12055
2018,6.758,0.468,3.467,6.6160,9720,14147.8,93601.0,93197.2,66726,12375
2019,6.067,0.355,1.317,6.9084,10510,14560.2,100587.2,100310.8,71453,12535
2020,2.340,0.238,0.531,6.9008,10740,14996.4,103486.8,102675.2,73338,12695
2021,8.570,0.089,4.474,6.4490,12220,18201.7,117382.3,116581.7,83111,13205
2022,3.134,-0.013,1.935,6.7372,13170,18316.8,123402.9,122370.7,87385,13845
2023,5.416,-0.104,-0.507,7.0840,13750,18270.4,129427.2,128477.4,91746,14005
2024,4.958,-0.123,-0.764,7.1975,13660,18729.7,134806.6,133879.7,95677,13935
2025,4.960,-0.170,-0.922,7.1898,14230,19498.0,140187.9,139370.0,99665,14375
"""

df = pd.read_csv(io.StringIO(RAW))
# real GDP per capita growth, exact rather than the difference of the two rates
df["real_pc_growth"] = ((1 + df["real_gdp_growth"] / 100) / (1 + df["pop_growth"] / 100) - 1) * 100
# renminbi against the dollar, percent a year, appreciation positive
df["rmb_change"] = (df["cny_per_usd"].shift(1) / df["cny_per_usd"] - 1) * 100
# Atlas GNI per capita, percent a year
df["atlas_growth"] = (df["atlas_gni_pc"] / df["atlas_gni_pc"].shift(1) - 1) * 100
# GDP in current US dollars, percent a year, from its three parts
df["usd_gdp_growth"] = ((1 + df["real_gdp_growth"] / 100) * (1 + df["deflator"] / 100)
                        * (1 + df["rmb_change"] / 100) - 1) * 100
# nominal per capita series in yuan, and their growth rates
df["population_m"] = df["gdp_lcu_bn"] * 1e3 / df["gdp_pc_lcu"]
df["gni_pc_lcu"] = df["gni_lcu_bn"] * 1e3 / df["population_m"]
df["nom_gdp_pc_growth"] = (df["gdp_pc_lcu"] / df["gdp_pc_lcu"].shift(1) - 1) * 100
df["nom_gni_pc_growth"] = (df["gni_pc_lcu"] / df["gni_pc_lcu"].shift(1) - 1) * 100

# ======================================================================
# CHART
# ======================================================================

STEM = "chart-6-dollar-growth-decomposition"

# post-pack type: base 15, ticks 14, in-plot labels 14; title and caption raised to land at the
# house pixel sizes on this canvas width
AXIS_PT, TICK_PT, LEGEND_PT, LABEL_PT, EMPH_PT = 15, 14, 14, 14, 17
TITLE_PT, CAP_PT = TITLE_PT * 1980 / 1640, CAP_PT * 1980 / 1640
GRID = "#E6E6E6"

TITLE = ("Prices and the currency added nine points to China's dollar growth in the late 2000s "
         "and took three away after 2022")
SUBTITLE = ("Average annual growth of China's GDP in current US dollars, split into real growth, "
            "the GDP deflator and the renminbi against the dollar, by period, percent")
SOURCE = ("World Bank World Development Indicators, 13 July 2026 (NY.GDP.MKTP.KD.ZG, "
          "NY.GDP.DEFL.KD.ZG, PA.NUS.FCRF).")
NOTE = ("Growth rates are log changes, so the three parts sum exactly to the dollar total shown by "
        "the marker. The exchange rate part is the change in the period-average renminbi per dollar, "
        "appreciation positive. Periods start in 1996, after the 1994 unification of the exchange rate; "
        "the last five years are split at 2022.")

PERIODS = [(1996, 2000), (2001, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2022),
           (2023, 2025)]
PARTS = [("real_gdp_growth", "real GDP growth", BLUE),
         ("deflator", "GDP deflator", GOLD),
         ("rmb_change", "renminbi vs dollar", GREEN)]

rows = []
for a, b in PERIODS:
    d = df[(df["year"] >= a) & (df["year"] <= b)]
    r = {"period": f"{a}-{b}"}
    for col, _, _ in PARTS:
        r[col] = (100 * np.log1p(d[col] / 100)).mean()
    r["usd_total"] = sum(r[col] for col, _, _ in PARTS)
    rows.append(r)
tab = pd.DataFrame(rows)
tab.round(2).to_csv(STEM + ".csv", index=False)

rc()
fig, ax = plt.subplots(figsize=(8.9, 6.0), dpi=DPI)
fig.subplots_adjust(left=0.072, right=0.985, top=0.965, bottom=0.11)

x = np.arange(len(tab))
pos = np.zeros(len(tab)); neg = np.zeros(len(tab))
for col, name, colour in PARTS:
    v = tab[col].values
    base = np.where(v >= 0, pos, neg)
    ax.bar(x, v, bottom=base, width=0.62, color=colour, label=name, zorder=3, lw=0)
    pos = pos + np.where(v >= 0, v, 0); neg = neg + np.where(v < 0, v, 0)
ax.scatter(x, tab["usd_total"], marker="D", s=46, color="white", edgecolor=INK, lw=1.4,
           zorder=6, label="GDP in US dollars")
for i, t in enumerate(tab["usd_total"]):
    top = max(t, pos[i]) if t >= 0 else t
    ax.text(x[i], top + 0.6, f"{t:.1f}", fontsize=LABEL_PT, fontweight="bold", color=INK,
            va="bottom", ha="center", zorder=7)
# value labels inside the larger segments
for col, name, colour in PARTS:
    v = tab[col].values
    cum_pos = np.zeros(len(tab)); cum_neg = np.zeros(len(tab))
    for c2, _, _ in PARTS:
        if c2 == col:
            break
        w = tab[c2].values
        cum_pos += np.where(w >= 0, w, 0); cum_neg += np.where(w < 0, w, 0)
    for i, val in enumerate(v):
        if abs(val) >= 1.6:
            y0 = cum_pos[i] if val >= 0 else cum_neg[i]
            yl = y0 + val / 2
            if col == "real_gdp_growth" and abs(yl - tab["usd_total"].iloc[i]) < 1.3:   # clear of the marker
                yl += 1.5
            ax.text(x[i], yl, f"{val:+.1f}" if col != "real_gdp_growth" else f"{val:.1f}",
                    fontsize=LABEL_PT, color="white", ha="center", va="center", zorder=5,
                    fontweight="bold")

ax.axhline(0, color=GREY, lw=1.0, zorder=2)
ax.set_xticks(x)
ax.set_xticklabels([p.replace("-", " to\n") for p in tab["period"]])
ax.set_xlim(-0.6, len(tab) - 0.2)
ax.set_ylim(-6, 24)
ax.set_yticks([-5, 0, 5, 10, 15, 20])
ax.set_ylabel("percent a year", labelpad=8)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, lw=0.8)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False, handlelength=1.2,
          columnspacing=1.4)

fig.savefig("_plot15.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot15.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
