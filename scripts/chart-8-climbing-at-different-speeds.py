"""chart-8-climbing-at-different-speeds.py

Self-contained: the Moving Frontiers house style, the data and the chart in one
file. Run it with matplotlib, numpy and Pillow available:

    python chart-8-climbing-at-different-speeds.py

It writes chart-8-climbing-at-different-speeds.png and
chart-8-climbing-at-different-speeds.csv into the working directory.

PROVENANCE, FROZEN VINTAGE. Nothing is read from disk or the network.
  Thresholds 1990-2025 : World Bank OGHIST, 1 July 2026 release, Thresholds
                         worksheet, official values as published, no smoothing.
  Classifications      : World Bank OGHIST, 1 July 2026, Country Analytical History.
  GNI per capita       : World Bank WDI, July 2026 vintage, Atlas method, current US$.
  Vintage freeze date  : 1 July 2026. The chart is pinned to this vintage; do not
                         swap the embedded table for a live API call.

G_CN, G_IN and DRIFT are the decade-median annual rates inherited from the shared
upstream projection pipeline that also drives the shares chart, and are embedded
here already resolved. They are not used to build the series, which arrive
already projected in the table below; they appear in the note, and the assertions
below keep the note honest if anyone edits them.

WHAT CHANGED FROM THE EARLIER CUT OF THIS CHART
-----------------------------------------------
The plot is the same: four solid threshold bands, two lines with contrasting
outlines, dashed beyond 2025, and dots at each crossing placed by a small solver
that rejects any anchor overlapping a curve or an earlier label. What has been
replaced is the furniture. The hand-rolled PIL title band, the seven-line
figtext caption with its renderer arithmetic, and the hand-placed watermark with
its 95-pixel offset are gone; the title, subtitle, caption and watermark now go
through compose(), so this chart carries the same gaps and border as the rest of
the pack and verify() checks them. The chart also now reads one embedded table
rather than three parallel dicts, so the CSV it writes and the series it plots
cannot drift apart.
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
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
# DATA: GNI per capita and the official thresholds, 1990 to 2050
# ======================================================================

RAW = """\
year,status,china_gni_pc,china_class,china_population_millions,india_gni_pc,india_class,india_population_millions,threshold_lic_lmic,threshold_lmic_umic,threshold_umic_hic
1990,actual,330,L,1135.18,390,L,864.97,610,2465,7620
1991,actual,360,L,1150.78,350,L,883.93,635,2555,7910
1992,actual,400,L,1164.97,350,L,902.96,675,2695,8355
1993,actual,420,L,1178.44,330,L,922.12,695,2785,8625
1994,actual,470,L,1191.84,340,L,941.16,725,2895,8955
1995,actual,540,L,1204.86,370,L,960.3,765,3035,9385
1996,actual,660,L,1217.55,400,L,979.68,785,3115,9645
1997,actual,760,LM,1230.08,410,L,999.13,785,3125,9655
1998,actual,800,L,1241.94,410,L,1018.67,760,3030,9360
1999,actual,860,LM,1252.73,440,L,1038.23,755,2995,9265
2000,actual,950,LM,1262.64,440,L,1057.92,755,2995,9265
2001,actual,1020,LM,1271.85,450,L,1077.9,745,2975,9205
2002,actual,1130,LM,1280.4,460,L,1097.6,735,2935,9075
2003,actual,1300,LM,1288.4,510,L,1116.8,765,3035,9385
2004,actual,1530,LM,1296.08,610,L,1135.99,825,3255,10065
2005,actual,1790,LM,1303.72,700,L,1154.68,875,3465,10725
2006,actual,2090,LM,1311.02,780,L,1172.88,905,3595,11115
2007,actual,2550,LM,1317.88,910,LM,1190.68,935,3705,11455
2008,actual,3140,LM,1324.66,990,LM,1207.93,975,3855,11905
2009,actual,3740,LM,1331.26,1110,LM,1225.52,995,3945,12195
2010,actual,4410,UM,1337.7,1210,LM,1243.48,1005,3975,12275
2011,actual,5130,UM,1345.04,1350,LM,1261.22,1025,4035,12475
2012,actual,6010,UM,1354.19,1460,LM,1278.67,1035,4085,12615
2013,actual,6860,UM,1363.24,1500,LM,1295.83,1045,4125,12745
2014,actual,7600,UM,1371.86,1540,LM,1312.28,1045,4125,12735
2015,actual,8040,UM,1379.86,1580,LM,1328.02,1025,4035,12475
2016,actual,8360,UM,1387.79,1670,LM,1343.94,1005,3955,12235
2017,actual,8830,UM,1396.22,1790,LM,1359.66,995,3895,12055
2018,actual,9720,UM,1402.76,1970,LM,1374.66,1025,3995,12375
2019,actual,10510,UM,1407.74,2070,LM,1389.03,1035,4045,12535
2020,actual,10740,UM,1411.1,1900,LM,1402.62,1045,4095,12695
2021,actual,12220,UM,1412.36,2170,LM,1414.2,1085,4255,13205
2022,actual,13170,UM,1412.18,2360,LM,1425.42,1135,4465,13845
2023,actual,13750,UM,1410.71,2490,LM,1438.07,1145,4515,14005
2024,actual,13660,UM,1408.98,2550,LM,1450.94,1135,4495,13935
2025,actual,14230,UM,1406.58,2760,LM,1463.87,1175,4635,14375
2026,projected,14943,H,1403.42,2938,LM,1476.63,1190,4693,14554
2027,projected,15692,H,1400.21,3127,LM,1489.16,1204,4751,14735
2028,projected,16479,H,1396.69,3328,LM,1501.43,1219,4810,14918
2029,projected,17305,H,1392.86,3543,LM,1513.42,1235,4870,15104
2030,projected,18173,H,1388.76,3771,LM,1525.14,1250,4931,15292
2031,projected,19084,H,1384.39,4014,LM,1536.54,1265,4992,15482
2032,projected,20040,H,1379.73,4272,LM,1547.61,1281,5054,15674
2033,projected,21045,H,1374.8,4548,LM,1558.32,1297,5117,15869
2034,projected,22100,H,1369.62,4840,LM,1568.69,1313,5181,16067
2035,projected,23208,H,1364.2,5152,LM,1578.69,1330,5245,16267
2036,projected,24371,H,1358.56,5484,UM,1588.33,1346,5310,16469
2037,projected,25593,H,1352.68,5837,UM,1597.54,1363,5376,16674
2038,projected,26876,H,1346.62,6213,UM,1606.3,1380,5443,16881
2039,projected,28223,H,1340.33,6613,UM,1614.64,1397,5511,17091
2040,projected,29638,H,1333.8,7039,UM,1622.58,1414,5579,17304
2041,projected,31124,H,1327.02,7493,UM,1630.12,1432,5649,17519
2042,projected,32684,H,1319.98,7975,UM,1637.24,1450,5719,17737
2043,projected,34322,H,1312.71,8489,UM,1643.92,1468,5790,17958
2044,projected,36043,H,1305.19,9036,UM,1650.19,1486,5862,18181
2045,projected,37850,H,1297.34,9618,UM,1656.07,1505,5935,18407
2046,projected,39747,H,1289.1,10237,UM,1661.55,1523,6009,18636
2047,projected,41740,H,1280.46,10897,UM,1666.63,1542,6084,18868
2048,projected,43832,H,1271.4,11599,UM,1671.31,1561,6159,19103
2049,projected,46030,H,1261.85,12346,UM,1675.62,1581,6236,19341
2050,projected,48337,H,1251.82,13141,UM,1679.59,1601,6314,19581
"""

STEM = "chart-8-climbing-at-different-speeds"
df = pd.read_csv(io.StringIO(RAW))
df.to_csv(STEM + ".csv", index=False)

YR = df["year"].tolist()
cn = dict(zip(df["year"], df["china_gni_pc"]))
ind = dict(zip(df["year"], df["india_gni_pc"]))
th = {r.year: [r.threshold_lic_lmic, r.threshold_lmic_umic, r.threshold_umic_hic]
      for r in df.itertuples()}
HY = df.loc[df["status"] == "actual", "year"].tolist()
PY = [HY[-1]] + df.loc[df["status"] == "projected", "year"].tolist()

DRIFT = 0.012440                 # threshold drift beyond 2025, quoted in the note
G_CN = 0.0501297896843995        # China's decade-median growth, quoted in the note
G_IN = 0.0644091563708026        # India's decade-median growth, quoted in the note
assert round(DRIFT * 100, 3) == 1.244, "the note states a 1.244 percent threshold drift"
assert round(G_CN * 100, 1) == 5.0, "the note states 5.0 percent for China"
assert round(G_IN * 100, 1) == 6.4, "the note states 6.4 percent for India"

tL = np.array([th[y][0] for y in YR])
tM = np.array([th[y][1] for y in YR])
tU = np.array([th[y][2] for y in YR])

# ======================================================================
# CHART
# ======================================================================

BAND = {"L": RED, "LM": GOLD, "UM": GREEN, "H": BLUE}
LINE_CN, LINE_IN = "#FFFFFF", "#141414"     # chosen to read on every solid band
PAPER = "#FFFFFF"
PE_W = [pe.Stroke(linewidth=6.4, foreground=LINE_IN), pe.Normal()]   # white line, dark outline
PE_K = [pe.Stroke(linewidth=6.0, foreground=PAPER), pe.Normal()]     # dark line, white outline

YLO, YHI = 190, 62000
SPLIT = 2025.5

TITLE = "Countries climb at different speeds"
SUBTITLE = ("China and India's GNI per capita against the World Bank's moving income thresholds, "
            "1990 to 2050")
SOURCE = ("World Bank OGHIST (1 July 2026), Thresholds worksheet for the official thresholds and "
          "Country Analytical History for the classifications, both 1990 to 2025, and WDI GNI per "
          "capita, Atlas method (July 2026 vintage), with the author's calculations and "
          "projections.")
NOTE = ("GNI per capita is plotted on a log scale. Band boundaries are the official thresholds "
        "year by year as published, with no smoothing, extended beyond 2025 at 1.244 percent a "
        "year, the median annual increase of the past decade. Solid lines are actual GNI per "
        "capita through 2025, dashed lines are projected at each economy's decade-median growth, "
        "5.0 percent for China and 6.4 percent for India. Circles mark each economy's crossings, "
        "dated by the classification year; each is announced the following July.")

rc()
fig, ax = plt.subplots(figsize=(8.6, 6.8), dpi=DPI)
fig.subplots_adjust(left=0.092, right=0.858, top=0.985, bottom=0.072)

ax.fill_between(YR, YLO, tL, color=BAND["L"], zorder=0)
ax.fill_between(YR, tL, tM, color=BAND["LM"], zorder=0)
ax.fill_between(YR, tM, tU, color=BAND["UM"], zorder=0)
ax.fill_between(YR, tU, YHI, color=BAND["H"], zorder=0)
for t in (tL, tM, tU):
    ax.plot(YR, t, ls="--", lw=1.5, color="white", alpha=0.85, zorder=2)
ax.axvline(SPLIT, ls=":", lw=1.8, color="white", zorder=3)

ax.plot(HY, [cn[y] for y in HY], color=LINE_CN, lw=3.4, zorder=5, solid_capstyle="round",
        path_effects=PE_W)
ax.plot(PY, [cn[y] for y in PY], color=LINE_CN, lw=3.0, ls=(0, (5, 2.6)), zorder=5,
        path_effects=PE_W)
ax.plot(HY, [ind[y] for y in HY], color=LINE_IN, lw=3.4, zorder=5, solid_capstyle="round",
        path_effects=PE_K)
ax.plot(PY, [ind[y] for y in PY], color=LINE_IN, lw=3.0, ls=(0, (5, 2.6)), zorder=5,
        path_effects=PE_K)

ax.set_yscale("log")
ax.set_ylim(YLO, YHI)
ax.set_xlim(1989.6, 2050.5)
ticks = [200, 500, 1000, 2000, 5000, 10000, 20000, 40000]
ax.set_yticks(ticks)
ax.set_yticklabels(["${:,}".format(t) for t in ticks])
ax.minorticks_off()
ax.set_xticks([1990, 2000, 2010, 2020, 2030, 2040, 2050])
style_ax(ax)
fig.canvas.draw()
REN = fig.canvas.get_renderer()


def dot(x, y, col):
    ax.plot([x], [y], "o", mfc=col, mec=LINE_IN if col == PAPER else PAPER, mew=2.8, ms=12,
            zorder=7)


# ---- label solver: take the first anchor that clears every curve and every label placed ----
CURVES = [lambda x: cn[x], lambda x: ind[x],
          lambda x: th[x][0], lambda x: th[x][1], lambda x: th[x][2]]
placed = []


def databox(t):
    bb = t.get_window_extent(REN)
    inv = ax.transData.inverted()
    (x0, y0) = inv.transform((bb.x0, bb.y0))
    (x1, y1) = inv.transform((bb.x1, bb.y1))
    return x0, x1, min(y0, y1), max(y0, y1)


def clear(box, pad=0.030):
    x0, x1, ylo, yhi = box
    if x0 < 1989.8 or x1 > 2050.3:
        return False
    lo, hi = ylo / 10 ** pad, yhi * 10 ** pad
    xs = [x for x in YR if x0 - 0.7 <= x <= x1 + 0.7]
    for f in CURVES:
        for x in xs:
            if lo <= f(x) <= hi:
                return False
    for p in placed:
        if x0 < p[1] + 0.4 and p[0] < x1 + 0.4 and ylo / 10 ** 0.012 < p[3] and p[2] < yhi * 10 ** 0.012:
            return False
    return True


def place(lab, cands, col):
    fc, tc = (LINE_IN, PAPER) if col == PAPER else (PAPER, LINE_IN)
    for (lx, ly, ha, va) in cands:
        t = ax.text(lx, ly, lab, fontsize=AXIS_PT, fontweight="bold", color=tc, ha=ha, va=va,
                    zorder=8, linespacing=1.3,
                    bbox=dict(boxstyle="round,pad=0.26", facecolor=fc, edgecolor="none"))
        b = databox(t)
        if clear(b):
            placed.append(b)
            return
        t.remove()
    t = ax.text(cands[0][0], cands[0][1], lab, fontsize=AXIS_PT, fontweight="bold", color=tc,
                ha=cands[0][2], va=cands[0][3], zorder=8, linespacing=1.3,
                bbox=dict(boxstyle="round,pad=0.26", facecolor=fc, edgecolor="none"))
    placed.append(databox(t))
    print("  !! no clear slot for", lab)


JOBS = [
    ("2026", 2026, cn[2026], LINE_CN,
     [(2024.6, y, "right", "center") for y in (21500, 24000, 19500)] +
     [(2027.8, y, "left", "center") for y in (11800, 11000)]),
    ("2010", 2010, cn[2010], LINE_CN,
     [(2008.8, y, "right", "center") for y in (6100, 6700, 5600)] +
     [(2011.8, y, "left", "center") for y in (3250, 3000)]),
    ("1999", 1999, cn[1999], LINE_CN,
     [(1997.6, y, "right", "center") for y in (1200, 1330, 1090)] +
     [(2000.9, y, "left", "center") for y in (610, 560)]),
    ("2036", 2036, ind[2036], LINE_IN,
     [(2037.8, y, "left", "center") for y in (4100, 3800, 4450)] +
     [(2034.2, y, "right", "center") for y in (7400, 8100)]),
    ("2007", 2007, ind[2007], LINE_IN,
     [(2008.8, y, "left", "center") for y in (630, 580, 690)] +
     [(2005.2, y, "right", "center") for y in (630, 580)]),
]
for lab, dx, dy, col, cands in JOBS:
    dot(dx, dy, col)
    place(lab, cands, col)

place("China", [(2043.5, y, "right", "center") for y in (44000, 48500, 40000)] +
      [(2038, y, "right", "center") for y in (37000, 41000)], LINE_CN)
place("India", [(2046.5, y, "right", "center") for y in (14600, 13600, 15600, 16600)] +
      [(2043, y, "right", "center") for y in (14600, 13600, 16000)] +
      [(2049.8, y, "right", "center") for y in (17500, 16000)], LINE_IN)

# band names outside the axes on the right, centred in each band at 2050
BANDLAB = [("HIGH\nINCOME", np.sqrt(th[2050][2] * YHI), BLUE),
           ("UPPER-\nMIDDLE", np.sqrt(th[2050][1] * th[2050][2]), GREEN),
           ("LOWER-\nMIDDLE", np.sqrt(th[2050][0] * th[2050][1]), "#B8860B"),
           ("LOW\nINCOME", np.sqrt(YLO * th[2050][0]), RED)]
for lab, yv, cc in BANDLAB:
    ax.text(1.012, yv, lab, transform=ax.get_yaxis_transform(), fontsize=LABEL_PT,
            fontweight="bold", color=cc, ha="left", va="center", linespacing=1.25,
            clip_on=False, zorder=6)

ax.text(SPLIT + 0.9, YLO * 1.12, "projected", fontsize=LABEL_PT, color="white",
        fontweight="bold", ha="left", va="bottom", zorder=6)
ax.text(SPLIT - 0.9, YLO * 1.12, "actual", fontsize=LABEL_PT, color="white",
        fontweight="bold", ha="right", va="bottom", zorder=6)

fig.savefig("_plot8.png", dpi=DPI, facecolor="white", bbox_inches="tight")
compose("_plot8.png", STEM + ".png", TITLE, SUBTITLE, SOURCE, NOTE)
print("wrote", STEM + ".png", "and", STEM + ".csv")
