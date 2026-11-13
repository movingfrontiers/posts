# Chart 16: future-ready governance framework
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
NAME = "chart-16-future-ready-governance"
COLS = [("Anticipate", NAVY, ["Foresight and long-term planning", "Scenario and contingency planning", "Risk sensing"]),
        ("Adapt", SKY, ["Learning and unlearning", "Experimentation and iterative policy", "Feedback loops and shared data"]),
        ("Act with agility", GOLD, ["Flexible budgets", "Coordination across\ngovernment", "Disciplined, digital\ndelivery"])]
ENABLERS = ["Political will", "Collaborative leadership", "Civic engagement"]
LEVELS = ["Formal authorisation", "Implementation", "Outcomes"]
from matplotlib.patches import FancyBboxPatch

def box(ax, x, y, w, h, fc, ec=None, lw=0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.012",
                                fc=fc, ec=ec or fc, lw=lw, zorder=2))

def txt(ax, x, y, s, col=INK, size=S_VALUE, bold=False, ha="center"):
    ax.text(x, y, s, color=col, fontfamily=CALIBRI, fontweight="bold" if bold else "normal",
            fontsize=size, ha=ha, va="center", zorder=3, linespacing=1.1)

def plot(fig):
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    gap = 0.025; w = (1 - 2 * gap) / 3
    for i, (name, col, items) in enumerate(COLS):
        x = i * (w + gap)
        box(ax, x, 0.86, w, 0.14, col); txt(ax, x + w / 2, 0.93, name, "white", S_HEAD, True)
        for j, it in enumerate(items):
            y = 0.70 - j * 0.15
            box(ax, x, y, w, 0.13, BAND)
            txt(ax, x + w / 2, y + 0.065, it.replace(" and ", " and\n", 1) if len(it) > 24 else it)
    box(ax, 0, 0.20, 1, 0.17, "white", NAVY, 3)
    txt(ax, 0.5, 0.325, "Enabling conditions", NAVY, S_VALUE, True)
    for k, e in enumerate(ENABLERS):
        txt(ax, (k + 0.5) / 3, 0.25, e, INK)
    lw3 = (1 - 2 * 0.06) / 3
    for k, l in enumerate(LEVELS):
        x = k * (lw3 + 0.06)
        box(ax, x, 0.0, lw3, 0.11, "#F2F2F2"); txt(ax, x + lw3 / 2, 0.055, l, GREY_TXT)
        if k < 2:
            ax.annotate("", xy=(x + lw3 + 0.052, 0.055), xytext=(x + lw3 + 0.008, 0.055),
                        arrowprops=dict(arrowstyle="-|>", color=GREY_TXT, lw=3, mutation_scale=30), zorder=3)

compose(plot, "Anticipate, adapt and act",
        "Governance capabilities, enablers and levels of assessment",
        "Source: UNDP and Chandler Governance Group, Future-Ready Governance: Anticipate, Adapt and Act (forthcoming); Neo and Chen (2007).\nRead more: movingfrontiers.substack.com/china-after-the-boom",
        os.path.join(HERE, NAME + ".png"))
rows = [[c[0], it] for c in COLS for it in c[2]] + [["Enabling conditions", e] for e in ENABLERS] + [["Assessment level", l] for l in LEVELS]
write_csv(os.path.join(HERE, NAME + ".csv"), ["layer", "element"], rows)
