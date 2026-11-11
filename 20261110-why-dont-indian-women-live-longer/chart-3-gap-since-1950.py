#!/usr/bin/env python3
"""chart-3-gap-since-1950: Female minus male life expectancy at birth, 1950 to 2023, India, China, Japan, Vietnam.

From the Moving Frontiers post "Why Don't Indian Women Live Longer?" (November 2026).
Self-contained: the house style and the data are inlined; no other files are read.
Requires numpy, matplotlib and pillow. Run:  python3 "chart-3-gap-since-1950.py"
Writes "chart-3-gap-since-1950.png" and "chart-3-gap-since-1950.csv" next to this script.
"""
import sys
# ---------------------------------------------------------------------------
# house_style (inlined verbatim): Moving Frontiers chart style.
# Plot in matplotlib, compose title, unit line, explainer, caption and
# wordmark in PIL with every gap measured ink to ink, then verify from pixels.
# ---------------------------------------------------------------------------
import io, os, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont

W, H, M, DPI = 2160, 2700, 150, 200
PX = 72 / DPI
GAP_TITLE_UNIT, GAP_UNIT_EXPL, GAP_HEAD_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK = 34, 22, 70, 70, 90
NAVY, RED, SKY, GOLD = '#0B2265', '#D0412F', '#5B8FCC', '#C9962B'
INK, GREY_TXT, LABEL, BAND = '#111111', '#555555', '#333333', '#E6EAF2'
T_TITLE, T_UNIT, T_CAP = (17, 17, 17), (34, 34, 34), (95, 95, 95)
S_TITLE, S_UNIT, S_EXPL, S_CAP, S_MARK = 92, 54, 42, 37, 48
S_HEAD, S_LABEL, S_VAL, S_TICK, S_AXT, S_LEG = 54, 46, 47, 42, 46, 46

def _font(cands, bold=False):
    """First font file that exists; else matplotlib's bundled DejaVu Sans."""
    for p in cands:
        if os.path.exists(p): return p
    return fm.findfont(fm.FontProperties(family='DejaVu Sans', weight='bold' if bold else 'normal'))
_FD = ['/usr/share/fonts/truetype/', '/usr/share/fonts/', '/Library/Fonts/', 'C:/Windows/Fonts/']
ARIAL   = _font([d + 'liberation/LiberationSans-Regular.ttf' for d in _FD] + [d + 'arial.ttf' for d in _FD] + ['/Library/Fonts/Arial.ttf'])
ARIAL_B = _font([d + 'liberation/LiberationSans-Bold.ttf' for d in _FD] + [d + 'arialbd.ttf' for d in _FD] + ['/Library/Fonts/Arial Bold.ttf'], True)
CAL     = _font([d + 'crosextra/Carlito-Regular.ttf' for d in _FD] + [d + 'calibri.ttf' for d in _FD])
CAL_B   = _font([d + 'crosextra/Carlito-Bold.ttf' for d in _FD] + [d + 'calibrib.ttf' for d in _FD], True)
for _f in (ARIAL, ARIAL_B, CAL, CAL_B): fm.fontManager.addfont(_f)
SANS = fm.FontProperties(fname=ARIAL).get_name()
VALFAM = fm.FontProperties(fname=CAL_B).get_name()
plt.rcParams.update({'font.family': SANS, 'axes.unicode_minus': False})

def pt(px): return px * PX

def style_axes(ax, left=False):
    ax.grid(False)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    if left:
        ax.spines['left'].set_visible(True); ax.spines['left'].set_color(INK); ax.spines['left'].set_linewidth(1.6)
    ax.spines['bottom'].set_color(INK); ax.spines['bottom'].set_linewidth(1.6)
    ax.tick_params(axis='both', direction='out', length=12, width=1.6, pad=10, labelsize=pt(S_TICK), colors=INK)
    ax.tick_params(axis='y', length=12 if left else 0)
    ax.patch.set_alpha(0)

def zero_line(ax, y=0, span=None, axis='y'):
    kw = dict(color=INK, lw=2.6, ls=(0, (1, 1.6)), zorder=1)
    if axis == 'y':
        x0, x1 = span if span else ax.get_xlim(); ax.plot([x0, x1], [y, y], **kw)
    else:
        y0, y1 = span if span else ax.get_ylim(); ax.plot([y, y], [y0, y1], **kw)

def val(ax, x, y, s, c, **k):
    """Value label: Calibri bold in the series colour."""
    return ax.text(x, y, s, color=c, fontsize=pt(S_VAL), fontfamily=VALFAM, fontweight='bold', **k)

def _wrap(d, text, font, width):
    out = []
    for para in text.split('\n'):
        line = ''
        for w in para.split(' '):
            t = (line + ' ' + w).strip()
            if d.textlength(t, font=font) <= width: line = t
            else: out.append(line); line = w
        out.append(line)
    return out

def _block(d, lines, font, x, y, fill, spacing):
    """Draw lines with the first line's ink top at y; return the ink bottom."""
    top_off = d.textbbox((0, 0), lines[0], font=font)[1]
    yy = y - top_off; bottom = y
    for ln in lines:
        d.text((x, yy), ln, font=font, fill=fill)
        bottom = d.textbbox((x, yy), ln, font=font)[3]; yy += round(font.size * spacing)
    return bottom

def _ink(img):
    a = np.asarray(img.convert('RGB')); m = (a < 250).any(axis=2)
    ys, xs = np.where(m.any(axis=1))[0], np.where(m.any(axis=0))[0]
    return xs[0], ys[0], xs[-1] + 1, ys[-1] + 1

def compose(plot_fn, title, unit, caption, out, expl=None, W=W, H=H):
    f = lambda p, s: ImageFont.truetype(p, s)
    cw = W - 2 * M
    img = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(img)
    y = _block(d, _wrap(d, title, f(ARIAL_B, S_TITLE), cw), f(ARIAL_B, S_TITLE), M, M, T_TITLE, 1.18)
    y = _block(d, _wrap(d, unit, f(ARIAL, S_UNIT), cw), f(ARIAL, S_UNIT), M, y + GAP_TITLE_UNIT, T_UNIT, 1.3)
    if expl: y = _block(d, _wrap(d, expl, f(ARIAL, S_EXPL), cw), f(ARIAL, S_EXPL), M, y + GAP_UNIT_EXPL, T_CAP, 1.42)
    head_bottom = y
    fc, fmk = f(ARIAL, S_CAP), f(ARIAL_B, S_MARK)
    mark = 'Moving Frontiers'; mw = d.textlength(mark, font=fmk)
    clines = _wrap(d, caption, fc, cw - mw - GAP_CAP_MARK)
    tmp = Image.new('RGB', (W, 1600), 'white')
    cap_h = _block(ImageDraw.Draw(tmp), clines, fc, M, 100, T_CAP, 1.42) - 100
    cap_top = H - M - cap_h
    ph = cap_top - GAP_PLOT_CAP - (head_bottom + GAP_HEAD_PLOT)
    for _ in range(5):
        fig = plt.figure(figsize=(cw / DPI, ph / DPI), dpi=DPI, layout='constrained')
        fig.get_layout_engine().set(w_pad=0, h_pad=0, wspace=0, hspace=0)
        plot_fn(fig)
        buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=DPI, facecolor='white'); plt.close(fig)
        p = Image.open(buf).convert('RGB'); p = p.crop(_ink(p))
        target = cap_top - GAP_PLOT_CAP - (head_bottom + GAP_HEAD_PLOT)
        if abs(p.height - target) <= 8: break
        ph += target - p.height
    img.paste(p, (M, head_bottom + GAP_HEAD_PLOT))
    cb = _block(d, clines, fc, M, cap_top, T_CAP, 1.42)
    mb = d.textbbox((0, 0), mark, font=fmk)
    d.text((W - M - mb[2], cb - mb[3]), mark, font=fmk, fill=NAVY)
    img.save(out, dpi=(DPI, DPI))
    return verify(out, head_bottom, p.height, cap_top, W, H)

def verify(path, head_bottom, plot_h, cap_top, W, H):
    img = Image.open(path); x0, y0, x1, y1 = _ink(img)
    assert x0 >= M - 2 and y0 == M and x1 <= W - M + 2 and abs((H - y1) - M) <= 2, ('margins', x0, y0, x1, y1)
    resid = cap_top - (head_bottom + GAP_HEAD_PLOT + plot_h)
    assert abs(resid - GAP_PLOT_CAP) <= 8, ('plot-caption gap', resid)
    return dict(ink=(int(x0), int(y0), int(x1), int(y1)), plot_cap_gap=int(resid))

def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)
# ------------------------------- end house_style ---------------------------

mf = sys.modules[__name__]
HERE = os.path.dirname(os.path.abspath(__file__))
STEM = os.path.splitext(os.path.basename(__file__))[0]
def OUT(ext): return os.path.join(HERE, STEM + ext)
SRC = 'Source: United Nations, World Population Prospects 2024.'
READ = 'Read more: movingfrontiers.substack.com/india-longevity-gap'

DATA = {"China": [3.547, 3.458, 3.509, 3.297, 3.423, 3.759, 3.739, 3.821, 3.96, 3.382, 2.692, 3.276, 4.244, 4.206, 4.199, 4.269, 4.134, 4.075, 3.965, 3.914, 3.838, 3.703, 3.742, 3.932, 4.153, 4.258, 4.052, 4.358, 4.393, 4.421, 4.457, 4.521, 4.562, 4.601, 4.635, 4.688, 4.755, 4.85, 4.897, 4.858, 4.7, 4.761, 4.721, 4.901, 5.001, 5.154, 5.159, 5.156, 5.118, 5.019, 5.045, 5.053, 5.07, 5.091, 5.099, 5.174, 5.196, 5.11, 5.137, 5.232, 5.137, 5.315, 5.357, 5.342, 5.392, 5.42, 5.477, 5.822, 5.539, 5.444, 5.754, 5.427, 5.666, 5.726], "India": [-1.526, -1.473, -1.434, -1.39, -1.381, -1.378, -1.38, -1.393, -1.41, -1.423, -1.413, -1.378, -1.34, -1.297, -1.255, -1.109, -1.082, -1.061, -1.145, -1.133, -1.111, -1.099, -1.057, -1.026, -0.992, -0.93, -0.841, -0.737, -0.574, -0.405, -0.216, -0.016, 0.189, 0.391, 0.586, 0.763, 0.927, 1.072, 1.199, 1.299, 1.395, 1.465, 1.508, 1.522, 1.549, 1.574, 1.613, 1.678, 1.769, 1.881, 2.034, 2.175, 2.34, 2.493, 2.623, 2.768, 2.884, 2.985, 3.065, 3.124, 3.165, 3.186, 3.191, 3.182, 3.151, 3.113, 3.066, 3.022, 2.99, 2.975, 3.409, 2.965, 3.034, 3.075], "Japan": [3.319, 3.31, 3.411, 3.528, 4.103, 4.152, 4.238, 4.354, 4.554, 4.668, 4.838, 4.921, 4.936, 5.082, 5.133, 5.167, 5.202, 5.201, 5.238, 5.419, 5.364, 5.353, 5.412, 5.266, 5.115, 5.129, 5.159, 5.195, 5.257, 5.329, 5.382, 5.362, 5.464, 5.591, 5.662, 5.652, 5.706, 5.784, 5.742, 5.832, 5.923, 6.017, 6.166, 6.182, 6.313, 6.364, 6.465, 6.49, 6.71, 6.745, 6.837, 6.831, 6.86, 6.92, 6.892, 6.912, 6.779, 6.777, 6.739, 6.81, 6.72, 6.444, 6.447, 6.376, 6.305, 6.241, 6.173, 6.199, 6.095, 6.064, 6.148, 6.093, 6.028, 6.053], "Vietnam": [8.961, 9.143, 9.39, 9.421, 6.275, 5.121, 5.364, 5.514, 5.69, 5.838, 6.135, 6.349, 6.979, 8.13, 7.781, 8.785, 9.17, 9.46, 11.564, 10.92, 11.07, 10.978, 12.706, 11.417, 12.043, 9.115, 8.513, 8.652, 8.793, 8.951, 9.01, 8.854, 8.535, 8.228, 8.023, 8.143, 8.248, 8.221, 7.896, 7.875, 8.065, 8.027, 7.805, 7.596, 7.248, 7.427, 7.534, 7.805, 8.241, 8.852, 9.078, 9.376, 9.736, 9.897, 9.525, 9.558, 9.573, 9.593, 9.58, 9.566, 9.602, 9.53, 9.486, 9.482, 9.498, 9.552, 9.61, 9.573, 9.56, 9.558, 9.949, 9.278, 9.451, 9.387]}

YEARS = list(range(1950, 2024))
COLS = {'Vietnam': NAVY, 'Japan': GOLD, 'China': SKY, 'India': RED}
OFF = {'Vietnam': 0, 'Japan': .25, 'China': -.25, 'India': 0}
def plot(fig):
    ax = fig.add_subplot(); style_axes(ax)
    for n, c in COLS.items():
        s = DATA[n]
        ax.plot(YEARS, s, color=c, lw=5.5 if n == 'India' else 4, zorder=4 if n == 'India' else 3, solid_capstyle='round')
        val(ax, 2024.2, s[-1] + OFF[n], f'{n} {s[-1]:.1f}', c, ha='left', va='center')
    ax.set_xlim(1950, 2023); ax.set_ylim(-3, 13.5); zero_line(ax, 0, span=(1950, 2023))
    ax.set_xticks([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2023]); ax.set_yticks(range(-2, 13, 2))
    ax.annotate('Indian women\novertake men, 1982', xy=(1982, 0.05), xytext=(1984, -2.25), fontsize=pt(S_EXPL), color=LABEL,
                ha='left', va='center', arrowprops=dict(arrowstyle='-', color=LABEL, lw=1.6, shrinkB=4))
    ax.text(1976, 12.3, 'War years', fontsize=pt(S_EXPL), color=LABEL, ha='left', va='center')
if __name__ == '__main__':
    write_csv(OUT('.csv'), ['year'] + list(COLS), [[y] + [DATA[n][i] for n in COLS] for i, y in enumerate(YEARS)])
    print(compose(plot, 'For three decades after independence, Indian men outlived Indian women',
        'Female minus male life expectancy at birth, years, 1950 to 2023',
        SRC + '\n' + READ,
        OUT('.png'), W=2160, H=2300))
