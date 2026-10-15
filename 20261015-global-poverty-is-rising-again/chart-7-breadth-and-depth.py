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

# UNDP and OPHI, 2026 global MPI, Table 1: headcount ratio (breadth) against intensity of deprivation among the poor (depth), 108 countries, sorted by number of poor.
DATA = [{"country": "India", "poor_pct": 16.39, "intensity_pct": 41.98, "poor_m": 237.85, "region_group": "South Asia"}, {"country": "Nigeria", "poor_pct": 48.7, "intensity_pct": 55.15, "poor_m": 113.32, "region_group": "Sub-Saharan Africa"}, {"country": "Pakistan", "poor_pct": 38.33, "intensity_pct": 51.72, "poor_m": 96.32, "region_group": "South Asia"}, {"country": "Ethiopia", "poor_pct": 68.74, "intensity_pct": 53.33, "poor_m": 90.77, "region_group": "Sub-Saharan Africa"}, {"country": "DR Congo", "poor_pct": 67.58, "intensity_pct": 50.91, "poor_m": 73.84, "region_group": "Sub-Saharan Africa"}, {"country": "China", "poor_pct": 3.89, "intensity_pct": 41.36, "poor_m": 55.14, "region_group": "Other"}, {"country": "Tanzania", "poor_pct": 47.22, "intensity_pct": 46.88, "poor_m": 32.37, "region_group": "Sub-Saharan Africa"}, {"country": "Uganda", "poor_pct": 57.17, "intensity_pct": 49.16, "poor_m": 28.59, "region_group": "Sub-Saharan Africa"}, {"country": "Afghanistan", "poor_pct": 64.88, "intensity_pct": 55.53, "poor_m": 27.67, "region_group": "South Asia"}, {"country": "Sudan", "poor_pct": 52.33, "intensity_pct": 53.4, "poor_m": 26.4, "region_group": "Sub-Saharan Africa"}, {"country": "Bangladesh", "poor_pct": 14.94, "intensity_pct": 44.52, "poor_m": 25.93, "region_group": "South Asia"}, {"country": "Madagascar", "poor_pct": 68.42, "intensity_pct": 56.41, "poor_m": 21.87, "region_group": "Sub-Saharan Africa"}, {"country": "Niger", "poor_pct": 79.89, "intensity_pct": 58.87, "poor_m": 21.6, "region_group": "Sub-Saharan Africa"}, {"country": "Mozambique", "poor_pct": 60.67, "intensity_pct": 55.11, "poor_m": 21.01, "region_group": "Sub-Saharan Africa"}, {"country": "Myanmar", "poor_pct": 38.32, "intensity_pct": 45.89, "poor_m": 20.88, "region_group": "Other"}, {"country": "Angola", "poor_pct": 49.29, "intensity_pct": 54.18, "poor_m": 18.67, "region_group": "Sub-Saharan Africa"}, {"country": "Chad", "poor_pct": 84.17, "intensity_pct": 61.42, "poor_m": 17.09, "region_group": "Sub-Saharan Africa"}, {"country": "Mali", "poor_pct": 64.4, "intensity_pct": 55.21, "poor_m": 15.76, "region_group": "Sub-Saharan Africa"}, {"country": "Yemen", "poor_pct": 37.42, "intensity_pct": 50.2, "poor_m": 15.19, "region_group": "Other"}, {"country": "Burkina Faso", "poor_pct": 64.47, "intensity_pct": 53.18, "poor_m": 15.18, "region_group": "Sub-Saharan Africa"}, {"country": "Kenya", "poor_pct": 25.35, "intensity_pct": 44.71, "poor_m": 14.31, "region_group": "Sub-Saharan Africa"}, {"country": "Côte d'Ivoire", "poor_pct": 42.77, "intensity_pct": 49.15, "poor_m": 13.66, "region_group": "Sub-Saharan Africa"}, {"country": "Cameroon", "poor_pct": 43.59, "intensity_pct": 53.24, "poor_m": 12.7, "region_group": "Sub-Saharan Africa"}, {"country": "Malawi", "poor_pct": 51.95, "intensity_pct": 46.56, "poor_m": 11.25, "region_group": "Sub-Saharan Africa"}, {"country": "Burundi", "poor_pct": 75.1, "intensity_pct": 54.44, "poor_m": 10.55, "region_group": "Sub-Saharan Africa"}, {"country": "Indonesia", "poor_pct": 3.62, "intensity_pct": 38.71, "poor_m": 10.26, "region_group": "Other"}, {"country": "Guinea", "poor_pct": 66.21, "intensity_pct": 56.37, "poor_m": 9.77, "region_group": "Sub-Saharan Africa"}, {"country": "Zambia", "poor_pct": 43.08, "intensity_pct": 47.41, "poor_m": 9.18, "region_group": "Sub-Saharan Africa"}, {"country": "Ghana", "poor_pct": 24.8, "intensity_pct": 45.48, "poor_m": 8.54, "region_group": "Sub-Saharan Africa"}, {"country": "Senegal", "poor_pct": 45.08, "intensity_pct": 50.18, "poor_m": 8.34, "region_group": "Sub-Saharan Africa"}, {"country": "Brazil", "poor_pct": 3.84, "intensity_pct": 42.55, "poor_m": 8.14, "region_group": "Other"}, {"country": "Benin", "poor_pct": 55.92, "intensity_pct": 51.77, "poor_m": 8.09, "region_group": "Sub-Saharan Africa"}, {"country": "Rwanda", "poor_pct": 48.82, "intensity_pct": 47.31, "poor_m": 6.96, "region_group": "Sub-Saharan Africa"}, {"country": "Papua New Guinea", "poor_pct": 56.63, "intensity_pct": 46.49, "poor_m": 5.99, "region_group": "Other"}, {"country": "Mexico", "poor_pct": 4.52, "intensity_pct": 38.56, "poor_m": 5.92, "region_group": "Other"}, {"country": "Guatemala", "poor_pct": 28.88, "intensity_pct": 46.23, "poor_m": 5.32, "region_group": "Other"}, {"country": "Sierra Leone", "poor_pct": 59.22, "intensity_pct": 49.46, "poor_m": 5.12, "region_group": "Sub-Saharan Africa"}, {"country": "Haiti", "poor_pct": 41.27, "intensity_pct": 48.36, "poor_m": 4.86, "region_group": "Other"}, {"country": "Philippines", "poor_pct": 3.89, "intensity_pct": 40.62, "poor_m": 4.5, "region_group": "Other"}, {"country": "Zimbabwe", "poor_pct": 25.8, "intensity_pct": 42.61, "poor_m": 4.29, "region_group": "Sub-Saharan Africa"}, {"country": "Central African Rep.", "poor_pct": 80.41, "intensity_pct": 57.37, "poor_m": 4.29, "region_group": "Sub-Saharan Africa"}, {"country": "Nepal", "poor_pct": 13.88, "intensity_pct": 40.15, "poor_m": 4.12, "region_group": "South Asia"}, {"country": "South Africa", "poor_pct": 6.26, "intensity_pct": 39.78, "poor_m": 4.0, "region_group": "Sub-Saharan Africa"}, {"country": "Iraq", "poor_pct": 8.64, "intensity_pct": 37.86, "poor_m": 3.98, "region_group": "Other"}, {"country": "Togo", "poor_pct": 37.61, "intensity_pct": 47.75, "poor_m": 3.58, "region_group": "Sub-Saharan Africa"}, {"country": "Mauritania", "poor_pct": 58.45, "intensity_pct": 55.95, "poor_m": 3.02, "region_group": "Sub-Saharan Africa"}, {"country": "Liberia", "poor_pct": 52.32, "intensity_pct": 49.56, "poor_m": 2.94, "region_group": "Sub-Saharan Africa"}, {"country": "Cambodia", "poor_pct": 16.64, "intensity_pct": 42.28, "poor_m": 2.94, "region_group": "Other"}, {"country": "Colombia", "poor_pct": 4.85, "intensity_pct": 40.56, "poor_m": 2.56, "region_group": "Other"}, {"country": "Morocco", "poor_pct": 6.36, "intensity_pct": 41.98, "poor_m": 2.42, "region_group": "Other"}, {"country": "Peru", "poor_pct": 5.87, "intensity_pct": 38.97, "poor_m": 2.01, "region_group": "Other"}, {"country": "Vietnam", "poor_pct": 1.92, "intensity_pct": 40.28, "poor_m": 1.94, "region_group": "Other"}, {"country": "Egypt", "poor_pct": 1.52, "intensity_pct": 37.0, "poor_m": 1.77, "region_group": "Other"}, {"country": "Congo", "poor_pct": 24.27, "intensity_pct": 46.02, "poor_m": 1.54, "region_group": "Sub-Saharan Africa"}, {"country": "Guinea-Bissau", "poor_pct": 64.4, "intensity_pct": 52.91, "poor_m": 1.42, "region_group": "Sub-Saharan Africa"}, {"country": "Lao PDR", "poor_pct": 17.82, "intensity_pct": 46.28, "poor_m": 1.38, "region_group": "Other"}, {"country": "Honduras", "poor_pct": 11.97, "intensity_pct": 42.72, "poor_m": 1.3, "region_group": "Other"}, {"country": "Gambia", "poor_pct": 41.71, "intensity_pct": 47.48, "poor_m": 1.15, "region_group": "Sub-Saharan Africa"}, {"country": "Bolivia", "poor_pct": 5.85, "intensity_pct": 39.63, "poor_m": 0.73, "region_group": "Other"}, {"country": "Timor-Leste", "poor_pct": 48.25, "intensity_pct": 45.91, "poor_m": 0.68, "region_group": "Other"}, {"country": "Sri Lanka", "poor_pct": 2.92, "intensity_pct": 38.29, "poor_m": 0.67, "region_group": "South Asia"}, {"country": "Algeria", "poor_pct": 1.38, "intensity_pct": 39.17, "poor_m": 0.65, "region_group": "Other"}, {"country": "Uzbekistan", "poor_pct": 1.73, "intensity_pct": 35.29, "poor_m": 0.63, "region_group": "Other"}, {"country": "Lesotho", "poor_pct": 25.04, "intensity_pct": 42.36, "poor_m": 0.59, "region_group": "Sub-Saharan Africa"}, {"country": "El Salvador", "poor_pct": 7.86, "intensity_pct": 41.3, "poor_m": 0.5, "region_group": "Other"}, {"country": "Botswana", "poor_pct": 17.22, "intensity_pct": 42.18, "poor_m": 0.43, "region_group": "Sub-Saharan Africa"}, {"country": "Tajikistan", "poor_pct": 3.81, "intensity_pct": 37.54, "poor_m": 0.4, "region_group": "Other"}, {"country": "Ecuador", "poor_pct": 2.09, "intensity_pct": 37.96, "poor_m": 0.38, "region_group": "Other"}, {"country": "Thailand", "poor_pct": 0.49, "intensity_pct": 37.01, "poor_m": 0.35, "region_group": "Other"}, {"country": "Paraguay", "poor_pct": 4.5, "intensity_pct": 41.88, "poor_m": 0.31, "region_group": "Other"}, {"country": "Dominican Republic", "poor_pct": 2.27, "intensity_pct": 38.76, "poor_m": 0.26, "region_group": "Other"}, {"country": "Mongolia", "poor_pct": 7.26, "intensity_pct": 38.75, "poor_m": 0.25, "region_group": "Other"}, {"country": "Gabon", "poor_pct": 8.65, "intensity_pct": 42.39, "poor_m": 0.22, "region_group": "Sub-Saharan Africa"}, {"country": "Argentina", "poor_pct": 0.43, "intensity_pct": 33.99, "poor_m": 0.2, "region_group": "Other"}, {"country": "Comoros", "poor_pct": 19.22, "intensity_pct": 43.86, "poor_m": 0.17, "region_group": "Sub-Saharan Africa"}, {"country": "Libya", "poor_pct": 2.0, "intensity_pct": 37.13, "poor_m": 0.15, "region_group": "Other"}, {"country": "Tunisia", "poor_pct": 0.98, "intensity_pct": 35.21, "poor_m": 0.12, "region_group": "Other"}, {"country": "Eswatini", "poor_pct": 7.9, "intensity_pct": 41.33, "poor_m": 0.1, "region_group": "Sub-Saharan Africa"}, {"country": "Vanuatu", "poor_pct": 27.76, "intensity_pct": 42.06, "poor_m": 0.09, "region_group": "Other"}, {"country": "Jordan", "poor_pct": 0.78, "intensity_pct": 35.33, "poor_m": 0.09, "region_group": "Other"}, {"country": "Jamaica", "poor_pct": 2.78, "intensity_pct": 38.95, "poor_m": 0.08, "region_group": "Other"}, {"country": "Cuba", "poor_pct": 0.71, "intensity_pct": 38.06, "poor_m": 0.08, "region_group": "Other"}, {"country": "Bhutan", "poor_pct": 9.79, "intensity_pct": 39.42, "poor_m": 0.08, "region_group": "South Asia"}, {"country": "Kyrgyzstan", "poor_pct": 0.97, "intensity_pct": 35.19, "poor_m": 0.07, "region_group": "Other"}, {"country": "Kazakhstan", "poor_pct": 0.2, "intensity_pct": 34.87, "poor_m": 0.04, "region_group": "Other"}, {"country": "Palestine, State of", "poor_pct": 0.57, "intensity_pct": 34.97, "poor_m": 0.03, "region_group": "Other"}, {"country": "Costa Rica", "poor_pct": 0.54, "intensity_pct": 37.12, "poor_m": 0.03, "region_group": "Other"}, {"country": "Sao Tome and Principe", "poor_pct": 11.71, "intensity_pct": 40.92, "poor_m": 0.03, "region_group": "Sub-Saharan Africa"}, {"country": "Kiribati", "poor_pct": 19.8, "intensity_pct": 40.48, "poor_m": 0.03, "region_group": "Other"}, {"country": "Albania", "poor_pct": 0.7, "intensity_pct": 39.06, "poor_m": 0.02, "region_group": "Other"}, {"country": "Azerbaijan", "poor_pct": 0.18, "intensity_pct": 37.18, "poor_m": 0.02, "region_group": "Other"}, {"country": "Suriname", "poor_pct": 2.85, "intensity_pct": 39.36, "poor_m": 0.02, "region_group": "Other"}, {"country": "Belize", "poor_pct": 4.3, "intensity_pct": 39.76, "poor_m": 0.02, "region_group": "Other"}, {"country": "Turkmenistan", "poor_pct": 0.23, "intensity_pct": 33.33, "poor_m": 0.02, "region_group": "Other"}, {"country": "Guyana", "poor_pct": 1.82, "intensity_pct": 39.29, "poor_m": 0.02, "region_group": "Other"}, {"country": "Fiji", "poor_pct": 1.51, "intensity_pct": 38.1, "poor_m": 0.01, "region_group": "Other"}, {"country": "Samoa", "poor_pct": 6.29, "intensity_pct": 39.12, "poor_m": 0.01, "region_group": "Other"}, {"country": "Georgia", "poor_pct": 0.34, "intensity_pct": 36.59, "poor_m": 0.01, "region_group": "Other"}, {"country": "Trinidad and Tobago", "poor_pct": 0.53, "intensity_pct": 38.8, "poor_m": 0.01, "region_group": "Other"}, {"country": "Montenegro", "poor_pct": 1.24, "intensity_pct": 39.64, "poor_m": 0.01, "region_group": "Other"}, {"country": "Serbia", "poor_pct": 0.11, "intensity_pct": 38.1, "poor_m": 0.01, "region_group": "Other"}, {"country": "North Macedonia", "poor_pct": 0.37, "intensity_pct": 38.24, "poor_m": 0.01, "region_group": "Other"}, {"country": "Armenia", "poor_pct": 0.19, "intensity_pct": 36.21, "poor_m": 0.01, "region_group": "Other"}, {"country": "Maldives", "poor_pct": 0.77, "intensity_pct": 34.38, "poor_m": 0.0, "region_group": "South Asia"}, {"country": "Seychelles", "poor_pct": 0.87, "intensity_pct": 34.23, "poor_m": 0.0, "region_group": "Sub-Saharan Africa"}, {"country": "Tonga", "poor_pct": 0.87, "intensity_pct": 38.14, "poor_m": 0.0, "region_group": "Other"}, {"country": "Naoero", "poor_pct": 6.81, "intensity_pct": 39.77, "poor_m": 0.0, "region_group": "Other"}, {"country": "Tuvalu", "poor_pct": 2.11, "intensity_pct": 38.24, "poor_m": 0.0, "region_group": "Other"}]
def area(p):
    return 25 + p * 12.0
COL = {"Sub-Saharan Africa": RED, "South Asia": BLUE, "Other": GOLD}
fig = new_figure(9.2, 7.0); ax = fig.add_subplot(111)
for r in DATA:
    ax.scatter(r["poor_pct"], r["intensity_pct"], s=area(r["poor_m"]), facecolor=COL[r["region_group"]], alpha=0.5, edgecolor="white", lw=0.5, zorder=3, clip_on=False)
BY = {r["country"]: r for r in DATA}
def lab(n, ux, uy):
    r = BY[n]; rad = np.sqrt(area(r["poor_m"]) / np.pi) + 4
    ax.annotate(n, (r["poor_pct"], r["intensity_pct"]), xytext=(ux * rad, uy * rad), textcoords="offset points", fontsize=10.5, color=INK,
                ha="right" if ux < 0 else ("left" if ux > 0 else "center"), va="center" if uy == 0 else ("bottom" if uy > 0 else "top"), zorder=5)
lab("India", 1, 0); lab("China", 0.8, -0.9); lab("Pakistan", -0.6, 0.9); lab("Nigeria", -0.7, 0.8); lab("Ethiopia", 0.7, -0.9)
lab("DR Congo", 0, -1); lab("Afghanistan", -0.9, 1.1); lab("Niger", -0.7, 0.8); lab("Chad", 1, 0); lab("Bangladesh", -0.5, 1)
for mval, kxx in zip([200, 50, 10], [66, 76, 84]):
    ax.scatter(kxx, 37.5, s=area(mval), facecolor="none", edgecolor="#666", lw=0.8, zorder=3)
    ax.text(kxx, 34.0, f"{mval}m", ha="center", va="top", fontsize=10.5, color="#666")
ax.text(76, 41.8, "Bubble area: number of poor", ha="center", va="bottom", fontsize=10.5, color="#666")
ax.set_xlim(0, 92); ax.set_ylim(32, 65)
ax.set_xlabel("Share of population in acute multidimensional poverty, % (breadth)"); ax.set_ylabel("Average deprivation score of the poor, % (depth)")
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=RED, alpha=0.7, ms=9, label="Sub-Saharan Africa"), Line2D([], [], marker="o", ls="", color=BLUE, alpha=0.7, ms=9, label="South Asia"),
                   Line2D([], [], marker="o", ls="", color=GOLD, alpha=0.7, ms=9, label="Other regions")], loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
compose(render_plot(fig), title="Where multidimensional poverty is the deepest it is also the broadest",
        subtitle="Poverty rate against the average intensity of deprivation among the poor, 108 countries, bubbles sized by number of poor",
        source='UNDP and OPHI, 2026 global Multidimensional Poverty Index statistical update (October 2026), Table 1.', note="Intensity is the average share of weighted indicators in which a poor person is deprived; a third is the threshold for being poor and a half for severe poverty. Bubble area is proportional to the number of poor people. Ten countries are labelled: the largest by number of poor and the two with the highest intensity.",
        out=OUT + ".png", csv=OUT + ".csv", csv_rows=[list(DATA[0].keys())] + [list(r.values()) for r in DATA])
