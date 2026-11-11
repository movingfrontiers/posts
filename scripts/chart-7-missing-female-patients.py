#!/usr/bin/env python3
"""chart-7-missing-female-patients: Male outpatient visits per female visit at AIIMS New Delhi by home state, 2016 (Kapoor et al., BMJ Open, 2019).

From the Moving Frontiers post "Why Don't Indian Women Live Longer?" (November 2026).
Self-contained: the house style and the data are inlined; no other files are read.
Requires numpy, matplotlib and pillow. Run:  python3 "chart-7-missing-female-patients.py"
Writes "chart-7-missing-female-patients.png" and "chart-7-missing-female-patients.csv" next to this script.
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

DATA = [["Delhi", 1.41], ["Haryana", 1.7], ["Uttar Pradesh", 1.98], ["Bihar", 2.37]]

POP_RATIO = 1.09  # men per woman in the population, Census 2011, as reported by the authors
def plot(fig):
    ax = fig.add_subplot(); style_axes(ax)
    n = [r[0] for r in DATA][::-1]; v = [r[1] for r in DATA][::-1]
    ax.barh(range(4), v, .62, color=[RED] + [NAVY] * 3, zorder=3)
    for i, vv in enumerate(v): val(ax, vv + .03, i, f'{vv:.2f}', RED if i == 0 else NAVY, ha='left', va='center_baseline')
    zero_line(ax, POP_RATIO, span=(-.5, 3.5), axis='x')
    ax.text(POP_RATIO + .025, 3.52, 'Men per woman in the\npopulation, 1.09', fontsize=pt(S_EXPL), color=LABEL, ha='left', va='bottom',
            linespacing=1.3, bbox=dict(fc='white', ec='none', pad=2), zorder=5)
    ax.set_yticks(range(4)); ax.set_yticklabels(n, fontsize=pt(S_LABEL), color=LABEL)
    ax.set_xlim(0, 2.6); ax.set_ylim(-.5, 4.15); ax.set_xticks([0, .5, 1, 1.5, 2, 2.5])
if __name__ == '__main__':
    write_csv(OUT('.csv'), ['home_state', 'male_visits_per_female_visit'], DATA)
    print(compose(plot, 'For every woman seen at India\'s top public hospital, 1.4 to 2.4 men are',
        "Male outpatient visits per female visit at AIIMS New Delhi, by patient's home state, 2016",
        'Source: Kapoor and others, "Missing female patients", BMJ Open, 2019.\nNote: 2.38 million visits, excluding obstetrics and gynaecology; ratios adjusted for age and department.\n' + READ,
        OUT('.png'), W=2160, H=1900))
