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

# UNDP and OPHI, 2026 global MPI, Table 1: MPI headcount alongside the national poverty line and the World Bank $3.00 (2021 PPP) rate reported in the same table, 14 largest countries with all three.
DATA = [{"country": "Chad", "mpi_poor_pct": 84.2, "national_line_pct": 44.8, "below_3_dollars_pct": 39.5, "poor_m": 17.1}, {"country": "Niger", "mpi_poor_pct": 79.9, "national_line_pct": 41.2, "below_3_dollars_pct": 60.5, "poor_m": 21.6}, {"country": "Ethiopia", "mpi_poor_pct": 68.7, "national_line_pct": 33.1, "below_3_dollars_pct": 38.6, "poor_m": 90.8}, {"country": "Madagascar", "mpi_poor_pct": 68.4, "national_line_pct": 75.2, "below_3_dollars_pct": 69.2, "poor_m": 21.9}, {"country": "DR Congo", "mpi_poor_pct": 67.6, "national_line_pct": 56.2, "below_3_dollars_pct": 85.3, "poor_m": 73.8}, {"country": "Mozambique", "mpi_poor_pct": 60.7, "national_line_pct": 65.0, "below_3_dollars_pct": 81.4, "poor_m": 21.0}, {"country": "Uganda", "mpi_poor_pct": 57.2, "national_line_pct": 16.1, "below_3_dollars_pct": 59.8, "poor_m": 28.6}, {"country": "Angola", "mpi_poor_pct": 49.3, "national_line_pct": 32.3, "below_3_dollars_pct": 39.3, "poor_m": 18.7}, {"country": "Nigeria", "mpi_poor_pct": 48.7, "national_line_pct": 56.2, "below_3_dollars_pct": 41.8, "poor_m": 113.3}, {"country": "Tanzania", "mpi_poor_pct": 47.2, "national_line_pct": 26.4, "below_3_dollars_pct": 51.3, "poor_m": 32.4}, {"country": "Pakistan", "mpi_poor_pct": 38.3, "national_line_pct": 21.9, "below_3_dollars_pct": 23.0, "poor_m": 96.3}, {"country": "Myanmar", "mpi_poor_pct": 38.3, "national_line_pct": 24.8, "below_3_dollars_pct": 10.3, "poor_m": 20.9}, {"country": "Bangladesh", "mpi_poor_pct": 14.9, "national_line_pct": 18.7, "below_3_dollars_pct": 5.9, "poor_m": 25.9}, {"country": "China", "mpi_poor_pct": 3.9, "national_line_pct": 0.0, "below_3_dollars_pct": 0.0, "poor_m": 55.1}]
rows = DATA[::-1]
fig = new_figure(9.2, 7.6); ax = fig.add_subplot(111)
y = list(range(len(rows)))
lo = [min(r["mpi_poor_pct"], r["national_line_pct"], r["below_3_dollars_pct"]) for r in rows]
hi = [max(r["mpi_poor_pct"], r["national_line_pct"], r["below_3_dollars_pct"]) for r in rows]
ax.hlines(y, lo, hi, color="#CCCCCC", lw=1.5, zorder=1)
ax.scatter([r["below_3_dollars_pct"] for r in rows], y, color=BLUE, s=70, zorder=3, label="Below $3.00 a day")
ax.scatter([r["national_line_pct"] for r in rows], y, color=GOLD, s=70, zorder=3, label="Below the national poverty line")
ax.scatter([r["mpi_poor_pct"] for r in rows], y, color=RED, s=70, zorder=3, label="In multidimensional poverty")
ax.set_yticks(y); ax.set_yticklabels([r["country"] for r in rows]); ax.set_xlim(-1.5, 100)
ax.set_xticks(range(0, 101, 20)); ax.set_xticklabels([f"{v}%" for v in range(0, 101, 20)]); ax.set_xlabel("Share of population")
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
compose(render_plot(fig), title="Three different poverty lines: the MPI, national lines and $3.00 a day",
        subtitle="Share of population counted as poor on each measure, 14 countries with the most multidimensionally poor and all three measures",
        source='UNDP and OPHI, 2026 global Multidimensional Poverty Index statistical update (October 2026), Table 1.' + " National and $3.00 poverty rates from World Bank WDI, most recent year 2014 to 2025.",
        note="The three measures come from different surveys and years. In Uganda the national line finds 16 percent poor, the $3.00 line 60 percent and the MPI 57 percent; in Chad the national line finds 45 percent, the $3.00 line 40 percent and the MPI 84 percent. India is not shown because no national poverty line estimate is reported.",
        out=OUT + ".png", csv=OUT + ".csv", csv_rows=[list(DATA[0].keys())] + [list(r.values()) for r in DATA])
