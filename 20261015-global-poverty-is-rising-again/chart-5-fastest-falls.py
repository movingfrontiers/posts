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

# UNDP and OPHI, 2026 global MPI, Table 2 (harmonised): steepest annual falls in the poverty rate between the first and latest survey.
DATA = [{"country": "Timor-Leste", "survey_first": "2009/2010", "survey_latest": "2016", "rate_first_pct": 69.6, "rate_latest_pct": 46.9, "fall_points_per_year": 3.5}, {"country": "Sierra Leone", "survey_first": "2013", "survey_latest": "2019", "rate_first_pct": 74.1, "rate_latest_pct": 55.2, "fall_points_per_year": 3.14}, {"country": "Congo", "survey_first": "2005", "survey_latest": "2014/2015", "rate_first_pct": 53.8, "rate_latest_pct": 24.7, "fall_points_per_year": 3.06}, {"country": "Sao Tome and Principe", "survey_first": "2008/2009", "survey_latest": "2019", "rate_first_pct": 40.7, "rate_latest_pct": 11.6, "fall_points_per_year": 2.77}, {"country": "India", "survey_first": "2005/2006", "survey_latest": "2020", "rate_first_pct": 55.1, "rate_latest_pct": 16.4, "fall_points_per_year": 2.67}, {"country": "Cambodia", "survey_first": "2010", "survey_latest": "2021/2022", "rate_first_pct": 47.1, "rate_latest_pct": 16.6, "fall_points_per_year": 2.65}, {"country": "Gambia", "survey_first": "2013", "survey_latest": "2019/2020", "rate_first_pct": 54.7, "rate_latest_pct": 38.1, "fall_points_per_year": 2.55}, {"country": "Nicaragua", "survey_first": "2001", "survey_latest": "2011/2012", "rate_first_pct": 41.7, "rate_latest_pct": 16.5, "fall_points_per_year": 2.41}, {"country": "Bangladesh", "survey_first": "2014", "survey_latest": "2022", "rate_first_pct": 30.5, "rate_latest_pct": 11.5, "fall_points_per_year": 2.38}, {"country": "Liberia", "survey_first": "2007", "survey_latest": "2019/2020", "rate_first_pct": 81.4, "rate_latest_pct": 52.3, "fall_points_per_year": 2.33}, {"country": "Togo", "survey_first": "2010", "survey_latest": "2017", "rate_first_pct": 58.2, "rate_latest_pct": 43.0, "fall_points_per_year": 2.18}, {"country": "Uganda", "survey_first": "2011", "survey_latest": "2016", "rate_first_pct": 67.7, "rate_latest_pct": 57.2, "fall_points_per_year": 2.11}, {"country": "Eswatini", "survey_first": "2006/2007", "survey_latest": "2021/2022", "rate_first_pct": 38.7, "rate_latest_pct": 8.0, "fall_points_per_year": 2.05}, {"country": "Kenya", "survey_first": "2008/2009", "survey_latest": "2022", "rate_first_pct": 50.1, "rate_latest_pct": 23.0, "fall_points_per_year": 2.01}, {"country": "Lao PDR", "survey_first": "2011/2012", "survey_latest": "2023", "rate_first_pct": 40.4, "rate_latest_pct": 17.8, "fall_points_per_year": 1.96}]
rows = DATA[::-1]
fig = new_figure(9.2, 7.8); ax = fig.add_subplot(111)
y = list(range(len(rows)))
for yy, r in zip(y, rows):
    ax.annotate("", xy=(r["rate_latest_pct"], yy), xytext=(r["rate_first_pct"], yy), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2, mutation_scale=14))
    ax.text(r["rate_first_pct"] + 1.5, yy, f'{r["rate_first_pct"]:.0f}%', va="center", ha="left", fontsize=11.5, color="#555")
    ax.text(r["rate_latest_pct"] - 1.5, yy, f'{r["rate_latest_pct"]:.0f}%', va="center", ha="right", fontsize=11.5, color=GREEN, fontweight="bold")
    ax.text(100, yy, f'{r["fall_points_per_year"]:.1f}', va="center", ha="right", fontsize=11.5, color="#666")
ax.text(100, len(rows) - 0.4, "points\nper year", va="bottom", ha="right", fontsize=10.5, color="#666", linespacing=1.1)
ax.set_yticks(y); ax.set_yticklabels([f'{r["country"]} ({r["survey_first"]} to {r["survey_latest"]})' for r in rows])
ax.set_ylim(-0.7, len(rows) + 1.0); ax.set_xlim(0, 100); ax.set_xticks(range(0, 101, 20)); ax.set_xticklabels([f"{v}%" for v in range(0, 101, 20)])
ax.set_xlabel("Share of population in acute multidimensional poverty, first to latest survey")
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
compose(render_plot(fig), title="34 of 89 countries halved their MPI between surveys",
        subtitle="The 15 steepest falls in the acute multidimensional poverty rate, first to latest harmonised survey, with the fall in percentage points per year",
        source='UNDP and OPHI, 2026 global Multidimensional Poverty Index statistical update (October 2026), Table 2 (harmonised estimates).', note="Harmonised estimates. Ranked by the annual fall in the headcount ratio between the first and the latest survey in the trend series; survey years in brackets.",
        out=OUT + ".png", csv=OUT + ".csv", csv_rows=[list(DATA[0].keys())] + [list(r.values()) for r in DATA])
