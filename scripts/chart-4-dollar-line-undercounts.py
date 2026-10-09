"""Chart 4: dollar line undercounts.
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

# OPHI and UNDP global MPI 2025, Table 1.4: MPI headcount and World Bank $3.00 headcount for the same country.
# The 20 countries with MPI headcount >= 20% and the largest gap, sorted by gap ascending.
# (country, MPI headcount %, $3.00 headcount %, year of $3.00 estimate)
DATA = [
    ('Nepal', 20.07, 2.40, '2022'),
    ('Sierra Leone', 59.22, 41.50, '2018'),
    ('Namibia', 40.88, 22.90, '2015'),
    ('Liberia', 52.32, 33.60, '2016'),
    ('Guatemala', 28.88, 9.70, '2023'),
    ('Niger', 79.89, 60.50, '2021'),
    ('Gambia', 41.71, 22.00, '2020'),
    ('Pakistan', 38.33, 16.50, '2018'),
    ("Cote d'Ivoire", 42.77, 20.90, '2021'),
    ('Burkina Faso', 64.47, 42.10, '2021'),
    ('Guinea-Bissau', 64.40, 39.90, '2021'),
    ('Senegal', 45.08, 17.90, '2021'),
    ('Myanmar', 38.32, 10.30, '2017'),
    ('Benin', 55.92, 27.20, '2021'),
    ('Ethiopia', 68.74, 38.60, '2021'),
    ('Mali', 68.33, 36.10, '2021'),
    ('Sudan', 52.33, 10.10, '2014'),
    ('Chad', 84.17, 39.50, '2022'),
    ('Mauritania', 58.45, 10.20, '2019'),
    ('Guinea', 66.21, 11.70, '2018')
]
N_DOUBLE, N_BOTH = 13, 104   # countries (of all with both measures, H >= 10%) where MPI > 2x $3.00 rate

labels = [r[0] for r in DATA]; H = [r[1] for r in DATA]; h3 = [r[2] for r in DATA]
fig = new_figure(9.2, 8.4)
ax = fig.add_subplot(111)
y = list(range(len(DATA)))
ax.hlines(y, h3, H, color="#BBBBBB", lw=2, zorder=1)
ax.scatter(h3, y, color=BLUE, s=70, zorder=3, label="Below $3.00 a day")
ax.scatter(H, y, color=RED, s=70, zorder=3, label="Multidimensionally poor")
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
        title="Where the dollar line undercounts: the 20 largest gaps between multidimensional and income poverty",
        subtitle="Multidimensionally poor versus below $3.00 a day, share of population, same country",
        source="OPHI and UNDP, global Multidimensional Poverty Index 2025, Table 1.4, which pairs each country's MPI headcount with the World Bank's $3.00 headcount (2021 PPP).",
        note=f"Countries with an MPI headcount of at least 20 percent, ranked by the gap in percentage points. The two measures come from different surveys and years. In {N_DOUBLE} of the {N_BOTH} countries with both measures, multidimensional poverty is more than double income poverty.",
        out="chart-4-dollar-line-undercounts.png", csv="chart-4-dollar-line-undercounts.csv",
        csv_rows=[["country", "mpi_headcount_pct", "below_3_dollars_pct", "year_of_3_dollar_estimate", "gap_pp"]]
                 + [[r[0], r[1], r[2], r[3], round(r[1] - r[2], 2)] for r in DATA])
