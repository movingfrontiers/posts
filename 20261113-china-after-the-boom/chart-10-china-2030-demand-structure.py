# Chart 10: China 2030 demand structure against outcomes
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
NAME = "chart-10-china-2030-demand-structure"
# China 2030 (World Bank and DRC, 2013), table 1.1: reform-scenario paths for consumption and investment,
# percent of GDP, end of period. Outcome: World Bank WDI, final consumption expenditure (NE.CON.TOTL.ZS)
# and gross capital formation (NE.GDI.TOTL.ZS). The report's 2010 base (47 and 49) predates data revisions.
PC = {2010: 47, 2015: 56, 2020: 60, 2025: 63, 2030: 66}
PI = {2010: 49, 2015: 42, 2020: 38, 2025: 36, 2030: 34}
AC = {2010: 49.4, 2011: 50.8, 2012: 51.6, 2013: 52.1, 2014: 52.9, 2015: 54.3, 2016: 55.6, 2017: 55.5, 2018: 55.8, 2019: 56.5, 2020: 55.8, 2021: 54.7, 2022: 54.4, 2023: 56.8, 2024: 56.7}
AI = {2010: 46.1, 2011: 46.3, 2012: 45.8, 2013: 45.9, 2014: 45.3, 2015: 42.7, 2016: 42.1, 2017: 42.5, 2018: 43.3, 2019: 42.7, 2020: 42.6, 2021: 42.7, 2022: 42.4, 2023: 41.1, 2024: 40.5}

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for d, col in [(PC, NAVY), (PI, RED)]:
        x = sorted(d); ax.plot(x, [d[k] for k in x], color=col, lw=4.5, dashes=(1.2, 1.2), marker="o", ms=12, mfc="white", mew=3.5, zorder=3)
    for d, col in [(AC, NAVY), (AI, RED)]:
        x = sorted(d); ax.plot(x, [d[k] for k in x], color=col, lw=5.5, solid_capstyle="round", zorder=4)
        ax.plot(x[-1], d[x[-1]], "o", color=col, ms=14, zorder=5)
    def lab(x, y, t, col, ha="left", va="center"):
        ax.text(x, y, t, color=col, fontfamily=CALIBRI, fontweight="bold", fontsize=S_VALUE, ha=ha, va=va, linespacing=1.05)
    lab(2030.6, 66, "Scenario\n66", NAVY); lab(2030.6, 34, "Scenario\n34", RED)
    lab(2024.5, AC[2024] - 2.6, f"Consumption\n{AC[2024]:.0f} in 2024", NAVY, ha="center", va="top")
    lab(2024.5, AI[2024] + 2.4, f"Investment\n{AI[2024]:.0f} in 2024", RED, ha="center", va="bottom")
    ax.set_xlim(2009, 2035.5); ax.set_ylim(30, 70)
    ax.set_xticks(range(2010, 2031, 5)); ax.set_yticks(range(30, 71, 10))

compose(plot, "Demand rebalanced at half the pace",
        "Consumption and investment, percent of GDP: scenario and outcome",
        "Source: World Bank and Development Research Center of the State Council, China 2030 (2013); World Bank, World Development Indicators.\nNote: Consumption is household plus government. The report's 2010 starting values differ from current data because of later revisions.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = [[y, PC.get(y), PI.get(y), AC.get(y), AI.get(y)] for y in range(2010, 2031)]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "scenario consumption", "scenario investment", "actual consumption", "actual investment"], rows)
