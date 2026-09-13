"""chart-10-AI-preparedness.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-10-AI-preparedness.py

It writes chart-10-AI-preparedness.png and chart-10-AI-preparedness.csv into the
working directory.

The layout, the packing, the sizing, the labelling rule and the legend are the
same as chart 3, so the two can be read side by side. Only the vertical variable
and its range differ.

HOW THE DATA WERE PUT TOGETHER
------------------------------
Three inputs, joined on the economy:

1. The AI Preparedness Index, from the IMF. The file lists 174 economies but
   carries a score for 165 of them; the nine listed without one (Macao, Puerto
   Rico, Taiwan, Maldives, Afghanistan, Sao Tome and Principe, Somalia, South
   Sudan and Uzbekistan) are dropped rather than treated as zero. The file
   carries ISO3 codes, so the join needs no name matching, unlike chart 3.

2. World Bank income group, the class held in 2023, taken from the 2023 column of
   the Classification sheet of 20260725-inversion-income-classification-2050
   .xlsx. That column is history, not projection: it is the official OGHIST class
   for the year, so it needs no assumption from the projection model. The same
   year is used as in chart 3, which is what lets the two charts be compared.

3. Population, millions in 2023, from the Population sheet of the same workbook,
   which carries WDI SP.POP.TOTL for 1990 to 2025.

One more, Venezuela, is dropped because the World Bank left it unclassified in
2023, the same economy chart 3 drops for the same reason. That leaves 164
economies covering 7.84 billion people.

HOW THE CHART IS BUILT
----------------------
* One bubble per economy, area proportional to 2023 population: the matplotlib
  scatter size is 5.1 points squared per million people. The legend circles at
  1, 10, 100 and 1,000 million are drawn with the same scatter call on their own
  axes, so they are literally to scale rather than approximated, and stepping
  them a decade apart shows the range without four near identical circles. They
  are outlines rather than fills, so they read as a ruler and not as four more
  economies.
* Bubbles are packed outward from the centre of their column, largest first,
  each taking the smallest horizontal offset that does not overlap one already
  placed. Horizontal position therefore carries no information; it is only a way
  of showing 164 overlapping circles at once.
* The horizontal bar in each column is the population-weighted mean index of the
  group, that is sum(index * population) / sum(population) over the economies in
  the column.
* An economy is labelled with its ISO3 code if it has more than 50 million
  people, or if it is among the three highest or three lowest index values in its
  column. A code sits at the centre of its own bubble where that is free, and
  otherwise moves out to the nearest ring position that clears the labels
  already placed.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import to_rgba
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
# IMF AI Preparedness Index, World Bank income class held in 2023, and 2023
# population in millions (WDI SP.POP.TOTL). Joined on ISO3 code.
# ======================================================================

RAW = """\
code,economy,income_group,aipi,population_m
SGP,Singapore,H,0.8006,5.918
DNK,Denmark,H,0.7785,5.947
USA,United States,H,0.7713,336.755
NLD,Netherlands,H,0.7665,17.877
EST,Estonia,H,0.7644,1.37
FIN,Finland,H,0.758,5.584
CHE,Switzerland,H,0.757,8.889
NZL,New Zealand,H,0.7537,5.2
DEU,Germany,H,0.7533,83.287
SWE,Sweden,H,0.7478,10.537
LUX,Luxembourg,H,0.7353,0.666
JPN,Japan,H,0.7332,124.517
GBR,United Kingdom,H,0.7309,68.526
AUS,Australia,H,0.7271,26.66
KOR,Korea,H,0.7266,51.713
ISR,Israel,H,0.7255,9.849
AUT,Austria,H,0.7246,9.132
CAN,Canada,H,0.7132,40.049
NOR,Norway,H,0.7058,5.52
HKG,Hong Kong,H,0.7006,7.536
ISL,Iceland,H,0.7001,0.386
FRA,France,H,0.6975,68.372
IRL,Ireland,H,0.6931,5.312
BEL,Belgium,H,0.6725,11.78
LTU,Lithuania,H,0.6649,2.872
MLT,Malta,H,0.6592,0.553
ESP,Spain,H,0.6483,48.353
CZE,Czechia,H,0.6462,10.864
PRT,Portugal,H,0.646,10.578
SVN,Slovenia,H,0.6339,2.12
CYP,Cyprus,H,0.6324,1.345
LVA,Latvia,H,0.6324,1.884
ARE,United Arab Emirates,H,0.6282,10.484
ITA,Italy,H,0.6207,58.984
POL,Poland,H,0.5969,36.687
SVK,Slovakia,H,0.5916,5.427
CHL,Chile,H,0.5858,19.659
ROU,Romania,H,0.5836,19.061
GRC,Greece,H,0.582,10.407
HRV,Croatia,H,0.5817,3.86
BGR,Bulgaria,H,0.5773,6.447
SAU,Saudi Arabia,H,0.5769,33.703
HUN,Hungary,H,0.563,9.592
RUS,Russian Federation,H,0.5592,143.826
URY,Uruguay,H,0.5486,3.388
QAT,Qatar,H,0.5346,2.656
OMN,Oman,H,0.5328,5.049
SYC,Seychelles,H,0.5307,0.12
BHR,Bahrain,H,0.5153,1.577
BRB,Barbados,H,0.5047,0.282
PAN,Panama,H,0.5013,4.459
BRN,Brunei Darussalam,H,0.4953,0.459
KWT,Kuwait,H,0.4613,4.853
BHS,Bahamas,H,0.4575,0.399
TTO,Trinidad and Tobago,H,0.4356,1.368
GUY,Guyana,H,0.4242,0.826
RWA,Rwanda,L,0.4374,13.954
LBR,Liberia,L,0.3703,5.493
GMB,Gambia,L,0.36,2.698
UGA,Uganda,L,0.3539,48.657
MWI,Malawi,L,0.34,21.104
NER,Niger,L,0.3258,26.16
TGO,Togo,L,0.3157,8.224
BFA,Burkina Faso,L,0.3118,23.026
MDG,Madagascar,L,0.3054,31.196
SYR,Syrian Arab Republic,L,0.2981,23.595
SLE,Sierra Leone,L,0.2978,8.461
MLI,Mali,L,0.2961,23.769
BDI,Burundi,L,0.2946,13.689
GNB,Guinea-Bissau,L,0.2649,2.153
MOZ,Mozambique,L,0.2574,33.635
ETH,Ethiopia,L,0.2536,128.692
YEM,Yemen,L,0.2533,39.391
COD,Congo,L,0.2475,105.79
TCD,Chad,L,0.2336,19.319
SDN,Sudan,L,0.2329,50.043
CAF,Central African Republic,L,0.1844,5.152
PHL,Philippines,LM,0.4985,114.891
IND,India,LM,0.4925,1438.07
JOR,Jordan,LM,0.4828,11.439
VNM,Viet Nam,LM,0.4819,100.352
TUN,Tunisia,LM,0.4654,12.2
KEN,Kenya,LM,0.4452,55.339
BTN,Bhutan,LM,0.4419,0.786
LKA,Sri Lanka,LM,0.4361,22.037
CPV,Cabo Verde,LM,0.4326,0.522
MAR,Morocco,LM,0.4291,37.713
TLS,Timor-Leste,LM,0.4277,1.384
KGZ,Kyrgyzstan,LM,0.4258,7.1
GHA,Ghana,LM,0.4252,33.788
LBN,Lebanon,LM,0.4178,5.773
SEN,Senegal,LM,0.396,18.078
EGY,Egypt,LM,0.3941,114.536
BGD,Bangladesh,LM,0.3841,171.467
BOL,Bolivia,LM,0.3766,12.244
ZMB,Zambia,LM,0.3707,20.724
KHM,Cambodia,LM,0.37,17.424
PAK,Pakistan,LM,0.3686,247.504
TJK,Tajikistan,LM,0.3664,10.39
CIV,Côte d'Ivoire,LM,0.3655,31.166
BEN,Benin,LM,0.3632,14.111
LSO,Lesotho,LM,0.3554,2.311
TZA,Tanzania,LM,0.3524,66.618
NPL,Nepal,LM,0.351,29.695
HND,Honduras,LM,0.3418,10.645
CMR,Cameroon,LM,0.3413,28.373
NGA,Nigeria,LM,0.3363,227.883
NIC,Nicaragua,LM,0.3314,6.824
LAO,Lao People's Democratic Republic,LM,0.3305,7.665
MMR,Myanmar,LM,0.3275,54.134
GIN,Guinea,LM,0.3235,14.405
DJI,Djibouti,LM,0.3189,1.153
SWZ,Eswatini,LM,0.3062,1.231
ZWE,Zimbabwe,LM,0.3048,16.341
PNG,Papua New Guinea,LM,0.2901,10.39
COG,Congo,LM,0.2766,6.183
HTI,Haiti,LM,0.2683,11.637
AGO,Angola,LM,0.2597,36.75
COM,Comoros,LM,0.2542,0.85
MRT,Mauritania,LM,0.2329,5.022
CHN,China,UM,0.6355,1410.71
MYS,Malaysia,UM,0.632,35.126
KAZ,Kazakhstan,UM,0.5524,20.33
CRI,Costa Rica,UM,0.5402,5.106
TUR,Turkey,UM,0.5402,85.326
SRB,Serbia,UM,0.5375,6.623
THA,Thailand,UM,0.5357,71.702
MEX,Mexico,UM,0.532,129.74
GEO,Georgia,UM,0.5299,3.715
ALB,Albania,UM,0.5268,2.412
MUS,Mauritius,UM,0.5251,1.249
IDN,Indonesia,UM,0.5163,281.19
UKR,Ukraine,UM,0.5125,37.733
MNE,Montenegro,UM,0.5037,0.624
BRA,Brazil,UM,0.5013,211.141
ZAF,South Africa,UM,0.4968,63.212
ARM,Armenia,UM,0.4929,2.964
PER,Peru,UM,0.4911,33.846
COL,Colombia,UM,0.4895,52.321
MNG,Mongolia,UM,0.4844,3.481
MKD,Republic of North Macedonia,UM,0.482,1.828
MDA,Moldova,UM,0.4806,2.458
ARG,Argentina,UM,0.4738,45.538
AZE,Azerbaijan,UM,0.4709,10.154
BLR,Belarus,UM,0.4708,9.178
DOM,Dominican Republic,UM,0.4688,11.331
FJI,Fiji,UM,0.4488,0.924
ECU,Ecuador,UM,0.4421,17.98
JAM,Jamaica,UM,0.4338,2.84
BIH,Bosnia and Herzegovina,UM,0.4279,3.185
BLZ,Belize,UM,0.4226,0.411
NAM,Namibia,UM,0.4196,2.963
SUR,Suriname,UM,0.4179,0.629
BWA,Botswana,UM,0.4128,2.48
PRY,Paraguay,UM,0.4098,6.844
GTM,Guatemala,UM,0.3901,18.125
SLV,El Salvador,UM,0.3897,6.31
IRN,Iran,UM,0.3783,90.609
LCA,Saint Lucia,UM,0.3742,0.179
DZA,Algeria,UM,0.3704,46.164
VCT,Saint Vincent and the Grenadines,UM,0.3419,0.101
GAB,Gabon,UM,0.3225,2.485
IRQ,Iraq,UM,0.2698,45.074
LBY,Libya,UM,0.245,7.306
"""

STEM = "chart-10-AI-preparedness"
df = pd.read_csv(io.StringIO(RAW))
df.to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================

# Income groups keep the pack's standing colours: low red, lower-middle gold,
# upper-middle green, high blue. Columns run from high to low, left to right.
GROUPS = [("H",  "High\nincome countries",          BLUE),
          ("UM", "Upper-middle\nincome countries",  GREEN),
          ("LM", "Lower-middle\nincome countries",  GOLD),
          ("L",  "Low\nincome countries",           RED)]

S_PER_MILLION = 5.1       # scatter area, points squared, per million people
FACE_ALPHA = 0.7          # no outline, so the fill alone carries the bubble
LEGEND_POPS = [1, 10, 100, 1000]      # a decade apart, so the legend reads as a log ladder
LABEL_POP = 50            # label every economy above this many million
LABEL_TAIL = 3            # and the three highest and three lowest in each column
BAR_LW = 1.6              # the group average rule

# The packer works within a column and cannot see across the gap between two, so a
# bubble pushed to the edge of one can still land against a bubble at the edge of its
# neighbour. One hand nudge, in x units, for the single case where that happens.
NUDGE = {}                # no cross-column collision needs a hand nudge here
CODE_PT = 9.0             # the house LABEL_PT of 11.5 is too large for ~90 codes

XLIM = (-0.58, 3.58)
YLIM = (0.13, 0.85)
FIGW, FIGH = 12.5, 8.8
LEFT, RIGHT, TOP, BOTTOM = 0.045, 0.996, 0.978, 0.265
LEG_H = 0.175             # the legend strip below the plot, as a share of the figure

TITLE = "Major AI preparedness gaps exist between countries"
SUBTITLE = "IMF AI Preparedness Index, by World Bank income group in 2023"
SOURCE = ("IMF AI Preparedness Index, and World Bank income classification and population "
          "data.")
NOTE = ("The horizontal bar is the population-weighted mean index of the group. An economy is "
        "labelled with its ISO3 code if it has more than 50 million people or if it is among the "
        "three highest or three lowest index values in its column.")

# This chart alone opens the gap under the subtitle. compose() reads the constant at
# call time, so setting it here overrides the pack default of 70 for this file only.
GAP_SUB_PLOT = 90


def _geometry():
    """Inches per unit on each axis, needed to test bubble and label overlap in the
    space the reader actually sees rather than in data units."""
    w = FIGW * (RIGHT - LEFT) / (XLIM[1] - XLIM[0])
    h = FIGH * (TOP - BOTTOM) / (YLIM[1] - YLIM[0])
    return w, h


def pack(xc, ys, sizes, xin, yin, span=0.495, step=0.005, tighten=(1.45, 0.88)):
    """Largest first, each bubble takes the smallest offset from the column centre
    that clears those already placed. The first pass asks for full clearance plus a
    little, which spreads the column out; anything that cannot be placed that way
    gets a second pass at a tighter standard rather than being dumped in the middle.
    Column centres are one unit apart, so span stays below 0.5 and columns never mix."""
    r = np.sqrt(np.asarray(sizes) / np.pi) / 72.0          # radius, inches
    out = np.full(len(ys), np.nan)
    placed = []

    def try_place(i, t):
        for d in np.arange(0, span, step):
            for cand in ((xc,) if d == 0 else (xc + d, xc - d)):
                if all(((cand - px) * xin) ** 2 + ((ys[i] - py) * yin) ** 2
                       >= (t * (r[i] + pr)) ** 2 for px, py, pr in placed):
                    return cand
        return None

    order = np.argsort(-np.asarray(sizes))
    leftover = []
    for i in order:
        cand = try_place(i, tighten[0])
        if cand is None:
            leftover.append(i)
        else:
            out[i] = cand
            placed.append((cand, ys[i], r[i]))
    for i in leftover:
        cand = try_place(i, tighten[1])
        out[i] = xc if cand is None else cand
        placed.append((out[i], ys[i], r[i]))
    return out


# label anchors: right, left, above, below, then the diagonals, at three distances
ANGLES = [0, 180, 90, 270, 45, 135, 315, 225]


def place_labels(ax, items, xin, yin):
    """items: (x, y, radius_in, text, colour), most important first. A code sits at the
    centre of its own bubble wherever that is free, which is the easiest thing to read;
    only where the centre is already taken does it move out to the nearest clear ring."""
    boxes, dropped = [], 0
    for x, y, r, text, colour in items:
        w = 0.62 * CODE_PT / 72 * len(text)                # DejaVu Sans, roughly
        h = CODE_PT / 72
        best = None
        for gap, a in [(None, None)] + [(g, a) for g in (0.035, 0.14, 0.26) for a in ANGLES]:
            if gap is None:
                cx, cy = x, y                              # the bubble's own centre
            else:
                dx = np.cos(np.radians(a)) * (r + gap + w / 2)
                dy = np.sin(np.radians(a)) * (r + gap + h / 2)
                cx, cy = x + dx / xin, y + dy / yin
            bx0, bx1 = cx - w / 2 / xin, cx + w / 2 / xin
            by0, by1 = cy - h / 2 / yin, cy + h / 2 / yin
            if bx0 < XLIM[0] or bx1 > XLIM[1] or by0 < YLIM[0] or by1 > YLIM[1]:
                continue
            if any(bx0 < b[1] and bx1 > b[0] and by0 < b[3] and by1 > b[2] for b in boxes):
                continue
            best = (cx, cy, bx0, bx1, by0, by1)
            break
        if not best:
            dropped += 1                                   # no clear spot, leave it off
            continue
        cx, cy, bx0, bx1, by0, by1 = best
        boxes.append((bx0, bx1, by0, by1))
        ax.text(cx, cy, text, color=colour, fontsize=CODE_PT, ha="center", va="center",
                zorder=6, path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])
    return dropped


rc()
fig = plt.figure(figsize=(FIGW, FIGH), dpi=DPI)
ax = fig.add_axes([LEFT, BOTTOM, RIGHT - LEFT, TOP - BOTTOM])
xin, yin = _geometry()

label_items = []
for i, (code, name, colour) in enumerate(GROUPS):
    g = df[df["income_group"] == code].sort_values("aipi", ascending=False).reset_index(drop=True)
    s = g["population_m"].values * S_PER_MILLION
    x = pack(i, g["aipi"].values, s, xin, yin)
    x = x + np.array([NUDGE.get(c, 0.0) for c in g["code"]])
    ax.scatter(x, g["aipi"], s=s, facecolors=to_rgba(colour, FACE_ALPHA),
               edgecolors="none", zorder=3)

    wavg = np.average(g["aipi"], weights=g["population_m"])
    ax.plot([i - 0.30, i + 0.30], [wavg, wavg], color=INK, lw=BAR_LW, solid_capstyle="butt",
            zorder=5)

    tails = set(g.index[:LABEL_TAIL]) | set(g.index[-LABEL_TAIL:])
    for j, row in g.iterrows():
        if row["population_m"] > LABEL_POP or j in tails:
            label_items.append((row["population_m"], x[j], row["aipi"],
                                np.sqrt(s[j] / np.pi) / 72.0, row["code"], INK))

label_items.sort(key=lambda t: -t[0])
skipped = place_labels(ax, [t[1:] for t in label_items], xin, yin)

ax.set_xlim(*XLIM)
ax.set_ylim(*YLIM)
ax.set_xticks(range(len(GROUPS)))
ax.set_xticklabels([n for _, n, _ in GROUPS])
ax.set_yticks([0.2, 0.4, 0.6, 0.8])
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E6E6E6", lw=0.8)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="both", length=0)
ax.tick_params(axis="x", pad=8)

# ---- legend: a strip below the plot, so the chart keeps the full width. The
# circles come from the same scatter call as the chart, so they are literally to
# size; x runs in inches here to make the spacing arithmetic readable.
lg = fig.add_axes([LEFT, 0.012, RIGHT - LEFT, LEG_H])
LW_IN = FIGW * (RIGHT - LEFT)
lg.set_xlim(0, LW_IN); lg.set_ylim(0, 1); lg.axis("off")

CY, GAP = 0.62, 0.30                                   # circle centres, and the gap between them
lg.text(0.0, CY, "Population (millions)", fontsize=LEGEND_PT, color=INK, ha="left", va="center")
cursor = 0.62 * LEGEND_PT / 72 * len("Population (millions)") + 0.35
for pop in LEGEND_POPS:
    r = np.sqrt(pop * S_PER_MILLION / np.pi) / 72.0
    cx = cursor + r
    lg.scatter([cx], [CY], s=pop * S_PER_MILLION, facecolors="none",
               edgecolors=GREY, linewidths=1.0, clip_on=False)
    lg.text(cx, 0.10, "{:,}".format(pop), fontsize=LEGEND_PT, color=INK, ha="center", va="center")
    cursor = cx + r + GAP

lg.plot([cursor + 0.4, cursor + 1.0], [CY, CY], color=INK, lw=BAR_LW, clip_on=False)
lg.text(cursor + 1.15, CY, "Group average (population weighted)", fontsize=LEGEND_PT,
        color=INK, ha="left", va="center")

fig.savefig("_plot10.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot10.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv",
      "|", len(label_items), "labels wanted,", skipped, "had no clear spot")
