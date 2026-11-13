# Chart 6: working-age population, China and Japan, aligned on the peak
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
NAME = "chart-6-working-age-population"
# Population aged 15 to 64, millions. World Bank Population Estimates and Projections (source 40),
# July 2026 update; values after 2025 are projections. Japan peaked in 1995, China in 2015.
JPN = {1995: 87.457, 1996: 87.36, 1997: 87.196, 1998: 87.046, 1999: 86.805, 2000: 86.479, 2001: 86.141, 2002: 85.802, 2003: 85.517, 2004: 85.008, 2005: 84.286, 2006: 83.557, 2007: 82.918, 2008: 82.235, 2009: 81.67, 2010: 81.364, 2011: 80.609, 2012: 79.502, 2013: 78.376, 2014: 77.388, 2015: 76.58, 2016: 75.947, 2017: 75.44, 2018: 75.026, 2019: 74.719, 2020: 74.319, 2021: 73.819, 2022: 73.496, 2023: 73.202, 2024: 72.877, 2025: 72.5, 2026: 72.027, 2027: 71.531, 2028: 70.999, 2029: 70.408, 2030: 69.739, 2031: 69.193, 2032: 68.577, 2033: 67.745, 2034: 66.879, 2035: 65.936, 2036: 64.918, 2037: 63.841, 2038: 62.71, 2039: 61.577, 2040: 60.543, 2041: 59.615, 2042: 58.776, 2043: 58.0, 2044: 57.281, 2045: 56.619, 2046: 56.016, 2047: 55.454, 2048: 54.905, 2049: 54.367, 2050: 53.863}
CHN = {2015: 988.372, 2016: 988.168, 2017: 986.648, 2018: 984.111, 2019: 981.778, 2020: 979.302, 2021: 977.528, 2022: 975.76, 2023: 974.72, 2024: 976.799, 2025: 980.126, 2026: 983.374, 2027: 983.812, 2028: 978.361, 2029: 971.405, 2030: 965.099, 2031: 958.657, 2032: 953.31, 2033: 945.392, 2034: 934.264, 2035: 921.323, 2036: 906.679, 2037: 891.859, 2038: 877.009, 2039: 862.916, 2040: 850.431, 2041: 839.159, 2042: 828.81, 2043: 818.996, 2044: 808.675, 2045: 797.591, 2046: 785.807, 2047: 772.852, 2048: 760.164, 2049: 748.02, 2050: 734.856}
SER = [("Japan", JPN, 1995, NAVY), ("China", CHN, 2015, RED)]

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for name, d, peak, col in SER:
        yrs = np.array(sorted(d)); idx = np.array([100 * d[y] / d[peak] for y in yrs]); t = yrs - peak
        a = yrs <= 2025
        ax.plot(t[a], idx[a], color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(t[~a | (yrs == 2025)], idx[~a | (yrs == 2025)], color=col, lw=5.5, dashes=(1.2, 1.2), zorder=3)
        k = int(np.where(yrs == 2025)[0][0])
        ax.plot(t[k], idx[k], "o", color=col, ms=13, zorder=4)
        ax.text(t[k], idx[k] + 2.2, "2025", color=col, fontfamily=CALIBRI, fontweight="bold",
                fontsize=S_VALUE, ha="center", va="bottom")
        if name == "China":
            ax.text(t[-1] - 1.0, idx[-1] - 1.5, f"{name}\n{idx[-1]:.0f} in 2050", color=col, fontfamily=CALIBRI,
                    fontweight="bold", fontsize=S_VALUE, ha="right", va="top", linespacing=1.05)
        else:
            end_label(ax, t[-1], idx[-1], f"{name}\n{idx[-1]:.0f} in 2050", col, dx=0.9)
    ax.set_xlim(-1, 66); ax.set_ylim(50, 106)
    ax.set_xticks(range(0, 56, 10)); ax.set_yticks(range(50, 101, 10))

compose(plot, "China's workforce follows Japan's path",
        "Population aged 15 to 64, index (peak year = 100), by years since the peak",
        "Source: World Bank, Population Estimates and Projections, July 2026 update.\nNote: Japan's working-age population peaked in 1995 and China's in 2015. Dotted lines are projections.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = [[y, "Japan", JPN[y], round(100 * JPN[y] / JPN[1995], 2), y - 1995] for y in sorted(JPN)] + \
       [[y, "China", CHN[y], round(100 * CHN[y] / CHN[2015], 2), y - 2015] for y in sorted(CHN)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "aged 15-64 (million)", "index (peak = 100)", "years since peak"], rows)
