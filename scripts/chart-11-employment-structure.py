# Chart 11: employment by sector
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
NAME = "chart-11-employment-structure"
# Share of total employment by sector, percent. World Bank WDI (ILO modelled estimates):
# SL.AGR.EMPL.ZS, SL.IND.EMPL.ZS, SL.SRV.EMPL.ZS. China, 1991-2025.
AG = {1991: 59.6, 1992: 58.5, 1993: 56.4, 1994: 54.3, 1995: 52.2, 1996: 50.5, 1997: 49.9, 1998: 49.8, 1999: 50.1, 2000: 50.0, 2001: 50.0, 2002: 50.0, 2003: 49.1, 2004: 46.9, 2005: 44.8, 2006: 42.6, 2007: 40.8, 2008: 39.6, 2009: 38.1, 2010: 36.7, 2011: 34.8, 2012: 33.6, 2013: 31.4, 2014: 29.5, 2015: 28.3, 2016: 27.4, 2017: 26.7, 2018: 25.8, 2019: 24.7, 2020: 23.6, 2021: 22.9, 2022: 24.1, 2023: 22.8, 2024: 22.2, 2025: 21.7}
IN = {1991: 21.4, 1992: 21.7, 1993: 22.4, 1994: 22.7, 1995: 23.0, 1996: 23.5, 1997: 23.7, 1998: 23.5, 1999: 23.0, 2000: 24.6, 2001: 22.3, 2002: 21.4, 2003: 21.6, 2004: 22.5, 2005: 23.8, 2006: 25.2, 2007: 26.8, 2008: 27.2, 2009: 27.8, 2010: 28.7, 2011: 29.5, 2012: 30.3, 2013: 30.1, 2014: 29.9, 2015: 29.3, 2016: 29.6, 2017: 30.0, 2018: 30.4, 2019: 30.8, 2020: 31.1, 2021: 31.5, 2022: 30.9, 2023: 31.4, 2024: 31.6, 2025: 31.8}
SV = {1991: 18.9, 1992: 19.8, 1993: 21.2, 1994: 23.0, 1995: 24.8, 1996: 26.0, 1997: 26.4, 1998: 26.7, 1999: 26.9, 2000: 25.3, 2001: 27.7, 2002: 28.6, 2003: 29.3, 2004: 30.6, 2005: 31.4, 2006: 32.2, 2007: 32.4, 2008: 33.2, 2009: 34.1, 2010: 34.6, 2011: 35.7, 2012: 36.1, 2013: 38.5, 2014: 40.6, 2015: 42.4, 2016: 42.9, 2017: 43.3, 2018: 43.9, 2019: 44.5, 2020: 45.3, 2021: 45.6, 2022: 45.0, 2023: 45.8, 2024: 46.2, 2025: 46.5}

def end_label(ax, x, y, text, col, dy=0, dx=0.6):
    ax.text(x + dx, y + dy, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    for d, col, name, dy in [(SV, NAVY, "Services", 0), (IN, GOLD, "Industry", 1.2), (AG, RED, "Agriculture", -1.6)]:
        x = sorted(d); y = [d[k] for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=4)
        end_label(ax, x[-1], y[-1], f"{name} {y[-1]:.0f}", col, dy=dy)
    ax.set_xlim(1990, 2038); ax.set_ylim(10, 62)
    ax.set_xticks(range(1995, 2026, 10)); ax.set_yticks(range(10, 61, 10))

compose(plot, "Services employ almost half of workers",
        "Share of total employment by sector, percent",
        "Source: World Bank, World Development Indicators (ILO modelled estimates).\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "agriculture (%)", "industry (%)", "services (%)"],
          [[y, AG.get(y), IN.get(y), SV.get(y)] for y in sorted(AG)])
