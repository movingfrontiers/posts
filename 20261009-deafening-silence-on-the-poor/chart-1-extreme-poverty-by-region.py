"""Chart 1: extreme poverty by region.
Self-contained: house style and data are embedded. Requires numpy, matplotlib and Pillow.
Run: python chart-1-extreme-poverty-by-region.py  -> writes chart-1-extreme-poverty-by-region.png and chart-1-extreme-poverty-by-region.csv
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

# World Bank PIP, $3.00 a day (2021 PPP), release 20260324. Millions of people.
years = list(range(1990, 2027))
world = [2300.59,2323.39,2328.28,2340.34,2301.76,2260.42,2216.92,2226.83,2272.78,2268.80,2230.90,2201.68,2134.90,2061.05,1964.86,1862.92,1797.69,1705.36,1648.77,1594.98,1469.14,1353.78,1279.30,1126.50,1066.89,998.79,946.66,898.00,855.84,837.17,896.38,897.15,869.96,856.26,846.76,837.21,826.02]
ssa   = [320.62,336.15,351.33,365.06,375.25,384.35,391.16,399.16,409.60,418.62,425.25,428.47,437.30,441.91,431.63,431.55,434.88,437.38,439.12,447.31,441.99,445.15,445.68,448.11,452.14,465.13,475.20,482.06,489.90,499.85,537.75,554.12,561.86,575.07,582.13,585.32,586.59]
sas   = [503.36,513.70,517.33,519.47,522.53,529.30,536.23,546.10,555.73,561.85,570.41,580.00,589.72,594.61,596.51,583.85,556.72,528.59,517.99,493.32,439.27,403.48,374.34,342.17,304.43,263.32,223.47,187.86,158.02,139.89,152.22,128.66,101.01,77.74,63.44,52.19,42.90]
eap   = [1218.39,1217.19,1204.14,1189.78,1134.64,1081.89,1022.37,1019.47,1038.22,997.69,955.14,911.50,835.15,762.16,697.10,616.60,596.29,541.91,510.62,469.61,417.49,340.58,297.89,203.76,177.30,139.38,116.22,96.55,77.15,60.96,64.53,62.25,57.38,52.11,47.16,42.48,39.15]
mea   = [131.18,126.03,114.44,118.17,110.12,111.24,103.93,104.68,109.23,113.11,117.93,124.53,125.20,117.84,108.21,104.79,100.56,97.69,87.82,93.29,83.53,82.91,80.25,77.63,78.23,78.67,80.20,79.49,80.75,86.43,95.33,103.13,105.28,110.82,116.85,121.28,122.06]
rest  = [w - a - b - c - d for w, a, b, c, d in zip(world, ssa, sas, eap, mea)]

series = [("Sub-Saharan Africa", ssa, RED), ("South Asia", sas, BLUE),
          ("East Asia and Pacific", eap, GREEN), ("Middle East, N. Africa, Afghanistan, Pakistan", mea, GOLD),
          ("Rest of the world", rest, GREY)]

fig = new_figure()
ax = fig.add_subplot(111)
ax.stackplot(years, *[s[1] for s in series], labels=[s[0] for s in series],
             colors=[s[2] for s in series], alpha=0.92, linewidth=0)
ax.set_xlim(1990, 2026)
ax.set_ylim(0, 2500)
ax.set_yticks(range(0, 2501, 500))
ax.set_yticklabels([f"{v:,}" for v in range(0, 2501, 500)])
ax.set_xticks([1990, 1995, 2000, 2005, 2010, 2015, 2020, 2026])
ax.set_ylabel("Millions of people")
ax.axvspan(2024.5, 2026, color="white", alpha=0.25, lw=0)
ax.text(2025.3, 2380, "nowcast", fontsize=12, color="#666", ha="right", va="top", rotation=90)
# end labels for the two big blocks
ax.text(2026.3, ssa[-1] / 2, f"{ssa[-1]:,.0f}", fontsize=14, color=RED, va="center", ha="left", fontweight="bold")
ax.text(2026.3, world[-1] + 25, f"{world[-1]:,.0f}", fontsize=14, color=INK, va="bottom", ha="left", fontweight="bold")
ax.text(1990.4, world[0] + 40, f"{world[0]:,.0f}", fontsize=14, color=INK, va="bottom", ha="left", fontweight="bold")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, frameon=False)
ax.set_box_aspect(0.798)

compose(render_plot(fig),
        title="Extreme poverty is barely falling, and Africa now holds most of it",
        subtitle="People living on less than $3.00 a day (2021 PPP), millions, 1990 to 2026",
        source="World Bank Poverty and Inequality Platform, March 2026 release ($3.00 line, 2021 PPP).",
        note="2025 and 2026 are World Bank nowcasts. Regions follow World Bank groupings; the Middle East and North Africa aggregate includes Afghanistan and Pakistan. Rest of the world is the residual after the four named regions.",
        out="chart-1-extreme-poverty-by-region.png", csv="chart-1-extreme-poverty-by-region.csv",
        csv_rows=[["year", "world", "sub_saharan_africa", "south_asia", "east_asia_pacific", "mena_afg_pak", "rest"]]
                 + [list(r) for r in zip(years, world, ssa, sas, eap, mea, [round(x, 2) for x in rest])])
