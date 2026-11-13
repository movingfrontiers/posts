# Chart 3: growth accounting for China
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
NAME = "chart-3-growth-accounting"
# Growth accounting, percentage points a year (log differences).
# GDP: official real growth (World Bank WDI, NY.GDP.MKTP.KD.ZG). Capital stock (rnna), employment (emp),
# human capital index (hc) and labour share (labsh, period average): Penn World Table 10.01.
# Contribution of capital = (1 - labour share) x capital growth; workers and skills = labour share x growth.
# Productivity (TFP) is the residual. Columns: label, start, end, GDP, capital, workers, skills, TFP, labour share.
R = [['1980s', 1980, 1990, np.float64(8.88), np.float64(3.21), np.float64(1.83), np.float64(0.7), np.float64(3.13), np.float64(0.592)], ['1990s', 1990, 2000, np.float64(9.98), np.float64(4.12), np.float64(0.63), np.float64(0.98), np.float64(4.24), np.float64(0.585)], ['2000s', 2000, 2010, np.float64(10.04), np.float64(5.02), np.float64(0.34), np.float64(0.31), np.float64(4.37), np.float64(0.571)], ['2010s', 2010, 2019, np.float64(7.08), np.float64(4.4), np.float64(0.14), np.float64(0.64), np.float64(1.89), np.float64(0.574)]]
SER = [("Capital", 4, NAVY), ("Workers", 5, GOLD), ("Skills", 6, SKY), ("Productivity", 7, RED)]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax)
    x = np.arange(len(R))
    bottom = np.zeros(len(R))
    for name, j, col in SER:
        v = np.array([r[j] for r in R])
        ax.bar(x, v, 0.6, bottom=bottom, color=col, zorder=2, edgecolor="white", linewidth=2)
        for xi, b, vi in zip(x, bottom, v):
            if vi >= 0.9:
                ax.text(xi, b + vi / 2, f"{vi:.1f}", color="white", fontfamily=CALIBRI, fontweight="bold",
                        fontsize=S_VALUE, ha="center", va="center")
        ax.text(-0.42, bottom[0] + v[0] / 2, name, color=col, fontfamily=CALIBRI, fontweight="bold",
                fontsize=S_VALUE, ha="right", va="center")
        bottom = bottom + v
    for xi, r in zip(x, R):
        ax.text(xi, r[3] + 0.25, f"{r[3]:.1f}", color=INK, fontfamily=CALIBRI, fontweight="bold",
                fontsize=S_VALUE, ha="center", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in R])
    ax.set_xlim(-1.75, len(R) - 0.5); ax.set_ylim(0, 11.2)

compose(plot, "Productivity growth has halved",
        "Contributions to China's real GDP growth, percentage points a year",
        "Source: Penn World Table 10.01; World Bank, World Development Indicators.\nNote: Productivity is total factor productivity, the residual after capital, employment and human capital (skills). The last period ends in 2019, the final year of the Penn World Table.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"),
          ["period", "start", "end", "GDP growth", "capital", "workers", "skills", "productivity (TFP)", "labour share"], R)
