"""chart-8-quarterly-deflator.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file.
Run with matplotlib, numpy, pandas and Pillow available:

    python chart-8-quarterly-deflator.py

It writes chart-8-quarterly-deflator.png and chart-8-quarterly-deflator.csv into the working directory.
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
# QUARTERLY DATA
# NBS quarterly national accounts, 1Q 2022 to 2Q 2026, from the NBS data portal
# (data.stats.gov.cn), downloaded September 2026: GDP and value added by sector at
# current prices for the quarter (nom_, 100 million yuan), the constant-price
# indices for the quarter (idx_, preceding year = 100) and the seasonally adjusted
# quarter-on-quarter GDP growth rate (qq_sa, percent). Sector deflators are implied:
# nominal year-on-year growth deflated by the constant-price index.
# ======================================================================

QRAW = """\
quarter,nom_gdp,nom_primary,nom_secondary,nom_tertiary,nom_agriculture,nom_industry,nom_manufacturing,nom_construction,nom_wholesale_retail,nom_transport,nom_hotels_catering,nom_finance,nom_real_estate,nom_ict,nom_business_services,nom_others,idx_gdp,idx_primary,idx_secondary,idx_tertiary,idx_agriculture,idx_industry,idx_manufacturing,idx_construction,idx_wholesale_retail,idx_transport,idx_hotels_catering,idx_finance,idx_real_estate,idx_ict,idx_business_services,idx_others,qq_sa
2022Q1,277175.8,10920.7,102919.5,163335.6,11572.0,90917.3,75430.8,12501.8,27555.2,11064.2,4180.0,22193.2,21989.8,13156.0,10234.6,51811.7,104.8,106.1,104.0,105.3,106.2,104.8,103.8,98.8,106.5,103.7,101.0,101.0,100.1,114.6,108.5,106.6,0.1
2022Q2,299111.5,18182.7,118689.2,162239.6,19121.9,97591.4,81320.4,21643.4,29188.2,12873.7,4119.9,21830.9,21935.1,13341.2,9253.6,48212.1,100.8,104.4,100.2,100.8,104.6,100.1,98.9,101.0,100.8,98.0,95.9,102.0,95.2,111.2,100.0,101.4,-0.7
2022Q3,315399.6,25653.5,117848.5,171897.6,26823.9,96915.0,78958.3,21544.4,31388.0,13887.4,5234.6,22372.4,21635.5,11727.2,11272.7,52598.6,104.0,103.4,103.4,104.4,103.7,103.1,101.9,105.3,104.2,104.3,103.9,101.5,97.9,111.6,108.7,106.0,3.3
2022Q4,342342.4,33450.1,128172.4,180719.8,35059.0,103227.9,84899.5,25750.3,34046.0,13142.4,5611.7,21655.0,22454.8,12811.8,13404.0,55179.4,103.0,104.0,101.9,103.6,104.2,101.4,100.6,104.4,102.9,97.6,95.3,101.9,95.1,113.6,108.9,107.4,0.5
2023Q1,292368.8,11500.4,104579.5,176288.8,12217.8,91921.4,75980.1,13285.8,29853.6,12275.4,4920.7,23876.6,22910.9,14700.8,11278.0,55127.7,104.7,103.7,102.9,105.9,103.8,102.5,102.3,106.8,106.6,105.0,115.4,105.4,101.8,111.8,108.4,104.9,1.6
2023Q2,316237.5,18695.5,119928.9,177613.2,19747.4,97298.2,81265.6,23278.3,31625.1,14235.2,5079.8,23695.1,22561.5,15419.9,11119.5,52177.6,106.5,103.7,104.9,107.9,104.0,104.2,104.4,108.3,108.6,108.9,119.3,106.1,99.4,115.2,117.2,107.1,1.3
2023Q3,328440.7,25759.7,119681.7,182999.2,27037.3,97575.0,79706.7,22827.4,33063.3,15569.8,6223.3,23693.8,20855.2,12966.8,12818.5,55810.2,105.0,104.2,104.3,105.6,104.3,103.8,104.1,106.7,106.1,108.6,114.5,104.9,97.9,110.8,111.0,104.8,1.6
2023Q4,357224.8,33213.5,131746.0,192265.3,34964.6,105388.4,86802.2,27249.1,36267.6,14357.8,6860.3,22661.4,21653.9,14410.8,15223.0,58187.7,105.3,104.2,105.1,105.7,104.3,104.8,104.8,106.7,107.6,109.5,116.5,104.4,97.8,111.6,111.0,103.6,0.8
2024Q1,304525.2,11475.6,107917.6,185132.0,12267.1,94639.6,78463.5,13962.4,31688.2,13124.8,5405.9,24594.8,20821.3,16853.6,12851.4,58316.1,105.3,103.5,105.7,105.1,103.9,105.9,106.2,104.8,107.0,106.9,107.9,103.4,95.3,114.5,111.5,104.3,1.3
2024Q2,328585.4,19057.5,124509.4,185018.5,20229.1,101408.9,84827.0,23776.2,33591.2,14752.0,5460.2,24055.6,21126.7,17043.8,12377.5,54764.1,104.7,103.8,105.3,104.3,104.1,105.8,106.0,103.3,106.3,106.1,106.5,102.5,95.9,111.0,109.5,103.6,1.0
2024Q3,341443.2,26964.5,122810.3,191668.5,28407.4,100467.3,81932.8,23120.2,35240.2,15997.8,6639.0,24496.0,20047.7,14228.9,14484.7,58314.0,104.6,103.4,104.3,104.9,103.8,104.9,104.8,102.0,106.0,106.2,106.5,104.3,98.4,110.8,111.5,103.4,1.4
2024Q4,373512.4,34138.3,135068.1,204306.0,36072.4,108002.7,89657.3,28003.9,38672.0,15170.8,7389.4,23809.3,22051.3,15831.3,17227.2,61282.1,105.4,103.9,104.9,105.9,104.2,105.6,106.0,102.5,106.7,107.5,107.2,104.7,101.7,110.5,111.8,104.3,1.6
2025Q1,318466.4,11729.8,111549.3,195187.3,12577.0,98103.9,81919.4,14255.6,33394.3,13853.7,5730.5,25316.6,21182.5,18530.5,14332.8,61188.9,105.4,103.5,105.9,105.3,103.7,106.3,106.8,103.1,105.8,107.2,105.1,103.8,101.0,110.3,110.2,104.1,1.1
2025Q2,341395.3,19505.0,126713.3,195176.9,20766.2,103996.4,87653.0,23493.4,35446.0,15556.1,5811.7,25142.2,20959.5,18908.4,13662.7,57652.6,105.2,103.8,104.8,105.7,104.0,106.2,106.5,99.4,106.0,105.6,105.2,105.8,101.0,111.8,109.0,104.4,1.2
2025Q3,354106.2,26952.3,124587.1,202566.8,28505.8,103271.0,84708.1,22201.2,36712.5,16706.3,6962.3,26191.2,19774.9,15769.1,15948.1,62063.8,104.8,104.0,104.2,105.4,104.1,105.8,106.3,97.7,104.9,104.8,103.6,105.2,99.8,111.7,108.6,105.5,1.1
2025Q4,387911.3,35159.7,136803.3,215948.3,37258.0,111454.7,92466.9,26474.9,40255.1,15976.0,7898.6,24686.6,21107.4,17390.8,19722.0,65687.3,104.5,104.2,103.4,105.2,104.3,105.0,105.1,97.5,103.7,103.4,105.6,103.3,99.0,110.7,112.7,105.9,1.1
2026Q1,334192.9,11940.8,116134.9,206117.2,12850.5,103388.2,86960.3,13632.1,35071.3,14638.0,6054.6,27224.6,20326.4,20444.0,16208.9,64354.2,105.0,103.8,104.9,105.2,104.0,106.1,106.3,96.2,104.1,104.3,104.3,106.5,99.9,110.6,112.2,104.0,1.3
2026Q2,361511.1,19581.0,134338.0,207592.0,20950.5,112836.2,95370.3,22410.8,37145.6,16691.7,6202.5,27389.8,21038.4,20890.4,15383.2,60572.1,104.3,103.7,103.0,105.1,103.9,104.7,104.8,95.9,103.3,105.1,105.8,106.9,99.8,110.8,111.6,103.7,0.9
"""

qdf = pd.read_csv(io.StringIO(QRAW), index_col="quarter")
SECTORS = [c[4:] for c in qdf.columns if c.startswith("nom_")]
nom_yoy = pd.DataFrame({s: (qdf["nom_" + s] / qdf["nom_" + s].shift(4) - 1) * 100 for s in SECTORS})
real_yoy = pd.DataFrame({s: qdf["idx_" + s] - 100 for s in SECTORS})
defl_yoy = ((1 + nom_yoy / 100) / (1 + real_yoy / 100) - 1) * 100
qlab = [q[2:4] + " Q" + q[-1] for q in qdf.index]          # "2023Q1" -> "23 Q1"

# ======================================================================
# CHART
# ======================================================================

STEM = "chart-8-quarterly-deflator"

# post-pack type: base 15, ticks 14, in-plot labels 14; title and caption raised to land at the
# house pixel sizes on this canvas width
AXIS_PT, TICK_PT, LEGEND_PT, LABEL_PT, EMPH_PT = 15, 14, 14, 14, 17
TITLE_PT, CAP_PT = TITLE_PT * 1980 / 1640, CAP_PT * 1980 / 1640
GRID = "#E6E6E6"

TITLE = ("For the first time in three years, nominal GDP growth exceeded real growth")
SUBTITLE = ("China's nominal GDP growth split into real growth and the GDP deflator, year on year, "
            "percent, 1Q 2023 to 2Q 2026")
SOURCE = ("National Bureau of Statistics of China, quarterly national accounts (data.stats.gov.cn), "
          "accessed September 2026.")
NOTE = ("The deflator is implied: nominal GDP for the quarter over the same quarter a year earlier, "
        "deflated by the NBS constant-price index.")

d = pd.DataFrame({"real": real_yoy["gdp"], "deflator": defl_yoy["gdp"], "nominal": nom_yoy["gdp"]}).dropna()
d.round(2).to_csv(STEM + ".csv")
labels = [q[2:4] + "\nQ" + q[-1] for q in d.index]

rc()
fig, ax = plt.subplots(figsize=(8.9, 4.8), dpi=DPI)
fig.subplots_adjust(left=0.072, right=0.985, top=0.965, bottom=0.13)

x = np.arange(len(d))
ax.bar(x, d["real"], width=0.78, color=BLUE, label="real GDP growth", zorder=3, lw=0)
ax.bar(x, d["deflator"], bottom=np.where(d["deflator"] >= 0, d["real"], 0), width=0.78,
       color=np.where(d["deflator"] >= 0, GOLD, RED), zorder=3, lw=0)
ax.plot(x, d["nominal"], color=INK, lw=2.2, marker="o", ms=5.5, mfc="white", mew=1.6,
        label="nominal GDP growth", zorder=5)
for i, v in enumerate(d["deflator"]):
    y = (d["real"].iloc[i] + v / 2) if v >= 0 else v / 2
    if abs(v) >= 0.5:
        ax.text(x[i], y, f"{v:+.1f}", fontsize=LABEL_PT - 1, color="white", ha="center",
                va="center", fontweight="bold", zorder=6)
for i, v in enumerate(d["real"]):
    ax.text(x[i], v / 2, f"{v:.1f}", fontsize=LABEL_PT - 1, color="white", ha="center",
            va="center", fontweight="bold", zorder=6)
ax.annotate("nominal growth back\nabove real growth", xy=(x[-1], d["nominal"].iloc[-1]),
            xytext=(x[-1] - 3.4, 7.3), fontsize=LABEL_PT, color=INK, ha="center", va="center",
            linespacing=1.15, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.9, shrinkB=4),
            zorder=6)

ax.axhline(0, color=GREY, lw=1.0, zorder=2)
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlim(-0.6, len(d) - 0.4)
ax.set_ylim(-2.2, 8)
ax.set_yticks([-2, 0, 2, 4, 6, 8])
ax.set_ylabel("percent, year on year", labelpad=8)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color=GRID, lw=0.8)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)
handles = [matplotlib.patches.Patch(color=BLUE, label="real GDP growth"),
           matplotlib.patches.Patch(color=RED, label="GDP deflator, negative"),
           matplotlib.patches.Patch(color=GOLD, label="GDP deflator, positive"),
           matplotlib.lines.Line2D([], [], color=INK, lw=2.2, marker="o", ms=5.5, mfc="white",
                                   mew=1.6, label="nominal GDP growth")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=False,
          handlelength=1.2, columnspacing=1.4)

fig.savefig("_plot19.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot19.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
