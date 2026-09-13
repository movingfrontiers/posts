"""chart-13-open-ended-range-income-classification.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy, pandas and Pillow available:

    python chart-13-open-ended-range-income-classification.py

It writes chart-13-open-ended-range-income-classification.png and
chart-13-open-ended-range-income-classification.csv into the working directory.

PROVENANCE, FROZEN VINTAGE. Nothing is read from disk or the network.
  Classification and thresholds : World Bank OGHIST, 1 July 2026 (FY27).
  GNI per capita and population : World Bank WDI, July 2026 release, Atlas
                                  method, current US$, 2025 data year.
  Frozen: 28 August 2026, from the published csv. The chart is pinned to this
  vintage; do not swap the embedded table for a live API call.

WHAT THE CHART IS FOR
---------------------
The high-income group has a floor and no ceiling, so it is not one step among
four. The two panels show the same 207 economies on the same data: on a linear
scale, where equal widths are equal dollars, the high-income band swallows the
chart and almost every economy is crushed against the left edge; on a log scale,
where equal widths are equal ratios, the four bands are comparable and the
spread inside high income becomes visible. Neither panel is the honest one on
its own, which is why both are drawn.

WHAT CHANGED FROM THE EARLIER CUT OF THIS CHART
-----------------------------------------------
The plot is the same, including the seeded jitter, the pinned positions for the
labelled economies and the coloured band along the bottom of each panel. What has
been replaced is the furniture: the hand-rolled PIL title band, and the caption
engine that measured word widths, wrapped greedily to a right margin, appended
filler sentences until the last two lines packed correctly, and asserted the
watermark sat one "movi" clear of the text. All of that is now compose(), which
gives this chart the same gaps and border as the rest of the pack. The data
assertions are kept: they are what stop the note from drifting away from the
table.
"""

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
# 207 classified economies, 2025 GNI per capita and population.
# Row order matters: the jitter generator maps to it.
# ======================================================================

RAW = """\
economy,gni_per_capita_usd_atlas_2025,population_millions_2025,income_group_fy27
Bermuda,139370,0.065,High income
Liechtenstein,116380,0.041,High income
Switzerland,110330,9.092,High income
Norway,97310,5.611,High income
Luxembourg,95720,0.687,High income
Iceland,89220,0.392,High income
United States,88810,341.785,High income
Ireland,87360,5.484,High income
Isle of Man,87030,0.084,High income
Cayman Islands,81920,0.076,High income
Singapore,81760,6.111,High income
Denmark,77190,6.009,High income
Qatar,74330,2.972,High income
Faeroe Islands,73120,0.055,High income
"Macao SAR, China",69920,0.686,High income
Netherlands,68530,18.088,High income
Australia,64120,27.614,High income
Sweden,63010,10.597,High income
"Hong Kong SAR, China",62500,7.499,High income
Austria,60360,9.208,High income
Germany,60200,83.491,High income
Belgium,59500,11.942,High income
Canada,56420,41.652,High income
Israel,56180,10.123,High income
Finland,55250,5.646,High income
United Kingdom,54550,69.487,High income
San Marino,53910,0.034,High income
Andorra,53230,0.083,High income
United Arab Emirates,51550,11.513,High income
France,48630,68.72,High income
New Zealand,46630,5.325,High income
Italy,42080,58.916,High income
Malta,41440,0.58,High income
Kuwait,41110,4.865,High income
Sint Maarten (Dutch part),38950,0.044,High income
Japan,38340,123.367,High income
"Korea, Rep.",37880,51.685,High income
Spain,37120,49.355,High income
"Bahamas, The",37020,0.403,High income
Turks and Caicos Islands,36760,0.047,High income
Cyprus,36110,1.371,High income
Saudi Arabia,36070,36.974,High income
Slovenia,35520,2.131,High income
Aruba,35200,0.109,High income
Greenland,34800,0.057,High income
Brunei Darussalam,34790,0.466,High income
Czechia,32960,10.887,High income
Estonia,32310,1.366,High income
Lithuania,30500,2.889,High income
New Caledonia,30070,0.295,High income
Portugal,29930,10.805,High income
Bahrain,28790,1.6,High income
Guyana,28470,0.836,High income
Puerto Rico (U.S.),27320,3.185,High income
Barbados,27080,0.283,High income
Slovak Republic,26410,5.414,High income
Poland,25520,36.436,High income
Greece,25360,10.414,High income
Croatia,25360,3.876,High income
Latvia,24980,1.848,High income
St. Kitts and Nevis,24530,0.047,High income
French Polynesia,24100,0.282,High income
Uruguay,24020,3.385,High income
Hungary,23850,9.514,High income
Antigua and Barbuda,23790,0.094,High income
Curaçao,22570,0.156,High income
Nauru,20690,0.012,High income
Romania,20190,19.02,High income
Palau,19890,0.018,High income
Oman,19520,5.495,High income
Seychelles,19200,0.123,High income
Panama,19140,4.571,High income
Trinidad and Tobago,18550,1.368,High income
Costa Rica,17930,5.153,High income
Bulgaria,17780,6.433,High income
Chile,16960,19.86,High income
Türkiye,16300,85.879,Upper middle income
Russian Federation,15960,143.513,High income
Argentina,14650,45.851,Upper middle income
China,14230,1406.585,Upper middle income
Montenegro,14150,0.623,Upper middle income
Mauritius,14040,1.244,Upper middle income
Kazakhstan,13740,20.844,Upper middle income
Mexico,13730,131.947,Upper middle income
Serbia,13480,6.549,Upper middle income
St. Lucia,13410,0.18,Upper middle income
Maldives,12950,0.53,Upper middle income
Malaysia,12380,35.978,Upper middle income
Albania,12060,2.35,Upper middle income
St. Vincent and the Grenadines,12000,0.1,Upper middle income
Grenada,11660,0.117,Upper middle income
Dominica,10690,0.066,Upper middle income
Dominican Republic,10620,11.52,Upper middle income
Brazil,10550,212.812,Upper middle income
Bosnia and Herzegovina,9940,3.14,Upper middle income
Tuvalu,9780,0.009,Upper middle income
Marshall Islands,9710,0.036,Upper middle income
North Macedonia,9490,1.821,Upper middle income
Belarus,9160,9.086,Upper middle income
Armenia,9020,3.087,Upper middle income
Cuba,9010,10.937,Upper middle income
Georgia,8990,3.936,Upper middle income
Peru,8430,34.577,Upper middle income
Gabon,8090,2.593,Upper middle income
Moldova,8050,2.361,Upper middle income
Colombia,7900,53.426,Upper middle income
Jamaica,7790,2.837,Upper middle income
Kosovo,7760,1.577,Upper middle income
Thailand,7690,71.62,Upper middle income
Belize,7530,0.423,Upper middle income
Botswana,7390,2.562,Upper middle income
Azerbaijan,7360,10.247,Upper middle income
Libya,7250,7.459,Upper middle income
Ecuador,6890,18.29,Upper middle income
Tonga,6840,0.104,Upper middle income
Paraguay,6750,7.013,Upper middle income
Guatemala,6360,18.688,Upper middle income
Turkmenistan,6340,7.619,Upper middle income
South Africa,6270,64.747,Upper middle income
Fiji,6230,0.933,Upper middle income
Mongolia,6210,3.569,Upper middle income
Suriname,6140,0.64,Upper middle income
Equatorial Guinea,5890,1.938,Upper middle income
Algeria,5850,47.435,Upper middle income
Iraq,5690,47.021,Upper middle income
Samoa,5640,0.219,Upper middle income
Cabo Verde,5590,0.527,Upper middle income
Ukraine,5510,38.98,Upper middle income
El Salvador,5410,6.366,Upper middle income
Jordan,5260,11.521,Upper middle income
Indonesia,5120,285.721,Upper middle income
Viet Nam,4970,101.599,Upper middle income
Philippines,4850,116.787,Upper middle income
"Micronesia, Fed. Sts.",4760,0.114,Upper middle income
Sri Lanka,4670,21.756,Upper middle income
"Iran, Islamic Rep.",4650,92.418,Upper middle income
Bolivia,4420,12.582,Lower middle income
Vanuatu,4410,0.335,Lower middle income
Morocco,4360,38.431,Lower middle income
Namibia,4340,3.093,Lower middle income
Bhutan,4310,0.797,Lower middle income
Tunisia,4300,12.349,Lower middle income
Djibouti,3960,1.184,Lower middle income
Kiribati,3930,0.136,Lower middle income
"Venezuela, RB",3860,28.517,Lower middle income
São Tomé and Príncipe,3800,0.24,Lower middle income
Eswatini,3730,1.256,Lower middle income
Uzbekistan,3670,37.053,Lower middle income
Lebanon,3560,5.849,Lower middle income
Honduras,3270,11.006,Lower middle income
"Egypt, Arab Rep.",3260,118.366,Lower middle income
West Bank and Gaza,3250,5.414,Lower middle income
Papua New Guinea,2890,10.763,Lower middle income
Angola,2860,39.04,Lower middle income
Nicaragua,2850,7.008,Lower middle income
Bangladesh,2840,175.687,Lower middle income
Kyrgyz Republic,2800,7.343,Lower middle income
Côte d'Ivoire,2780,32.712,Lower middle income
India,2760,1463.866,Lower middle income
Cambodia,2750,17.848,Lower middle income
Zimbabwe,2660,16.951,Lower middle income
Ghana,2630,35.064,Lower middle income
"Congo, Rep.",2280,6.484,Lower middle income
Mauritania,2210,5.315,Lower middle income
Kenya,2200,57.532,Lower middle income
Lao PDR,2150,7.873,Lower middle income
Tajikistan,2080,10.787,Lower middle income
Solomon Islands,2020,0.839,Lower middle income
Haiti,2010,11.906,Lower middle income
Comoros,1950,0.883,Lower middle income
Cameroon,1860,29.879,Lower middle income
Senegal,1780,18.932,Lower middle income
Guinea,1730,15.1,Lower middle income
Benin,1600,14.814,Lower middle income
Nepal,1570,29.618,Lower middle income
Timor-Leste,1510,1.419,Lower middle income
Pakistan,1500,255.22,Lower middle income
Nigeria,1360,237.528,Lower middle income
Togo,1350,8.592,Lower middle income
Myanmar,1320,54.851,Lower middle income
Lesotho,1280,2.363,Lower middle income
Tanzania,1270,70.546,Lower middle income
Zambia,1200,21.914,Lower middle income
Rwanda,1150,14.569,Low income
Uganda,1120,51.385,Low income
Mali,1120,25.199,Low income
Ethiopia,1110,135.472,Low income
Guinea-Bissau,1090,2.25,Low income
South Sudan,1050,12.189,Low income
Burkina Faso,980,24.075,Low income
Chad,970,21.004,Low income
"Gambia, The",930,2.822,Low income
Sudan,900,51.662,Low income
Sierra Leone,830,8.82,Low income
Liberia,830,5.731,Low income
Niger,750,27.918,Low income
"Yemen, Rep.",740,41.774,Low income
"Congo, Dem. Rep.",720,112.832,Low income
Syrian Arab Republic,720,25.62,Low income
Eritrea,650,3.607,Low income
"Somalia, Fed. Rep.",640,19.655,Low income
Malawi,600,22.216,Low income
Mozambique,570,35.632,Low income
Central African Republic,560,5.513,Low income
Madagascar,560,32.741,Low income
Afghanistan,390,43.844,Low income
Burundi,240,14.39,Low income
"""

STEM = "chart-13-open-ended-range-income-classification"
df = pd.read_csv(io.StringIO(RAW))
df.to_csv(STEM + ".csv", index=False)

GRP = {"Low income": "L", "Lower middle income": "LM",
       "Upper middle income": "UM", "High income": "H"}
g = pd.DataFrame({"name": df["economy"],
                  "base": df["gni_per_capita_usd_atlas_2025"].astype(float),
                  "pop": df["population_millions_2025"],
                  "cls": df["income_group_fy27"].map(GRP)})

# ======================================================================
# CHART
# ======================================================================

COL = {"L": RED, "LM": GOLD, "UM": GREEN, "H": BLUE}
TH = (1175, 4635, 14375)          # FY27 thresholds, 2025 GNI per capita
TOP = 140000                      # both panels end above Bermuda, the maximum
NAME_PT = 8.6                     # economy labels; LABEL_PT is too large beside a bubble
BAND_LW = 9.6                     # the four-group bar along the bottom of each panel
ALPHA = 0.45

TITLE = "Most countries remain far from the frontier"
SUBTITLE = ("Classified economies by GNI per capita against the FY27 income thresholds, sized by "
            "population, on a linear and a logarithmic scale")
SOURCE = "World Bank OGHIST and WDI."
NOTE = ("Each bubble is one of the 207 classified economies with a reported income level, placed "
        "by its GNI per capita. The coloured bar marks the four income groups at the FY27 "
        "thresholds of $1,175, $4,635 and $14,375. The high-income group has no upper bound, so "
        "both scales end at Bermuda ($139,370), the highest observed income. Bubble area rises "
        "nonlinearly with population.")

# ---- the note has to keep agreeing with the table ----
assert "%d classified " % len(g) in NOTE, "note economy count no longer matches the data"
assert "$1,175, $4,635 and $14,375" in NOTE and TH == (1175, 4635, 14375), \
    "note threshold values no longer match TH"
_mx = g.loc[g["base"].idxmax()]
assert _mx["name"] == "Bermuda" and "Bermuda ($139,370)" in NOTE and int(_mx["base"]) == 139370, \
    "note maximum no longer matches the data"
assert g["base"].max() <= TOP, "the linear scale no longer covers the maximum"


def area(pop_m):
    """Bubble area against population, compressed. Strict proportionality would make
    the smallest economies invisible next to China; a cube of the log keeps the big
    ones large without losing the small ones."""
    if pop_m < 10:
        return 10
    x = (np.log10(pop_m) - 1.0) / (np.log10(1450) - 1.0)
    return 10 + x ** 3.4 * 2200


rng = np.random.default_rng(7)
g["yj"] = rng.uniform(0.17, 0.92, len(g))
SIDE = {"China": "right", "India": "right", "United States": "right", "Indonesia": "eleven",
        "Nigeria": "right", "Pakistan": "left", "Brazil": "left", "Japan": "right",
        "Congo, Dem. Rep.": "right", "Malaysia": "right", "Bermuda": "left"}
PINY = {"China": 0.68, "India": 0.42, "United States": 0.52, "Indonesia": 0.72,
        "Nigeria": 0.56, "Pakistan": 0.32, "Brazil": 0.62, "Japan": 0.30,
        "Congo, Dem. Rep.": 0.42, "Malaysia": 0.20, "Bermuda": 0.80}
g.loc[g["name"].isin(PINY), "yj"] = g.loc[g["name"].isin(PINY), "name"].map(PINY)
SHOW = {"United States": "US", "Congo, Dem. Rep.": "DR Congo"}

rc()
fig, axes = plt.subplots(2, 1, figsize=(9.8, 6.2), dpi=DPI)
fig.subplots_adjust(left=0.022, right=0.978, top=0.925, bottom=0.075, hspace=0.62)

seg_specs = []
for ax, scale in zip(axes, ["linear", "log"]):
    if scale == "linear":
        lo, hi = 0, TOP
        panel = "Linear scale: equal widths are equal dollars"
    else:
        lo, hi = 200, TOP
        ax.set_xscale("log")
        panel = "Log scale: equal widths are equal ratios"
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 1)
    seg_specs.append((ax, [lo, TH[0], TH[1], TH[2], hi]))

    sub = g.assign(_a=g["pop"].apply(area)).sort_values("_a", ascending=False)
    for _, r in sub.iterrows():
        ax.scatter(r["base"], r["yj"], s=area(r["pop"]), facecolor=COL[r["cls"]], alpha=ALPHA,
                   edgecolor="white", lw=0.5, zorder=3, clip_on=False)

    if scale == "log":                       # naming the big economies once is enough
        for _, r in g[g["name"].isin(SIDE)].iterrows():
            side = SIDE[r["name"]]
            rad = np.sqrt(area(r["pop"])) / 2
            if side == "eleven":
                dx, dy, ha, va = -0.72 * rad - 2, 0.72 * rad + 2, "right", "bottom"
            else:
                off = 3 + rad
                dx, dy = (off if side == "right" else -off), 0
                ha, va = ("left" if side == "right" else "right"), "center"
            ax.annotate(SHOW.get(r["name"], r["name"]), (r["base"], r["yj"]), xytext=(dx, dy),
                        textcoords="offset points", ha=ha, va=va, fontsize=NAME_PT,
                        fontweight="bold", color=CAP_INK, zorder=7)
        ax.set_xticks([1175, 4635, 14375, TOP])
        ax.set_xticklabels(["$1,175", "$4,635", "$14,375", "$140,000"])
        ax.minorticks_off()
    else:
        ax.set_xticks([4635, 14375, TOP])
        ax.set_xticklabels(["\n$4,635", "$14,375", "$140,000"])

    ax.set_yticks([])
    for sp in ("top", "right", "left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=5)
    ax.text(0.0, 1.06, panel, transform=ax.transAxes, fontsize=AXIS_PT, fontweight="bold",
            color=INK, va="bottom")

# the four-group bar, with half-character gaps measured in display space
fig.canvas.draw()
half_gap = 0.5 * CAP_PT * fig.dpi / 72
for ax, edges in seg_specs:
    tr = ax.transData
    inv = tr.inverted()
    for k, (a0, a1, grp) in enumerate(zip(edges[:-1], edges[1:], ["L", "LM", "UM", "H"])):
        p0 = tr.transform((a0, 0))[0] + (half_gap / 2 if k > 0 else 0)
        p1 = tr.transform((a1, 0))[0] - (half_gap / 2 if k < 3 else 0)
        ax.plot([inv.transform((p0, 0))[0], inv.transform((p1, 0))[0]], [0.015, 0.015],
                color=COL[grp], lw=BAND_LW, solid_capstyle="butt", zorder=2, clip_on=False)

fig.savefig("_plot13.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot13.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
