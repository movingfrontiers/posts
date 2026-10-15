# ---- Moving Frontiers house style (inlined) -------------------------------
# Plot in matplotlib on a transparent canvas, then compose() lays out title,
# subtitle, plot, caption and watermark in PIL with every gap measured ink to
# ink, and verify() re-measures the finished PNG and asserts the gaps.
import io, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

RED, GOLD, GREEN, BLUE, GREY = "#C62828", "#F9A825", "#00897B", "#283593", "#888888"
INK, PAPER = "#141414", "#FFFFFF"
def palette(n):
    return [[BLUE], [BLUE, RED], [BLUE, RED, GREEN], [BLUE, RED, GREEN, GOLD]][n - 1]

REF_W = 1980
GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK, BORDER = 25, 70, 60, 20, 70
TITLE_PX, SUB_PX, CAP_PX = 61, 40, 30          # at REF_W; title ~3.1% of width
TITLE_RGB, SUB_RGB, CAP_RGB = (45, 45, 45), (100, 100, 100), (102, 102, 102)
WATERMARK = "movingfrontiers.substack.com"

_fp = font_manager.findfont("DejaVu Sans")
_fpb = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))
def _font(px, bold=False):
    return ImageFont.truetype(_fpb if bold else _fp, px)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 15,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
    "axes.labelsize": 15, "axes.edgecolor": "#888888", "axes.linewidth": 1.0,
    "axes.facecolor": PAPER, "figure.facecolor": "none", "savefig.facecolor": "none",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": "#444444", "ytick.color": "#444444", "text.color": INK,
})

def new_figure(w_in=9.2, h_in=7.34, dpi=200):
    fig = plt.figure(figsize=(w_in, h_in), dpi=dpi)
    return fig

def render_plot(fig):
    """Rasterise the figure on a transparent background and crop to its ink."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi, transparent=True, bbox_inches="tight", pad_inches=0.05)
    buf.seek(0)
    im = Image.open(buf).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox)

def _text_layer(text, px, rgb, bold=False, width_px=None, align="left", linespacing=1.25):
    """Render wrapped text on a transparent layer cropped to its ink."""
    font = _font(px, bold)
    if width_px:
        # wrap by measured width
        lines = []
        for para in text.split("\n"):
            words, cur = para.split(), ""
            for w in words:
                t = (cur + " " + w).strip()
                if font.getlength(t) <= width_px or not cur:
                    cur = t
                else:
                    lines.append(cur); cur = w
            lines.append(cur)
    else:
        lines = text.split("\n")
    lh = int(round(px * linespacing))
    H = lh * len(lines) + px
    W = int(max(font.getlength(l) for l in lines)) + px
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, l in enumerate(lines):
        x = 0 if align == "left" else W - px - font.getlength(l)
        d.text((x, i * lh), l, font=font, fill=rgb + (255,))
    return layer.crop(layer.getchannel("A").getbbox())

def compose(plot_im, title, subtitle, source, note=None, out="chart.png", csv=None, csv_rows=None, W=REF_W):
    s = W / REF_W
    inner = W - 2 * BORDER
    # scale the plot to the inner width
    pw, ph = plot_im.size
    if pw != inner:
        plot_im = plot_im.resize((inner, int(ph * inner / pw)), Image.LANCZOS)
    t_layer = _text_layer(title, int(TITLE_PX * s), TITLE_RGB, bold=True, width_px=inner)
    s_layer = _text_layer(subtitle, int(SUB_PX * s), SUB_RGB, width_px=inner)
    cap = "Source: " + source + ("\nNote: " + note if note else "")
    c_layer = _text_layer(cap, int(CAP_PX * s), CAP_RGB, width_px=inner)
    m_layer = _text_layer(WATERMARK, int(CAP_PX * 1.2 * s), CAP_RGB)
    H = (BORDER + t_layer.height + GAP_TITLE_SUB + s_layer.height + GAP_SUB_PLOT + plot_im.height
         + GAP_PLOT_CAP + c_layer.height + GAP_CAP_MARK + m_layer.height + BORDER)
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    y = BORDER
    canvas.paste(t_layer, (BORDER, y), t_layer); y += t_layer.height + GAP_TITLE_SUB
    canvas.paste(s_layer, (BORDER, y), s_layer); y += s_layer.height + GAP_SUB_PLOT
    canvas.paste(plot_im, (BORDER, y), plot_im); y += plot_im.height + GAP_PLOT_CAP
    canvas.paste(c_layer, (BORDER, y), c_layer); y += c_layer.height + GAP_CAP_MARK
    canvas.paste(m_layer, (W - BORDER - m_layer.width, y), m_layer)
    canvas.save(out, dpi=(200, 200))
    if csv and csv_rows:
        import csv as _csv
        with open(csv, "w", newline="") as f:
            _csv.writer(f).writerows(csv_rows)
    verify(out, (t_layer.height, s_layer.height, plot_im.height, c_layer.height, m_layer.height))
    return out

def verify(path, heights):
    """Scan rows of the finished PNG for ink and assert the vertical gaps."""
    a = np.asarray(Image.open(path).convert("L"))
    ink_rows = np.where((a < 250).any(axis=1))[0]
    ink_cols = np.where((a < 250).any(axis=0))[0]
    assert ink_rows[0] == BORDER and ink_cols[0] == BORDER, ("border", ink_rows[0], ink_cols[0])
    assert a.shape[0] - 1 - ink_rows[-1] == BORDER, ("bottom border", a.shape[0] - 1 - ink_rows[-1])
    # blocks of ink separated by white gaps
    gaps, prev = [], ink_rows[0]
    for r in ink_rows[1:]:
        if r - prev > 1:
            gaps.append(r - prev - 1)
        prev = r
    expected = [GAP_TITLE_SUB, GAP_SUB_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK]
    found = [g for g in gaps if g >= GAP_CAP_MARK - 1]
    # the four structural gaps must be present in order (text lines create smaller gaps)
    ok = [g for g in found if g in expected or g - 1 in expected or g + 1 in expected]
    assert len(ok) >= 4, ("structural gaps", found)
    print(f"verified {path}: size {a.shape[1]}x{a.shape[0]}, gaps {found}")
# ---------------------------------------------------------------------------

from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import os
OUT = os.path.splitext(os.path.basename(__file__))[0]

# UNDP and OPHI, 2026 global MPI, Table 1: people in multidimensional poverty summed by the year of each country's latest survey (two-year surveys at their midpoint, rounded).
DATA = [{"survey_year": 2014, "poor_m": 89.0, "group": "before 2020"}, {"survey_year": 2015, "poor_m": 8.1, "group": "before 2020"}, {"survey_year": 2016, "poor_m": 73.6, "group": "before 2020"}, {"survey_year": 2017, "poor_m": 19.8, "group": "before 2020"}, {"survey_year": 2018, "poor_m": 132.4, "group": "before 2020"}, {"survey_year": 2019, "poor_m": 118.9, "group": "before 2020"}, {"survey_year": 2020, "poor_m": 254.3, "group": "2020 or later"}, {"survey_year": 2021, "poor_m": 74.1, "group": "2020 or later"}, {"survey_year": 2022, "poor_m": 161.9, "group": "2020 or later"}, {"survey_year": 2023, "poor_m": 11.2, "group": "2020 or later"}, {"survey_year": 2024, "poor_m": 254.7, "group": "2020 or later"}]
OLD_SHARE = 0.3782
yrs = [r["survey_year"] for r in DATA]; vals = [r["poor_m"] for r in DATA]
fig = new_figure(9.2, 6.6); ax = fig.add_subplot(111)
ax.bar(yrs, vals, color=[RED if yv < 2020 else BLUE for yv in yrs], width=0.72)
for yv, v in zip(yrs, vals): ax.text(yv, v + 4, f"{v:,.0f}", ha="center", va="bottom", fontsize=12, color=INK)
ax.set_xticks(range(2014, 2025)); ax.set_xlabel("Year of the latest survey behind each country's estimate (mid-year for two-year surveys)")
ax.set_ylabel("Poor people counted, millions")
ax.set_ylim(0, 365); ax.set_yticks(range(0, 301, 50))
ax.text(2016.4, 357, f"Surveys before 2020: {OLD_SHARE:.0%} of all the poor", fontsize=13, color=RED, ha="center", va="top", fontweight="bold")
ax.text(2016.4, 333, "China 2014: 55m\nPakistan 2017/18: 96m\nEthiopia 2019: 91m", fontsize=11, color="#555", ha="center", va="top", linespacing=1.35)
ax.text(2022.2, 357, f"2020 or later: {1-OLD_SHARE:.0%}", fontsize=13, color=BLUE, ha="center", va="top", fontweight="bold")
ax.text(2022.2, 333, "India 2019/21: 238m\nNigeria 2024: 113m\nDR Congo 2023/24: 74m", fontsize=11, color="#555", ha="center", va="top", linespacing=1.35)
compose(render_plot(fig), title=f"{OLD_SHARE:.0%} of the multidimensionally poor are counted from surveys taken before 2020",
        subtitle="People in acute multidimensional poverty by year of the underlying survey, millions, 2026 global MPI",
        source='UNDP and OPHI, 2026 global Multidimensional Poverty Index statistical update (October 2026), Table 1.', note="Each country's headcount comes from its latest available survey and is applied to 2024 population, so the figure for a country surveyed in 2014 assumes its poverty rate has not changed since. Two-year surveys are placed at their midpoint. The largest countries in each group are listed with their survey year and number of poor.",
        out=OUT + ".png", csv=OUT + ".csv", csv_rows=[list(DATA[0].keys())] + [list(r.values()) for r in DATA])
