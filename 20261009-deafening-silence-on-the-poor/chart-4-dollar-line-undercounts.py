"""Chart 4: dollar line undercounts (2026 global MPI).
Self-contained: house style and data are embedded. Requires numpy, matplotlib and Pillow.
Run: python chart-4-dollar-line-undercounts.py  -> writes chart-4-dollar-line-undercounts.png and .csv
"""
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

# UNDP and OPHI, 2026 global MPI statistical update, Table 1: acute multidimensional poverty headcount and the World Bank
# $3.00 a day headcount (2021 PPP, WDI, most recent year 2014 to 2025) for the same country.
# The 20 countries with an MPI headcount of at least 20 percent and the largest gap, sorted by gap ascending.
# (country, MPI survey, acute MPI headcount %, $3.00 headcount %)
DATA = [
    ('Rwanda', '2019/2020 D', 48.82, 38.6),
    ('Pakistan', '2017/2018 D', 38.33, 23.0),
    ('Cameroon', '2018 D', 43.59, 26.7),
    ('Sierra Leone', '2019 D', 59.22, 41.5),
    ('Liberia', '2019/2020 D', 52.32, 33.6),
    ('Guatemala', '2014/2015 D', 28.88, 9.7),
    ('Niger', '2021 N', 79.89, 60.5),
    ('Gambia', '2019/2020 D', 41.71, 22.0),
    ("Côte d'Ivoire", '2021 D', 42.77, 20.8),
    ('Burkina Faso', '2021 D', 64.47, 42.1),
    ('Guinea-Bissau', '2018/2019 M', 64.40, 39.9),
    ('Senegal', '2023 D', 45.08, 17.9),
    ('Myanmar', '2015/2016 D', 38.32, 10.3),
    ('Mali', '2023/2024 D', 64.40, 36.1),
    ('Benin', '2021/2022 M', 55.92, 27.2),
    ('Ethiopia', '2019 D', 68.74, 38.6),
    ('Sudan', '2014 M', 52.33, 10.1),
    ('Chad', '2019 M', 84.17, 39.5),
    ('Mauritania', '2019/2021 D', 58.45, 10.2),
    ('Guinea', '2018 D', 66.21, 11.7)
]
N_DOUBLE, N_BOTH = 15, 91   # countries (of all with both measures, MPI headcount >= 10%) where MPI > 2x $3.00 rate
short = {"Congo (Democratic Republic of the)": "DR Congo", "Tanzania (United Republic of)": "Tanzania", "Central African Republic": "Central African Rep."}
DATA = sorted(DATA, key=lambda r: r[3])   # plotted from the lowest $3.00 rate at the bottom to the highest at the top
labels = [short.get(r[0], r[0]) for r in DATA]; H = [r[2] for r in DATA]; h3 = [r[3] for r in DATA]
fig = new_figure(9.2, 8.4)
ax = fig.add_subplot(111)
y = list(range(len(DATA)))
ax.hlines(y, h3, H, color=GOLD, lw=2, zorder=1)
ax.scatter(h3, y, color=BLUE, s=70, zorder=3, label="Below $3.00 a day")
ax.scatter(H, y, color=RED, s=70, zorder=3, label="In acute multidimensional poverty")
for yy, a, b in zip(y, h3, H):
    ax.text(b + 1.5, yy, f"{b:.0f}%", va="center", ha="left", fontsize=12, color=RED)
    if a >= 6:
        ax.text(a - 1.5, yy, f"{a:.0f}%", va="center", ha="right", fontsize=12, color=BLUE)
    else:
        ax.text(a, yy + 0.42, f"{a:.0f}%", va="center", ha="center", fontsize=12, color=BLUE)
ax.set_yticks(y); ax.set_yticklabels(labels)
ax.set_xlim(0, 100); ax.set_xticks(range(0, 101, 20)); ax.set_xticklabels([f"{x}%" for x in range(0, 101, 20)])
ax.set_xlabel("Share of population")
ax.set_ylim(-0.8, len(DATA) - 0.2)
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, frameon=False)

compose(render_plot(fig),
        title="The 20 largest gaps between the MPI and income poverty",
        subtitle="Share of population in acute multidimensional poverty versus below $3.00 a day, same country, 2026 global MPI",
        source="UNDP and OPHI, 2026 global Multidimensional Poverty Index statistical update (October 2026), Table 1, which pairs each country's MPI headcount with the World Bank's $3.00 a day headcount (2021 PPP).",
        note=f"Acute multidimensional poverty means a deprivation score of at least one third across ten weighted indicators. The 20 countries with an MPI headcount of at least 20 percent and the largest gap in percentage points, sorted by the $3.00 rate. The two measures come from different surveys and years, both the most recent available between 2014 and 2025. In {N_DOUBLE} of the {N_BOTH} countries with both measures and an MPI headcount of at least 10 percent, acute multidimensional poverty is more than double income poverty.",
        out="chart-4-dollar-line-undercounts.png", csv="chart-4-dollar-line-undercounts.csv",
        csv_rows=[["country", "mpi_survey", "acute_mpi_headcount_pct", "below_3_dollars_pct", "gap_pp"]]
                 + [[r[0], r[1], r[2], r[3], round(r[2] - r[3], 2)] for r in DATA])
