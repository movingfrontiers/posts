"""chart-1-Maddison.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file. Run it with
matplotlib, numpy, pandas and Pillow available:

    python chart-1-Maddison.py

It writes chart-1-Maddison.png and chart-1-Maddison.csv into the working directory.

GDP per capita of seven world regions as a percent of the Western offshoots (US, Canada, Australia
and New Zealand), 1820 to 2022, with the 40 percent line.

DATA
Maddison Project Database 2023 (Bolt and van Zanden) regional aggregates, real GDP per capita in
constant 2011 international dollars, as exported by Our World in Data. Embedded below.
"""
import io, os
import numpy as np
import pandas as pd

# ======================================================================
# HOUSE STYLE (inlined)
# ======================================================================
# ==== Moving Frontiers house style (house_style.py) ====
"""Moving Frontiers house style.

Set in October 2026 with the "Drivers of social progress" chart. Plot in matplotlib with the
helpers below, then compose() lays out title, unit line, explainer, plot, caption and wordmark on a fixed
canvas in PIL, fitting the plot height so everything fills the frame, and verify() asserts margins and
gaps from the rendered pixels.

Design rules
- Two typefaces: Arial (Liberation Sans) for title, unit line, explainer, axis ticks, axis title and caption;
  Calibri (Carlito) for category labels, data values and legends.
- Navy for the main series, red for the contrast series; light navy-grey bands to group or highlight rows.
- No gridlines. Dotted reference line at zero. Bottom axis only, outward ticks. No left spine.
- Wordmark "Moving Frontiers" in bold navy, right-aligned, ink bottom level with the caption's last line
  The caption wraps in the column to its left.
- Every gap is measured ink to ink; 150 px of white margin on all sides.
Canvas defaults to LinkedIn 4:5 portrait (2160 x 2700); pass W, H to compose() for other formats.
"""
import os, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory
from PIL import Image, ImageDraw, ImageFont

# ---------------- canvas and spacing (px) ----------------
W, H = 2160, 2700                 # LinkedIn 4:5 portrait
M = 150                           # white margin on every side
DPI = 200; PX = 72/DPI            # points per pixel, for matplotlib font sizes
GAP_TITLE_UNIT = 34               # title ink to unit-line ink
GAP_UNIT_EXPL = 22                # unit line to explainer
GAP_HEAD_PLOT = 70                # last header line to highest plot ink
GAP_PLOT_CAP = 70                 # lowest plot ink to caption ink (absorbs the few px of fitting residual)
GAP_CAP_MARK = 90                 # horizontal clearance between caption column and wordmark

# ---------------- colours ----------------
NAVY, RED = '#0B2265', '#D0412F'          # main and contrast series
SKY, GOLD = '#5B8FCC', '#C9962B'          # third and fourth series, when needed
INK, GREY_TXT, LABEL = '#111111', '#555555', '#333333'
BAND = '#E6EAF2'                          # light navy-grey row band
TITLE_RGB, UNIT_RGB, EXPL_RGB, CAP_RGB = (17,17,17), (34,34,34), (95,95,95), (95,95,95)
def palette(n):
    assert 1 <= n <= 4, n
    return [NAVY, RED, SKY, GOLD][:n]

# ---------------- type sizes (px) ----------------
T_TITLE, T_UNIT, T_EXPL, T_CAP, T_MARK = 92, 54, 42, 37, 66      # PIL layer
T_HDR, T_LAB, T_VAL, T_TICK, T_XLAB, T_LEG = 54, 46, 47, 42, 46, 46   # matplotlib layer
LS_TITLE, LS_UNIT, LS_EXPL, LS_CAP = 1.18, 1.3, 1.42, 1.42           # line spacing, multiples of size
MARK = 'Moving Frontiers'

# ---------------- fonts ----------------
# Arial and Calibri, or their metric-compatible open twins (Liberation Sans, Carlito), searched
# in the usual Linux, macOS and Windows font folders. If neither is installed the chart still
# renders in DejaVu Sans, which ships with matplotlib, though line breaks may then differ.
FONT_DIRS = ['/usr/share/fonts/truetype/liberation/', '/usr/share/fonts/truetype/crosextra/',
             '/Library/Fonts/', '/System/Library/Fonts/Supplemental/', os.path.expanduser('~/Library/Fonts/'),
             'C:/Windows/Fonts/']
def _find(names, bold=False):
    for d in FONT_DIRS:
        for n in names:
            if os.path.exists(os.path.join(d, n)): return os.path.join(d, n)
    hits = {os.path.basename(f): f for f in fm.findSystemFonts()}
    for n in names:
        if n in hits: return hits[n]
    return os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf', 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
F_ARIAL   = _find(['LiberationSans-Regular.ttf', 'Arial.ttf', 'arial.ttf'])
F_ARIAL_B = _find(['LiberationSans-Bold.ttf', 'Arial Bold.ttf', 'arialbd.ttf'], bold=True)
F_CAL     = _find(['Carlito-Regular.ttf', 'Calibri.ttf', 'calibri.ttf'])
F_CAL_B   = _find(['Carlito-Bold.ttf', 'Calibri Bold.ttf', 'calibrib.ttf'], bold=True)
for _f in (F_ARIAL, F_ARIAL_B, F_CAL, F_CAL_B): fm.fontManager.addfont(_f)
P_ARIAL, P_ARIAL_B = fm.FontProperties(fname=F_ARIAL), fm.FontProperties(fname=F_ARIAL_B)
P_CAL, P_CAL_B = fm.FontProperties(fname=F_CAL), fm.FontProperties(fname=F_CAL_B)
def cal(px, bold=False):   return dict(fontproperties=P_CAL_B if bold else P_CAL, fontsize=px*PX)
def arial(px, bold=False): return dict(fontproperties=P_ARIAL_B if bold else P_ARIAL, fontsize=px*PX)

# ---------------- matplotlib helpers ----------------
def new_fig(w_px, h_px):
    return plt.figure(figsize=(w_px/DPI, h_px/DPI), dpi=DPI)

def style_axes(ax, axis='x', xlabel=None):
    """Axis treatment: bottom spine only, outward ticks, Arial tick labels, bold Arial axis title.
    axis='x' for horizontal bars (value axis at the bottom); axis='y' keeps a left value axis instead."""
    for sp in ('top', 'right', 'left') if axis == 'x' else ('top', 'right'):
        ax.spines[sp].set_visible(False)
    for sp in ('bottom',) if axis == 'x' else ('bottom', 'left'):
        ax.spines[sp].set_color(INK); ax.spines[sp].set_linewidth(1.6)
    ax.grid(False)
    ax.tick_params(axis='both', direction='out', length=12, width=1.6, color=INK, pad=10)
    if axis == 'x': ax.set_yticks([])
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_fontproperties(P_ARIAL); t.set_fontsize(T_TICK*PX); t.set_color('#222')
    if xlabel: ax.set_xlabel(xlabel, color=INK, labelpad=16, **arial(T_XLAB, bold=True))

def set_ticks(ax, ticks, axis='x', fmt='{:g}'):
    """Set ticks with hyphen-minus labels and re-apply tick fonts."""
    (ax.set_xticks if axis == 'x' else ax.set_yticks)(ticks)
    (ax.set_xticklabels if axis == 'x' else ax.set_yticklabels)([fmt.format(v) for v in ticks])
    for t in (ax.get_xticklabels() if axis == 'x' else ax.get_yticklabels()):
        t.set_fontproperties(P_ARIAL); t.set_fontsize(T_TICK*PX); t.set_color('#222')

def zero_line(ax, at=0, axis='x', span=None):
    """Dotted reference line. span=(lo, hi) in data units limits its length; use it when the
    line would otherwise be the outermost ink, since where the last dot falls shifts the plot's ink edge
    by up to a dot period and stops compose() from fitting the plot height."""
    kw = dict(colors=INK, lw=2.6, linestyles=[(0, (1, 1.6))], zorder=4)
    if span is None:
        lo, hi = (ax.get_ylim() if axis == 'x' else ax.get_xlim())
    else:
        lo, hi = span
    (ax.vlines if axis == 'x' else ax.hlines)(at, lo, hi, **kw)

def band(fig, ax, y, half=0.5, color=BAND):
    """Full-width shaded band behind row y (data units on ax, full figure width).
    Puts the axes above the band and makes its background transparent so bars stay visible."""
    tr = blended_transform_factory(fig.transFigure, ax.transData)
    fig.patches.append(Rectangle((0, y-half), 1, 2*half, transform=tr, facecolor=color, edgecolor='none', zorder=0))
    ax.set_zorder(1); ax.patch.set_alpha(0)

def _ink(im):
    arr = np.array(im.convert('L')); ys, xs = np.where(arr < 250); return xs.min(), ys.min(), xs.max(), ys.max()

def render(fig, path='_mf_plot.png'):
    """Save the figure and return its ink-cropped PIL image."""
    fig.savefig(path, dpi=DPI, facecolor='white'); plt.close(fig)
    P = Image.open(path).convert('RGB'); x0, y0, x1, y1 = _ink(P); P = P.crop((x0, y0, x1+1, y1+1))
    os.remove(path); return P

# ---------------- PIL layout ----------------
def _wrap(text, f, width):
    out = []
    for para in text.split('\n'):
        cur = ''
        for w in para.split():
            t = (cur+' '+w).strip(); b = f.getbbox(t, anchor='la')
            if b[2]-b[0] <= width: cur = t
            else: out.append(cur); cur = w
        out.append(cur)
    return out

def _block(text, f, ls, width, col):
    L = _wrap(text, f, width); lh = round(f.size*ls); top = bot = None
    for i, ln in enumerate(L):
        b = f.getbbox(ln, anchor='la'); t, bo = i*lh+b[1], i*lh+b[3]
        top = t if top is None else min(top, t); bot = bo if bot is None else max(bot, bo)
    return dict(lines=L, font=f, col=col, lh=lh, top=top, h=bot-top)

def compose(plot_fn, title, unit, caption, out, expl=None, W=W, H=H, title_lines=None, mark=MARK):
    """Lay out a finished chart on a fixed W x H canvas and save it to `out`.
    plot_fn(w_px, h_px) returns a matplotlib figure of that size; compose() searches h_px until the plot's
    ink height fills what the header and caption leave, takes the closest fit not above the target, and
    gives the leftover pixels to the plot-caption gap. Returns the PIL image."""
    BW = W - 2*M
    FT, FU = ImageFont.truetype(F_ARIAL_B, T_TITLE), ImageFont.truetype(F_ARIAL, T_UNIT)
    FE, FC, FM = ImageFont.truetype(F_ARIAL, T_EXPL), ImageFont.truetype(F_ARIAL, T_CAP), ImageFont.truetype(F_ARIAL_B, T_MARK)
    mb = FM.getbbox(mark, anchor='la'); cap_w = BW - (mb[2]-mb[0]) - GAP_CAP_MARK
    head = [(_block(title, FT, LS_TITLE, BW, TITLE_RGB), 0), (_block(unit, FU, LS_UNIT, BW, UNIT_RGB), GAP_TITLE_UNIT)]
    if expl: head.append((_block(expl, FE, LS_EXPL, BW, EXPL_RGB), GAP_UNIT_EXPL))
    cap = _block(caption, FC, LS_CAP, cap_w, CAP_RGB)
    if title_lines: assert len(head[0][0]['lines']) == title_lines, head[0][0]['lines']
    target = H - 2*M - sum(b['h'] + g for b, g in head) - GAP_HEAD_PLOT - GAP_PLOT_CAP - cap['h']

    best = None; h = target + 20.0; step = 1.0
    for _ in range(40):
        P = render(plot_fn(BW, h))
        assert P.width <= BW, f'plot ink {P.width}px wider than content width {BW}px'
        if P.height <= target and (best is None or P.height > best.height): best = P
        if P.height == target: break
        if P.height > target: step *= 0.6          # overshot: approach in smaller steps
        h += 0.6*(target - P.height) + (0.4*step if P.height < target else -0.4*step)
    P = best; assert P is not None and target - P.height <= 8, (None if P is None else P.height, target)
    gap_cap = GAP_PLOT_CAP + target - P.height

    C = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(C)
    def draw(b, y):
        for i, ln in enumerate(b['lines']):
            dr.text((M - b['font'].getbbox(ln, anchor='la')[0], y - b['top'] + i*b['lh']), ln,
                    font=b['font'], fill=b['col'], anchor='la')
        return y + b['h']
    y = M
    for b, g in head: y = draw(b, y + g)
    plot_y = y + GAP_HEAD_PLOT; C.paste(P, (M, plot_y))
    cap_bot = draw(cap, plot_y + P.height + gap_cap)
    dr.text((W - M - mb[2], cap_bot - mb[3]), mark, font=FM, fill=NAVY, anchor='la')
    verify(C, plot_y, P.height, cap_w, gap_cap)
    C.save(out, optimize=True); return C

def verify(C, plot_y, plot_h, cap_w, gap_cap):
    """Assert margins and gaps from the rendered pixels."""
    W, H = C.size
    A = np.array(C.convert('L')) < 250; rws = np.where(A.any(axis=1))[0]; cols = np.where(A.any(axis=0))[0]
    assert rws.min() == M and H-1-rws.max() == M, ('top/bottom margin', rws.min(), H-1-rws.max())
    assert cols.min() == M and W-1-cols.max() >= M-1, ('left/right margin', cols.min(), W-1-cols.max())
    runs = np.split(rws, np.where(np.diff(rws) > 1)[0]+1); pb = plot_y + plot_h - 1
    head_bot = max(r[-1] for r in runs if r[-1] < plot_y)
    capcol = np.where(A[:, M:M+cap_w].any(axis=1))[0]; cap_top = capcol[capcol > pb].min()
    assert plot_y - head_bot - 1 == GAP_HEAD_PLOT, ('header-plot gap', plot_y - head_bot - 1)
    assert cap_top - pb - 1 == gap_cap, ('plot-caption gap', cap_top - pb - 1)
# ==== end of house style ====

import sys
mf = sys.modules[__name__]        # the chart code below refers to the style as mf.*

# Pack settings shared by the three charts
mf.T_TITLE = 66                    # title size: the largest at which the pack's titles fit two lines
mf.T_MARK = round(66*0.7)          # wordmark 30% smaller than the house size
mf.M = round(150*0.3)              # white margin 70% smaller than the house 150 px
URL = 'movingfrontiers.substack.com/ai-divergence'

# One region palette for charts 1 and 2, from the house colours (navy, sky, red, gold) and their tints
REGCOL = {"Western offshoots":"#0B2265","Western Europe":"#5B8FCC","Eastern Europe":"#9DBCE3","East Asia":"#D0412F",
          "Middle East and North Africa":"#E9998A","Latin America":"#8C6A1C","South and South East Asia":"#C9962B",
          "Sub Saharan Africa":"#4A4A4A","Pacific islands (no Maddison region)":"#C8C8C8"}

# ======================================================================
# DATA
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

STEM = "chart-1-Maddison"
levels = pd.read_csv(io.StringIO(RAW), index_col="Year")
rel = levels.div(levels["Western offshoots"], axis=0) * 100
tidy = (levels.stack().rename("gdp_per_capita_2011_intl_usd").to_frame()
        .join(rel.stack().rename("pct_of_western_offshoots").to_frame()))
tidy.index.names = ["year", "region"]
tidy.round(4).to_csv(STEM + ".csv")

# ======================================================================
# CHART
# ======================================================================
SERIES = ["Western Europe","East Asia","Eastern Europe","Middle East and North Africa","Latin America",
          "South and South East Asia","Sub Saharan Africa"]
LABEL = {"Western offshoots":"Western offshoots", "Middle East and North Africa":"Middle East & N. Africa","South and South East Asia":"South & South East Asia",
         "Sub Saharan Africa":"Sub-Saharan Africa"}
COL = {k: REGCOL[k] for k in SERIES + ['Western offshoots']}
YMAX = 104
THRESHOLD, X_END, LABEL_X = 40, 2022, 2025

def declutter(points, sep):
    """Nudge crowded end labels apart, downwards only, so none crosses the 40 percent line."""
    order = sorted(points, key=lambda t: t[0], reverse=True); ys = [y for y, _ in order]
    for i in range(1, len(ys)): ys[i] = min(ys[i], ys[i-1] - sep)
    return [(y, lab) for y, (_, lab) in zip(ys, order)]

def plot(w, h):
    fig = mf.new_fig(w, h)
    bot = 120/h
    ax = fig.add_axes([0.075, bot, 0.72, 0.985-bot])
    ax.axhspan(0, THRESHOLD, color=mf.BAND, zorder=0, lw=0)
    ends = []
    for name in SERIES:
        s = rel[name].dropna()
        ax.plot(s.index, s.values, color=COL[name], lw=3.2, solid_capstyle='round', zorder=3)
        ends.append((s.values[-1], name))
    ax.plot([1820, X_END], [100, 100], color=COL['Western offshoots'], lw=3.2, solid_capstyle='round', zorder=3)
    ends.append((100.0, 'Western offshoots'))
    ax.set_xlim(1820, X_END); ax.set_ylim(0, YMAX)
    mf.style_axes(ax, axis='y')
    mf.set_ticks(ax, [1820, 1850, 1900, 1950, 2000, X_END], 'x', fmt='{:d}')
    mf.set_ticks(ax, [0, 20, 40, 60, 80, 100], 'y')
    ax.get_yticklabels()[2].set_fontproperties(mf.P_ARIAL_B); ax.get_yticklabels()[2].set_fontsize(mf.T_TICK*mf.PX)
    mf.zero_line(ax, at=THRESHOLD, axis='y', span=(1820, X_END))
    px_per_unit = (0.985-bot)*h/YMAX; sep = 52/px_per_unit
    labs = [ax.text(LABEL_X, y, LABEL.get(name, name), color=COL[name], va='center', ha='left', clip_on=False, **mf.cal(mf.T_LAB, bold=True))
            for y, name in declutter(ends, sep)]
    for _ in range(4):                      # widen the plot as far as the longest end label allows
        fig.canvas.draw(); r = max(t.get_window_extent().x1 for t in labs)/w
        if abs(r - 0.995) < 0.002: break
        pos = ax.get_position(); ax.set_position([pos.x0, pos.y0, pos.width + (0.995 - r)/1.03, pos.height])
    return fig

TITLE = "Despite convergence, 90% of the world has lived in regions below 40% of frontier income over the last 200 years"
UNIT = "GDP per capita as percent of the Western offshoots (US, Canada, Australia and New Zealand), 1820 to 2022"
CAP = ("Source: Bolt and van Zanden, Maddison Project Database 2023.\n"
       "Note: Constant 2011 international dollars. 90% refers to the share of the population in 2022 outside of "
       "Western Europe and the Western offshoots.\n" + URL)
mf.compose(plot, TITLE, UNIT, CAP, STEM + ".png", W=2160, H=2160, title_lines=2)
print("wrote", STEM + ".png and", STEM + ".csv")
