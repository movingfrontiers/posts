# Chart 1: China's real GDP growth and its trend
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
NAME = "chart-1-growth-and-trend"
# Real GDP growth, percent. IMF World Economic Outlook, October 2026 (DataMapper NGDP_RPCH).
# 1980-2025 actual, 2026-2031 IMF projections.
G = {1980: 7.9, 1981: 5.1, 1982: 9.0, 1983: 10.8, 1984: 15.2, 1985: 13.5, 1986: 8.9, 1987: 11.7, 1988: 11.2, 1989: 4.2, 1990: 3.9, 1991: 10.2, 1992: 14.3, 1993: 13.9, 1994: 13.1, 1995: 11.0, 1996: 10.0, 1997: 9.3, 1998: 7.9, 1999: 7.8, 2000: 8.6, 2001: 8.3, 2002: 9.2, 2003: 10.1, 2004: 10.1, 2005: 11.4, 2006: 12.7, 2007: 14.2, 2008: 9.6, 2009: 9.4, 2010: 10.6, 2011: 9.5, 2012: 7.8, 2013: 7.8, 2014: 7.5, 2015: 7.0, 2016: 6.8, 2017: 6.9, 2018: 6.8, 2019: 6.1, 2020: 2.3, 2021: 8.6, 2022: 3.1, 2023: 5.4, 2024: 5.0, 2025: 5.0, 2026: 4.5, 2027: 4.0, 2028: 4.0, 2029: 3.7, 2030: 3.3, 2031: 3.3}
X = np.array(sorted(G)); Y = np.array([G[x] for x in X])
LAMBDA = 100

def hp(y, lam):
    n = len(y); d2 = np.diff(np.eye(n), 2, axis=0)
    return np.linalg.solve(np.eye(n) + lam * d2.T @ d2, y)

TR = hp(Y, LAMBDA)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    ax.bar(X, Y, 0.72, color=[NAVY if x <= 2025 else SKY for x in X], zorder=2)
    ax.plot(X, TR, color=RED, lw=5.5, solid_capstyle="round", zorder=3)
    i = int(np.argmax(TR))
    ax.plot(X[i], TR[i], "o", color=RED, ms=13, zorder=4)
    ax.plot([X[i], X[i] + 3.2], [TR[i], 15.4], color=RED, lw=2, zorder=3)
    ax.text(X[i] + 3.6, 15.4, f"Trend peak {TR[i]:.1f} ({X[i]})", color=RED, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="left", va="center")
    ax.plot(X[-1], TR[-1], "o", color=RED, ms=13, zorder=4)
    ax.text(X[-1] + 0.8, TR[-1], f"Trend\n{TR[-1]:.1f}", color=RED, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="left", va="center", linespacing=1.05)
    ax.text(2028.5, 6.2, "IMF\nprojection", color=SKY, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, ha="center", va="bottom", linespacing=1.05)
    ax.set_xlim(1978.8, 2035.8); ax.set_ylim(0, 16.5)
    ax.set_xticks(range(1980, 2031, 10)); ax.set_yticks(range(0, 17, 4))

compose(plot, "China's trend growth peaked in 2006",
        "Real GDP growth, percent",
        "Source: IMF, World Economic Outlook, October 2026.\nNote: The trend is a Hodrick-Prescott filter (lambda 100) run over 1980 to 2031, including the IMF projections for 2026 to 2031.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "real GDP growth (%)", "trend (%)", "status"],
          [[int(x), y, round(t, 2), "actual" if x <= 2025 else "IMF projection"] for x, y, t in zip(X, Y, TR)])
