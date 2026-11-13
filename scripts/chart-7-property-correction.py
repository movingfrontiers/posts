# Chart 7: property investment and real house prices
# ---- house style (inlined) -------------------------------------------------
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H, M, DPI = 2160, 2160, 150, 200
PX = 72 / DPI
GAP_TITLE_UNIT, GAP_UNIT_EXPL, GAP_HEAD_PLOT, GAP_PLOT_CAP, GAP_CAP_MARK = 34, 22, 70, 70, 90
NAVY, RED, SKY, GOLD = "#0B2265", "#D0412F", "#5B8FCC", "#C9962B"
INK, GREY_TXT, LABEL, BAND = "#111111", "#555555", "#333333", "#E6EAF2"
T_TITLE, T_UNIT, T_SOFT = (17, 17, 17), (34, 34, 34), (95, 95, 95)
FD = "/usr/share/fonts/truetype/"
F_REG, F_BOLD = FD + "liberation/LiberationSans-Regular.ttf", FD + "liberation/LiberationSans-Bold.ttf"
F_CAL, F_CALB = FD + "crosextra/Carlito-Regular.ttf", FD + "crosextra/Carlito-Bold.ttf"
for f in (F_REG, F_BOLD, F_CAL, F_CALB):
    fm.fontManager.addfont(f)
ARIAL, CALIBRI = "Liberation Sans", "Carlito"
S_TICK, S_LABEL, S_VALUE, S_HEAD = 42 * PX, 46 * PX, 47 * PX, 54 * PX
plt.rcParams.update({"font.family": ARIAL, "font.size": S_TICK, "axes.unicode_minus": False})

def style_axes(ax, yticks=False):
    ax.grid(False)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INK); ax.spines["bottom"].set_linewidth(1.6)
    ax.tick_params(axis="x", direction="out", length=12, width=1.6, pad=10, colors=INK, labelsize=S_TICK)
    ax.tick_params(axis="y", length=0, pad=10, colors=LABEL, labelsize=S_TICK)
    if not yticks:
        ax.set_yticks([])

def zero_line(ax, x0=None, x1=None):
    lo, hi = ax.get_xlim()
    ax.plot([lo if x0 is None else x0, hi if x1 is None else x1], [0, 0], color=INK, lw=2.6,
            dashes=(1, 1.6), zorder=1)
    ax.set_xlim(lo, hi)

def _wrap(d, text, font, width):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= width or not line:
                line = t
            else:
                out.append(line); line = w
        out.append(line)
    return "\n".join(out)

def _block(d, text, font, ls, y, fill, x=M, draw=True):
    sp = (ls - 1) * font.size
    b = d.multiline_textbbox((0, 0), text, font=font, spacing=sp)
    if draw:
        d.multiline_text((x - b[0], y - b[1]), text, font=font, spacing=sp, fill=fill)
    return int(round(y + (b[3] - b[1])))

def _ink(im):
    return ImageChops.difference(im.convert("RGB"), Image.new("RGB", im.size, "white")).getbbox()

def compose(plot_fn, title, unit, caption, out, expl=None):
    canvas = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(canvas)
    ft, fu, fe = ImageFont.truetype(F_BOLD, 92), ImageFont.truetype(F_REG, 54), ImageFont.truetype(F_REG, 42)
    fc, fw = ImageFont.truetype(F_REG, 37), ImageFont.truetype(F_BOLD, 48)
    cw = W - 2 * M
    y = _block(d, _wrap(d, title, ft, cw), ft, 1.18, M, T_TITLE)
    y = _block(d, _wrap(d, unit, fu, cw), fu, 1.3, y + GAP_TITLE_UNIT, T_UNIT)
    if expl:
        y = _block(d, _wrap(d, expl, fe, cw), fe, 1.42, y + GAP_UNIT_EXPL, T_SOFT)
    mark = "Moving Frontiers"
    mb = d.textbbox((0, 0), mark, font=fw)
    cap = _wrap(d, caption, fc, cw - GAP_CAP_MARK - (mb[2] - mb[0]))
    ch = _block(d, cap, fc, 1.42, 0, T_SOFT, draw=False)
    cap_top = int(H - M - ch)
    _block(d, cap, fc, 1.42, cap_top, T_SOFT)
    d.text((int(W - M - mb[2]), int(H - M - mb[3])), mark, font=fw, fill=NAVY)
    top, th = y + GAP_HEAD_PLOT, cap_top - GAP_PLOT_CAP - (y + GAP_HEAD_PLOT)
    fw_in, fh_in = cw / DPI, th / DPI
    tmp = out + ".tmp.png"
    for _ in range(6):
        fig = plt.figure(figsize=(fw_in, fh_in), dpi=DPI)
        plot_fn(fig)
        fig.savefig(tmp, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.05); plt.close(fig)
        im = Image.open(tmp).convert("RGB"); b = _ink(im)
        iw, ih = b[2] - b[0], b[3] - b[1]
        if abs(iw - cw) <= 2 and 0 <= th - ih <= 8:
            break
        fw_in += (cw - iw) / DPI; fh_in += (th - 3 - ih) / DPI
    b = (b[0], b[1], min(b[2], b[0] + cw), b[3])
    canvas.paste(im.crop(b), (M, top)); os.remove(tmp)
    canvas.save(out, dpi=(DPI, DPI))
    verify(out, top, ih, cap_top)

def verify(out, top, ih, cap_top):
    b = _ink(Image.open(out))
    assert b[0] == M and b[1] == M and b[3] == H - M and b[2] <= W - M, ("margins", b)
    assert 0 <= cap_top - (top + ih) - GAP_PLOT_CAP <= 8, ("plot to caption gap", cap_top - top - ih)

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

HERE = os.path.dirname(os.path.abspath(__file__))
# ---- end house style -------------------------------------------------------
NAME = "chart-7-property-correction"
# Real estate development investment, RMB trillion (NBS annual releases, levels as published).
INV = {2015: 9.5979, 2016: 10.2581, 2017: 10.9799, 2018: 12.0264, 2019: 13.2194, 2020: 14.1443, 2021: 14.7602, 2022: 13.2895, 2023: 11.0913, 2024: 10.028, 2025: 8.2788}
# Real residential property prices, index 2010 = 100 (BIS, WS_SPP Q.CN.R.628).
BQ = {'2015-Q1': 93.769, '2015-Q2': 93.824, '2015-Q3': 93.834, '2015-Q4': 94.259, '2016-Q1': 94.907, '2016-Q2': 97.163, '2016-Q3': 99.11, '2016-Q4': 100.935, '2017-Q1': 101.195, '2017-Q2': 103.497, '2017-Q3': 104.284, '2017-Q4': 104.228, '2018-Q1': 103.56, '2018-Q2': 105.809, '2018-Q3': 108.075, '2018-Q4': 109.439, '2019-Q1': 109.458, '2019-Q2': 110.552, '2019-Q3': 110.351, '2019-Q4': 108.746, '2020-Q1': 107.159, '2020-Q2': 109.938, '2020-Q3': 110.307, '2020-Q4': 111.214, '2021-Q1': 110.553, '2021-Q2': 112.631, '2021-Q3': 112.991, '2021-Q4': 111.088, '2022-Q1': 109.33, '2022-Q2': 107.829, '2022-Q3': 106.451, '2022-Q4': 105.043, '2023-Q1': 104.343, '2023-Q2': 104.847, '2023-Q3': 103.135, '2023-Q4': 101.475, '2024-Q1': 98.963, '2024-Q2': 96.851, '2024-Q3': 93.823, '2024-Q4': 92.597, '2025-Q1': 91.615, '2025-Q2': 90.676, '2025-Q3': 88.851, '2025-Q4': 86.79, '2026-Q1': 85.134, '2026-Q2': 84.37}
I21 = INV[2021]
P21 = np.mean([BQ[f"2021-Q{q}"] for q in range(1, 5)])

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    xi = np.array(sorted(INV)) + 0.5; yi = np.array([100 * INV[y] / I21 for y in sorted(INV)])
    ax.plot(xi, yi, color=NAVY, lw=5.5, marker="o", ms=12, zorder=3)
    qs = sorted(BQ); xq = np.array([int(q[:4]) + (int(q[-1]) - 0.5) / 4 for q in qs])
    yq = np.array([100 * BQ[q] / P21 for q in qs])
    ax.plot(xq, yq, color=RED, lw=5.5, solid_capstyle="round", zorder=3)
    end_label(ax, xi[-1], yi[-1], f"Investment\n{yi[-1]:.0f}", NAVY, dx=0.25)
    end_label(ax, xq[-1], yq[-1], f"Real house\nprices {yq[-1]:.0f}", RED, dx=0.25)
    ax.set_xlim(2014.8, 2029.6); ax.set_ylim(50, 106)
    ax.set_xticks(range(2015, 2027, 2)); ax.set_yticks(range(50, 101, 10))

compose(plot, "Property investment has nearly halved",
        "China's property sector, index (2021 = 100)",
        "Source: National Bureau of Statistics of China; Bank for International Settlements.\nNote: Investment is in current yuan. The BIS price index builds on new-home prices and likely understates the fall in resale prices.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = [[y, "investment (RMB tn)", INV[y], round(100 * INV[y] / I21, 1)] for y in sorted(INV)] + \
       [[q, "real house price index (2010=100)", BQ[q], round(100 * BQ[q] / P21, 1)] for q in sorted(BQ)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["period", "series", "value", "index (2021 = 100)"], rows)
