# Chart 17: research and development spending
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
NAME = "chart-17-research-and-development"
# World Bank, World Development Indicators: research and development expenditure, percent of GDP (GB.XPD.RSDV.GD.ZS)
RD = {'CHN': {2023: 2.577, 2022: 2.494, 2021: 2.382, 2020: 2.357, 2019: 2.201, 2018: 2.102, 2017: 2.078, 2016: 2.059, 2015: 2.017, 2014: 1.985, 2013: 1.962, 2012: 1.881, 2011: 1.752, 2010: 1.685, 2009: 1.637, 2008: 1.423, 2007: 1.353, 2006: 1.349, 2005: 1.29, 2004: 1.197, 2003: 1.105, 2002: 1.044, 2001: 0.929, 2000: 0.884, 1999: 0.743, 1998: 0.642, 1997: 0.635, 1996: 0.56}, 'JPN': {2023: 3.441, 2022: 3.401, 2021: 3.274, 2020: 3.266, 2019: 3.218, 2018: 3.219, 2017: 3.166, 2016: 3.107, 2015: 3.241, 2014: 3.368, 2013: 3.279, 2012: 3.174, 2011: 3.205, 2010: 3.105, 2009: 3.196, 2008: 3.292, 2007: 3.293, 2006: 3.228, 2005: 3.131, 2004: 2.981, 2003: 2.993, 2002: 2.965, 2001: 2.923, 2000: 2.858, 1999: 2.847, 1998: 2.827, 1997: 2.722, 1996: 2.643}, 'USA': {2023: 3.447, 2022: 3.487, 2021: 3.469, 2020: 3.418, 2019: 3.143, 2018: 2.99, 2017: 2.883, 2016: 2.837, 2015: 2.773, 2014: 2.709, 2013: 2.696, 2012: 2.673, 2011: 2.738, 2010: 2.714, 2009: 2.792, 2008: 2.745, 2007: 2.615, 2006: 2.545, 2005: 2.502, 2004: 2.487, 2003: 2.55, 2002: 2.547, 2001: 2.637, 2000: 2.62, 1999: 2.544, 1998: 2.496, 1997: 2.477, 1996: 2.45}, 'KOR': {2023: 4.944, 2022: 4.848, 2021: 4.597, 2020: 4.521, 2019: 4.364, 2018: 4.272, 2017: 4.073, 2016: 3.786, 2015: 3.789, 2014: 3.89, 2013: 3.775, 2012: 3.685, 2011: 3.444, 2010: 3.179, 2009: 3.021, 2008: 2.868, 2007: 2.759, 2006: 2.615, 2005: 2.427, 2004: 2.353, 2003: 2.197, 2002: 2.13, 2001: 2.199, 2000: 2.049, 1999: 1.945, 1998: 2.036, 1997: 2.174, 1996: 2.142}, 'WLD': {2023: 2.597, 2022: 2.571, 2021: 2.523, 2020: 2.456, 2019: 2.263, 2018: 2.218, 2017: 2.142, 2016: 2.149, 2015: 2.104, 2014: 2.087, 2013: 1.975, 2012: 2.013, 2011: 1.982, 2010: 1.999, 2009: 2.014, 2008: 1.978, 2007: 1.925, 2006: 1.959, 2005: 1.947, 2004: 1.967, 2003: 2.016, 2002: 2.026, 2001: 2.062, 2000: 2.045, 1999: 2.047, 1998: 1.972, 1997: 1.963, 1996: 1.965}}
SER = [("KOR", "Korea", SKY), ("JPN", "Japan", NAVY), ("USA", "United States", GOLD), ("CHN", "China", RED), ("WLD", "World", GREY_TXT)]

def end_label(ax, x, y, text, col):
    ax.text(x + 0.8, y, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    last = {}
    for iso, name, col in SER:
        x = sorted(RD[iso]); y = [RD[iso][k] for k in x]
        if iso == "WLD":
            ax.plot(x, y, color=col, lw=3.5, ls=(0, (2, 1.5)), zorder=2)
        else:
            ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=4 if iso == "CHN" else 3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=5)
        last[iso] = (x[-1], y[-1], name, col)
    pos = {"KOR": 0, "JPN": 0.14, "USA": -0.14, "CHN": 0.13, "WLD": -0.13}
    for iso, (x, y, name, col) in last.items():
        end_label(ax, x, y + pos[iso], f"{name} {y:.1f}", col)
    ax.set_xlim(1995, 2031); ax.set_ylim(0, 5.5)
    ax.set_xticks(range(2000, 2021, 5)); ax.set_yticks(range(0, 6, 1))

compose(plot, "R&D spending more than quadrupled",
        "Research and development expenditure, percent of GDP",
        "Source: World Bank, World Development Indicators (UNESCO Institute for Statistics).\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = []
for iso, name, _ in SER:
    rows += [[y, name, RD[iso][y]] for y in sorted(RD[iso])]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "R&D expenditure (% of GDP)"], rows)
