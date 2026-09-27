"""chart-13-capital-per-worker.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-13-capital-per-worker.py

It writes chart-13-capital-per-worker.png and chart-13-capital-per-worker.csv into the working directory.
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

# DATA: Penn World Table 11.0 (Feenstra, Inklaar and Timmer), via FRED: capital stock at constant
# national prices in millions of 2021 US dollars (rkna; RKNANPCNA666NRUG, RKNANPUSA666NRUG) and number
# of persons engaged in millions (emp; EMPENGCNA148NRUG, EMPENGUSA148NRUG), China and United States,
# 1980 to 2023. Capital per worker is capital stock divided by persons engaged.
KRAW = """\
year,china_capital_musd,us_capital_musd,china_workers_m,us_workers_m
1980,2626428.750,29506590,476.466,103.470
1981,2820224.500,30360724,496.539,104.698
1982,3040363.750,31041684,522.161,103.980
1983,3285501.750,31824032,536.208,105.435
1984,3572324.500,32878966,550.420,109.862
1985,3923363.750,34021900,564.916,112.191
1986,4299320.000,35158052,577.688,114.730
1987,4697350.500,36259956,588.970,117.664
1988,5153502.000,37347072,605.541,120.204
1989,5487767.000,38436032,627.566,122.550
1990,5772352.500,39439352,647.400,123.910
1991,6129512.000,40251216,662.984,122.740
1992,6667980.000,41116496,670.216,123.288
1993,7461987.500,42057968,676.428,124.846
1994,8335410.000,43102436,682.057,127.499
1995,9279385.000,44213800,687.490,129.188
1996,10315911.000,45461520,693.968,130.842
1997,11413979.000,46823444,701.587,133.489
1998,12711590.000,48363724,709.159,135.238
1999,14058341.000,50045728,716.568,137.152
2000,15487957.000,51804608,723.769,138.807
2001,17124416.000,53377052,731.011,138.769
2002,19022494.000,54757692,736.964,138.340
2003,21374392.000,56217084,741.642,139.018
2004,24049898.000,57823104,746.583,140.764
2005,27050484.000,59564856,751.312,143.134
2006,30437274.000,61276848,755.542,145.864
2007,34227428.000,62818256,759.478,147.298
2008,38462012.000,64052376,763.157,147.243
2009,43962712.000,64686820,766.975,142.301
2010,50110612.000,65349080,771.193,141.964
2011,56670656.000,66106652,772.328,143.618
2012,63722176.000,67036032,772.423,146.332
2013,71349296.000,68023432,773.677,148.028
2014,79360160.000,69139896,773.977,150.637
2015,87775192.000,70325160,774.418,153.072
2016,96755824.000,71524240,772.982,155.681
2017,106217664.000,72799488,771.330,158.468
2018,116379784.000,74181696,769.240,161.066
2019,126968344.000,75565584,765.730,163.924
2020,137695824.000,76785096,762.124,154.940
2021,148589856.000,78158760,757.860,160.861
2022,159623808.000,79490152,744.443,165.578
2023,171095104.000,80822920,751.185,167.540
"""
STEM = "chart-13-capital-per-worker"
TITLE = "A Chinese worker has less than half the capital of an American worker, up from 6 percent in 2000"
SUBTITLE = ("Capital stock per person engaged, thousands of 2021 US dollars at purchasing power parity, "
            "China and United States, 1980 to 2023")
SOURCE = ("Penn World Table 11.0, Feenstra, Inklaar and Timmer (2015), via FRED (rkna, emp).")
NOTE = ("Capital stock at constant national prices, expressed in 2021 US dollars at PPP. The PPP for "
        "capital goods is lower in China than the market exchange rate, so at market exchange rates "
        "China's capital per worker relative to the US would be lower.")
d = pd.read_csv(io.StringIO(KRAW), index_col=0)
d["china"] = d.china_capital_musd / d.china_workers_m / 1000
d["us"] = d.us_capital_musd / d.us_workers_m / 1000
d["china_pct_of_us"] = d.china / d.us * 100
d[["china", "us", "china_pct_of_us"]].round(2).to_csv(STEM + ".csv")
Y = d.index.values

fig, ax = post_axes(right=0.86)
ax.fill_between(Y, d.china, d.us, color=BLUE, alpha=0.07, lw=0, zorder=2)
ax.plot(Y, d.us, color=BLUE, lw=2.8, zorder=4)
ax.plot(Y, d.china, color=RED, lw=2.8, zorder=4)
for yr in (2000, 2010, 2023):
    v = d.loc[yr, "china"]; r = d.loc[yr, "china_pct_of_us"]
    ax.plot(yr, v, marker="o", ms=11, mfc=RED, mec="white", mew=1.5, ls="none", zorder=6, clip_on=False)
    ax.text(yr - 0.4 if yr != 2023 else yr - 0.6, v + 22, f"{r:.0f}% of US", fontsize=EMPH_PT, color=RED,
            fontweight="bold", ha="center" if yr != 2023 else "right", va="bottom", zorder=6)
end_labels(ax, [(d.us.iloc[-1], f"United States\n{d.us.iloc[-1]:.0f}", BLUE),
                (d.china.iloc[-1], f"China\n{d.china.iloc[-1]:.0f}", RED)], 2023.8, 60)
ax.set_xlim(1980, 2023)
ax.set_xticks([1983, 1988, 1993, 1998, 2003, 2008, 2013, 2018, 2023])
ax.set_ylim(0, 560)
ax.set_yticks([0, 100, 200, 300, 400, 500])
ax.set_ylabel("thousands of 2021 US$ per worker", labelpad=8)
ax.yaxis.grid(True, color=GRID, lw=0.8)
fig.savefig("_plot_p16.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot_p16.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png")
