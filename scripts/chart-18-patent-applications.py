# Chart 18: resident patent applications
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
NAME = "chart-18-patent-applications"
# World Bank, World Development Indicators: patent applications, residents (IP.PAT.RESD), from WIPO
PT = {'CHN': {2024: 1672001.0, 2023: 1522292.0, 2022: 1464605.0, 2021: 1427845.0, 2020: 1344817.0, 2019: 1243568.0, 2018: 1393815.0, 2017: 1245709.0, 2016: 1204981.0, 2015: 968252.0, 2014: 801135.0, 2013: 704936.0, 2012: 535313.0, 2011: 415829.0, 2010: 293066.0, 2009: 229096.0, 2008: 194579.0, 2007: 153060.0, 2006: 122318.0, 2005: 93485.0, 2004: 65786.0, 2003: 56769.0, 2002: 39806.0, 2001: 30038.0, 2000: 25346.0, 1999: 15626.0, 1998: 13751.0, 1997: 12672.0, 1996: 11628.0, 1995: 10011.0, 1994: 11191.0, 1993: 12084.0, 1992: 10022.0, 1991: 7372.0, 1990: 5832.0, 1989: 4749.0, 1988: 4780.0, 1987: 3975.0, 1986: 3494.0, 1985: 4065.0}, 'JPN': {2024: 237169.0, 2023: 228936.0, 2022: 218813.0, 2021: 222452.0, 2020: 227348.0, 2019: 245372.0, 2018: 253630.0, 2017: 260292.0, 2016: 260244.0, 2015: 258839.0, 2014: 265959.0, 2013: 271731.0, 2012: 287013.0, 2011: 287580.0, 2010: 290081.0, 2009: 295315.0, 2008: 330110.0, 2007: 333498.0, 2006: 347060.0, 2005: 367960.0, 2004: 368416.0, 2003: 358184.0, 2002: 369458.0, 2001: 386767.0, 2000: 387364.0, 1999: 360180.0, 1998: 359381.0, 1997: 350807.0, 1996: 340101.0, 1995: 334612.0, 1994: 319938.0, 1993: 332345.0, 1992: 338019.0, 1991: 335933.0, 1990: 333230.0, 1989: 317566.0, 1988: 308908.0, 1987: 311006.0, 1986: 290202.0, 1985: 274373.0, 1984: 256205.0, 1983: 227708.0, 1980: 165730.0}, 'USA': {2024: 270295.0, 2023: 278446.0, 2022: 273691.0, 2021: 282476.0, 2020: 287979.0, 2019: 302986.0, 2018: 294738.0, 2017: 302741.0, 2016: 302991.0, 2015: 295151.0, 2014: 291275.0, 2013: 292276.0, 2012: 272797.0, 2011: 254170.0, 2010: 247844.0, 2009: 229005.0, 2008: 225998.0, 2007: 232669.0, 2006: 214672.0, 2005: 202722.0, 2004: 188191.0, 2003: 182024.0, 2002: 173208.0, 2001: 163469.0, 2000: 151764.0, 1999: 149251.0, 1998: 134733.0, 1997: 119214.0, 1996: 106892.0, 1995: 123962.0, 1994: 107233.0, 1993: 99955.0, 1992: 92425.0, 1991: 87955.0, 1990: 90643.0, 1989: 82370.0, 1988: 75192.0, 1987: 68315.0, 1986: 65195.0, 1985: 63673.0, 1984: 61841.0, 1983: 59391.0, 1982: 63316.0, 1981: 62404.0, 1980: 62098.0}, 'KOR': {2024: 195786.0, 2023: 191142.0, 2022: 183748.0, 2021: 186245.0, 2020: 180477.0, 2019: 171603.0, 2018: 162561.0, 2017: 159084.0, 2016: 163424.0, 2015: 167275.0, 2014: 164073.0, 2013: 159978.0, 2012: 148136.0, 2011: 138034.0, 2010: 131805.0, 2009: 127316.0, 2008: 127114.0, 2007: 128701.0, 2006: 125476.0, 2005: 122188.0, 2004: 105250.0, 2003: 90313.0, 2002: 76570.0, 2001: 73714.0, 2000: 72831.0, 1999: 55970.0, 1998: 50596.0, 1997: 67359.0, 1996: 68405.0, 1995: 59228.0, 1994: 28554.0, 1993: 21449.0, 1992: 15951.0, 1991: 13253.0, 1990: 9082.0, 1989: 7020.0, 1988: 5696.0, 1987: 4871.0, 1986: 3640.0, 1985: 2702.0, 1984: 1997.0, 1983: 1599.0, 1982: 1556.0, 1981: 1319.0, 1980: 1241.0}, 'WLD': {2024: 2702600.0, 2023: 2530000.0, 2022: 2429900.0, 2021: 2402800.0, 2020: 2330000.0, 2019: 2256900.0, 2018: 2396000.0, 2017: 2259900.0, 2016: 2223300.0, 2015: 1980400.0, 2014: 1805400.0, 2013: 1713100.0, 2012: 1523300.0, 2011: 1371300.0, 2010: 1242600.0, 2009: 1149900.0, 2008: 1155900.0, 2007: 1115700.0, 2006: 1067500.0, 2005: 1033100.0, 2004: 964900.0, 2003: 917500.0, 2002: 881600.0, 2001: 885600.0, 2000: 864300.0, 1999: 793300.0, 1998: 757500.0, 1997: 738300.0, 1996: 708400.0, 1995: 703600.0, 1994: 637000.0, 1993: 649200.0, 1992: 635700.0, 1991: 601000.0, 1990: 687700.0, 1989: 705400.0, 1988: 714900.0, 1987: 712400.0, 1986: 675000.0, 1985: 651100.0}}
SER = [("JPN", "Japan", NAVY), ("USA", "United States", GOLD), ("KOR", "Korea", SKY), ("CHN", "China", RED)]

def end_label(ax, x, y, text, col):
    ax.text(x + 0.8, y, text, color=col, fontfamily=CALIBRI, fontweight="bold",
            fontsize=S_VALUE, va="center", ha="left", linespacing=1.05)

def plot(fig):
    ax = fig.add_subplot(111); style_axes(ax, yticks=True)
    last = {}
    for iso, name, col in SER:
        x = [k for k in sorted(PT[iso]) if k >= 1985]; y = [PT[iso][k] / 1000 for k in x]
        ax.plot(x, y, color=col, lw=5.5, solid_capstyle="round", zorder=4 if iso == "CHN" else 3)
        ax.plot(x[-1], y[-1], "o", color=col, ms=13, zorder=5)
        last[iso] = (x[-1], y[-1], name, col)
    pos = {"CHN": 0, "USA": 75, "JPN": 0, "KOR": -75}
    for iso, (x, y, name, col) in last.items():
        end_label(ax, x, y + pos[iso], f"{name} {y:,.0f}", col)
    share = 100 * PT["CHN"][2024] / PT["WLD"][2024]
    ax.text(2013.5, 1300, f"China: {share:.0f} percent of\nworld filings in 2024", color=RED, fontfamily=CALIBRI,
            fontweight="bold", fontsize=S_VALUE, ha="right", va="center", linespacing=1.05)
    ax.set_xlim(1984, 2035); ax.set_ylim(0, 1800)
    ax.set_xticks(range(1990, 2021, 10)); ax.set_yticks(range(0, 1801, 300))

compose(plot, "China files six in ten patents",
        "Patent applications by residents, thousands",
        "Source: World Bank, World Development Indicators (World Intellectual Property Organization).\nNote: Counts measure the number of filings, not their quality or value.\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = []
for iso, name, _ in SER + [("WLD", "World", None)]:
    rows += [[y, name, PT[iso][y]] for y in sorted(PT[iso]) if y >= 1985]
write_csv(os.path.join(HERE, NAME + ".csv"), ["year", "economy", "resident patent applications"], rows)
