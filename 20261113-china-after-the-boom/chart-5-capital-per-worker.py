# Chart 5: capital stock per worker, China and the United States
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
NAME = "chart-5-capital-per-worker"
# Penn World Table 11.0 (Feenstra, Inklaar and Timmer), via FRED: capital stock at constant national prices,
# millions of 2021 US dollars (rkna) and persons engaged, millions (emp), China and United States, 1980-2023.
KRAW = """\
year,china_capital_musd,us_capital_musd,china_workers_m,us_workers_m
1980,2626428.750,29506590,476.466,103.470
1981,2820224.500,30360724,496.539,104.698
1982,3040363.750,31041684,522.161,103.980
1983,3285501.750,31824032,536.208,105.435
1984,3572324.500,32878966,550.420,109.862
1985,3923363.750,34021900,564.916,112.191
1986,4299320.000,35158052,577.688,114.730
1987,4697350.500,36259956,588.970,117.664
1988,5153502.000,37347072,605.541,120.204
1989,5487767.000,38436032,627.566,122.550
1990,5772352.500,39439352,647.400,123.910
1991,6129512.000,40251216,662.984,122.740
1992,6667980.000,41116496,670.216,123.288
1993,7461987.500,42057968,676.428,124.846
1994,8335410.000,43102436,682.057,127.499
1995,9279385.000,44213800,687.490,129.188
1996,10315911.000,45461520,693.968,130.842
1997,11413979.000,46823444,701.587,133.489
1998,12711590.000,48363724,709.159,135.238
1999,14058341.000,50045728,716.568,137.152
2000,15487957.000,51804608,723.769,138.807
2001,17124416.000,53377052,731.011,138.769
2002,19022494.000,54757692,736.964,138.340
2003,21374392.000,56217084,741.642,139.018
2004,24049898.000,57823104,746.583,140.764
2005,27050484.000,59564856,751.312,143.134
2006,30437274.000,61276848,755.542,145.864
2007,34227428.000,62818256,759.478,147.298
2008,38462012.000,64052376,763.157,147.243
2009,43962712.000,64686820,766.975,142.301
2010,50110612.000,65349080,771.193,141.964
2011,56670656.000,66106652,772.328,143.618
2012,63722176.000,67036032,772.423,146.332
2013,71349296.000,68023432,773.677,148.028
2014,79360160.000,69139896,773.977,150.637
2015,87775192.000,70325160,774.418,153.072
2016,96755824.000,71524240,772.982,155.681
2017,106217664.000,72799488,771.330,158.468
2018,116379784.000,74181696,769.240,161.066
2019,126968344.000,75565584,765.730,163.924
2020,137695824.000,76785096,762.124,154.940
2021,148589856.000,78158760,757.860,160.861
2022,159623808.000,79490152,744.443,165.578
2023,171095104.000,80822920,751.185,167.540
"""

ROWS = [l.split(",") for l in KRAW.strip().splitlines()[1:]]
YR = [int(r[0]) for r in ROWS]
CN = [float(r[1]) / float(r[3]) / 1000 for r in ROWS]
US = [float(r[2]) / float(r[4]) / 1000 for r in ROWS]
PCT = [100 * c / u for c, u in zip(CN, US)]

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    ax.fill_between(YR, CN, US, color=BAND, lw=0, zorder=1)
    ax.plot(YR, US, color=NAVY, lw=5.5, solid_capstyle="round", zorder=3)
    ax.plot(YR, CN, color=RED, lw=5.5, solid_capstyle="round", zorder=3)
    for yr, dx, ha in [(2000, 0, "center"), (2010, -1.0, "right"), (2023, -1.2, "right")]:
        i = YR.index(yr)
        ax.plot(yr, CN[i], "o", color=RED, ms=14, mec="white", mew=3, zorder=5)
        ax.text(yr + dx, CN[i] + 22, f"{PCT[i]:.0f}% of US\nin {yr}", color=RED, fontfamily=CALIBRI,
                fontweight="bold", fontsize=S_VALUE, ha=ha, va="bottom", linespacing=1.05)
    ax.plot(YR[-1], US[-1], "o", color=NAVY, ms=14, zorder=5)
    ax.text(YR[-1] + 1.0, US[-1], f"United\nStates\n{US[-1]:.0f}", color=NAVY, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="left", va="center", linespacing=1.05)
    ax.text(YR[-1] + 1.0, CN[-1], f"China\n{CN[-1]:.0f}", color=RED, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="left", va="center", linespacing=1.05)
    ax.set_xlim(1979, 2031); ax.set_ylim(0, 520)
    ax.set_xticks(range(1980, 2021, 10)); ax.set_yticks(range(0, 501, 100))

compose(plot, "Capital per worker nears half the US",
        "Capital stock per worker, thousands of 2021 US dollars, PPP",
        "Source: Penn World Table 11.0, via FRED.\nNote: At market exchange rates China's capital per worker relative to the United States would be lower.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
write_csv(os.path.join(HERE, NAME + ".csv"),
          ["year", "China (thousand 2021 US$ per worker)", "United States (thousand 2021 US$ per worker)", "China relative to US (%)"],
          [[y, round(c, 2), round(u, 2), round(p, 2)] for y, c, u, p in zip(YR, CN, US, PCT)])
