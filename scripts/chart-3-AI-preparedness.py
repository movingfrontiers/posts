"""chart-3-AI-preparedness.py

Self-contained: the Moving Frontiers house style, the data and the chart in one file. Run it with
matplotlib, numpy, pandas and Pillow available:

    python chart-3-AI-preparedness.py

It writes chart-3-AI-preparedness.png and chart-3-AI-preparedness.csv into the working directory.

One bubble per economy: the AI Preparedness Index (vertical) by World Bank income group in 2023
(columns), bubble area proportional to 2023 population, with each group's population-weighted mean.

DATA
AI Preparedness Index scores for 164 economies, the World Bank income group held in 2023 (OGHIST),
and 2023 population in millions (WDI SP.POP.TOTL), joined on ISO3 code. Embedded below.
"""
import io, os
import numpy as np
import pandas as pd

import matplotlib.patheffects as pe
from matplotlib.colors import to_rgba

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

# ======================================================================
# DATA
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

STEM = "chart-3-AI-preparedness"
df = pd.read_csv(io.StringIO(RAW))
df.to_csv(STEM + ".csv", index=False)

# ======================================================================
# CHART
# ======================================================================
GROUPS = [("H", "High\nincome", mf.NAVY), ("UM", "Upper-middle\nincome", mf.SKY),
          ("LM", "Lower-middle\nincome", mf.GOLD), ("L", "Low\nincome", mf.RED)]
S_PER_MILLION = 4.6; FACE_ALPHA = 0.72
LEGEND_POPS = [1, 10, 100, 1000]; LABEL_POP = 50; LABEL_TAIL = 3; BAR_LW = 3.0
XLIM = (-0.58, 3.58); YLIM = (0.13, 0.85)
CODE_PX = 34                            # ISO3 codes, Calibri
LEG_PX = 300                            # height of the legend strip
ANGLES = [0, 180, 90, 270, 45, 135, 315, 225]

def pack(xc, ys, sizes, xin, yin, span=0.495, step=0.005, tighten=(1.45, 0.88)):
    """Largest first, each bubble takes the smallest offset from the column centre that clears those placed."""
    r = np.sqrt(np.asarray(sizes)/np.pi)/72.0; out = np.full(len(ys), np.nan); placed = []
    def try_place(i, t):
        for d in np.arange(0, span, step):
            for cand in ((xc,) if d == 0 else (xc+d, xc-d)):
                if all(((cand-px)*xin)**2 + ((ys[i]-py)*yin)**2 >= (t*(r[i]+pr))**2 for px, py, pr in placed):
                    return cand
        return None
    leftover = []
    for i in np.argsort(-np.asarray(sizes)):
        c = try_place(i, tighten[0])
        if c is None: leftover.append(i)
        else: out[i] = c; placed.append((c, ys[i], r[i]))
    for i in leftover:
        c = try_place(i, tighten[1]); out[i] = xc if c is None else c; placed.append((out[i], ys[i], r[i]))
    return out

def place_labels(ax, items, xin, yin):
    """A code sits at its bubble's centre where free, else at the nearest clear ring position."""
    pt = CODE_PX*mf.PX; boxes = []
    for x, y, r, text in items:
        w = 0.56*pt/72*len(text); h = pt/72
        for gap, a in [(None, None)] + [(g, a) for g in (0.035, 0.14, 0.26) for a in ANGLES]:
            if gap is None: cx, cy = x, y
            else:
                cx = x + np.cos(np.radians(a))*(r+gap+w/2)/xin; cy = y + np.sin(np.radians(a))*(r+gap+h/2)/yin
            b = (cx-w/2/xin, cx+w/2/xin, cy-h/2/yin, cy+h/2/yin)
            if b[0] < XLIM[0] or b[1] > XLIM[1] or b[2] < YLIM[0] or b[3] > YLIM[1]: continue
            if any(b[0] < q[1] and b[1] > q[0] and b[2] < q[3] and b[3] > q[2] for q in boxes): continue
            boxes.append(b)
            ax.text(cx, cy, text, color=mf.INK, ha='center', va='center', zorder=6,
                    path_effects=[pe.withStroke(linewidth=3, foreground='white')], **mf.cal(CODE_PX))
            break

def plot(w, h):
    fig = mf.new_fig(w, h)
    L, R, T, B = 150/w, 1 - 4/w, 1 - 30/h, (LEG_PX + 190)/h
    ax = fig.add_axes([L, B, R-L, T-B])
    xin = w*(R-L)/mf.DPI/(XLIM[1]-XLIM[0]); yin = h*(T-B)/mf.DPI/(YLIM[1]-YLIM[0])
    items = []
    for i, (code, name, col) in enumerate(GROUPS):
        g = df[df.income_group == code].sort_values('aipi', ascending=False).reset_index(drop=True)
        s = g.population_m.values*S_PER_MILLION
        x = pack(i, g.aipi.values, s, xin, yin)
        ax.scatter(x, g.aipi, s=s, facecolors=to_rgba(col, FACE_ALPHA), edgecolors='none', zorder=3)
        wavg = np.average(g.aipi, weights=g.population_m)
        ax.plot([i-0.30, i+0.30], [wavg, wavg], color=mf.INK, lw=BAR_LW, solid_capstyle='butt', zorder=5)
        tails = set(g.index[:LABEL_TAIL]) | set(g.index[-LABEL_TAIL:])
        for j, row in g.iterrows():
            if row.population_m > LABEL_POP or j in tails:
                items.append((row.population_m, x[j], row.aipi, np.sqrt(s[j]/np.pi)/72.0, row.code))
    items.sort(key=lambda t: -t[0]); place_labels(ax, [t[1:] for t in items], xin, yin)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    mf.style_axes(ax, axis='y'); ax.spines['bottom'].set_visible(False)
    mf.set_ticks(ax, [0.2, 0.4, 0.6, 0.8], 'y', fmt='{:.1f}')
    ax.set_xticks(range(len(GROUPS))); ax.set_xticklabels([n for _, n, _ in GROUPS])
    ax.tick_params(axis='x', length=0, pad=14)
    for t, (_, _, col) in zip(ax.get_xticklabels(), GROUPS):
        t.set_fontproperties(mf.P_CAL_B); t.set_fontsize(mf.T_HDR*mf.PX); t.set_color(col); t.set_linespacing(1.05); t.set_va('top')
    # legend strip: circles use the same scatter scale, so they are to size; they share a baseline,
    # values underneath. Coordinates are inches on both axes.
    LH = LEG_PX/mf.DPI; lg = fig.add_axes([L, 0, R-L, LEG_PX/h]); LW_IN = w*(R-L)/mf.DPI
    lg.set_xlim(0, LW_IN); lg.set_ylim(0, LH); lg.axis('off')
    rmax = np.sqrt(max(LEGEND_POPS)*S_PER_MILLION/np.pi)/72.0; base = LH - 2*rmax - 0.02; GAP = 0.20
    lt = lg.text(0, base + rmax, 'Population (millions)', ha='left', va='center', color=mf.LABEL, **mf.cal(mf.T_LEG))
    fig.canvas.draw(); cursor = lt.get_window_extent().x1/mf.DPI - L*w/mf.DPI + 0.25
    for pop in LEGEND_POPS:
        r = np.sqrt(pop*S_PER_MILLION/np.pi)/72.0; half = max(r, 0.12); cx = cursor + half
        lg.scatter([cx], [base + r], s=pop*S_PER_MILLION, facecolors='none', edgecolors=mf.GREY_TXT, linewidths=1.6, clip_on=False)
        lg.text(cx, base - 0.07, f'{pop:,}', ha='center', va='top', color=mf.LABEL, **mf.cal(mf.T_LEG))
        cursor = cx + half + GAP
    lg.plot([cursor+0.20, cursor+0.75], [base + rmax]*2, color=mf.INK, lw=BAR_LW, solid_capstyle='butt', clip_on=False)
    lg.text(cursor+0.88, base + rmax, 'Group average, population-weighted', ha='left', va='center', color=mf.LABEL, **mf.cal(mf.T_LEG))
    fig.canvas.draw()
    over = max(t.get_window_extent().x1 for t in lg.texts)/w
    assert over <= 1.0, f'legend runs past the canvas: {over:.3f}'
    return fig

TITLE = "Major AI preparedness gaps exist between countries"
UNIT = "AI Preparedness Index, by World Bank income group in 2023"
CAP = ("Source: AI Preparedness Index; World Bank income classification and population data.\n"
       "Note: The horizontal bar is the population-weighted mean index of the group. An economy is labelled with its ISO3 code "
       "if it has more than 50 million people or if it is among the three highest or three lowest index values in its column.\n" + URL)
mf.compose(plot, TITLE, UNIT, CAP, STEM + ".png", W=2160, H=2160)
print("wrote", STEM + ".png and", STEM + ".csv")
