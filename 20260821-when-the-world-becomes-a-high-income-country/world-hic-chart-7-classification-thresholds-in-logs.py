# ---------------------------------------------------------------------------
# chart-7-classification-thresholds-in-logs.py
# Moving Frontiers / The Moving Escalator. Self-sufficient build: every value
# this script consumes is embedded below; it runs offline in an empty directory
# with Python 3.x + matplotlib, numpy, Pillow only, and writes chart-7-classification-thresholds-in-logs.png.
#
# Provenance (frozen vintage; do NOT replace the embedded data with live API
# calls, downloads or file reads):
#   - Band thresholds: World Bank income classification thresholds for the
#     2025 data year (FY27), published July 2026, from OGHIST
#     (OGHIST_2026_07_01.xlsx): L up to $1,175; LM $1,176-$4,635;
#     UM $4,636-$14,375; H above $14,375.
#   - Member GNI per capita: World Bank WDI, GNI per capita, Atlas method,
#     13 July 2026 download. Data year 2025 for all members except Bermuda
#     (2024, latest reported).
#   - DERIVED, not raw: the selection of members (lowest, highest and most
#     populous classified economy per band) comes from the upstream
#     OGHIST/WDI/WPP pipeline and cannot be recomputed from this table alone.
#     Classifications follow OGHIST, never GNI-vs-threshold comparison, which
#     is also why no assert checks member values against band bounds.
#   - Values were carried over from the published c8d/c8e chart pack of the
#     same vintage.
# Duplication note: the embedded tables below also appear, deliberately, in
# the companion script chart-6-classification-thresholds-in-dollars.py, so each file stays single-file
# self-sufficient.
# ---------------------------------------------------------------------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import findfont, FontProperties
from PIL import Image, ImageDraw, ImageFont
import numpy as np

plt.rcParams["font.family"] = "DejaVu Sans"
DPI = 200; W_IN, H_IN = 8, 8
COL = {"L": "#C62828", "LM": "#F9A825", "UM": "#00897B", "H": "#283593"}
LMTXT = "#5A3D00"
TH = {"L": (0, 1175), "LM": (1176, 4635), "UM": (4636, 14375), "H": (14375, None)}
MEMBERS = {
    "H": [("Argentina", 14650, 2025), ("USA", 88810, 2025), ("Bermuda", 139370, 2024)],
    "UM": [("Iran", 4650, 2025), ("China", 14230, 2025)],
    "LM": [("Zambia", 1200, 2025), ("India", 2760, 2025), ("Bolivia", 4420, 2025)],
    "L": [("Burundi", 240, 2025), ("Ethiopia", 1110, 2025), ("Rwanda", 1150, 2025)],
}
NAME = {"L": "Low income", "LM": "Lower-middle income", "UM": "Upper-middle income", "H": "High income"}
CAP_FS = 8.5; WM_FS = CAP_FS * 1.2; WM_TXT = "movingfrontiers.substack.com"
RIGHT_PX = 70; LEFT_FIG = 0.012; XMAX_LIN = 162000

SOURCE = ("Source: World Bank WDI (13 July 2026), GNI per capita, Atlas method; OGHIST thresholds (FY27); "
          "Schellekens 2026.")
NOTE_COMMON = ("Note: Thresholds used for the 2025 classification (low income up to \\$1,175; lower-middle \\$1,176 "
               "to \\$4,635; upper-middle \\$4,636 to \\$14,375; high income above \\$14,375), ")
NOTE = {
  "linear": NOTE_COMMON + ("drawn on a linear dollar scale, on which the three lower bands together cover less than a "
            "tenth of the axis. The high-income band has no upper bound; the fading segments at its right end mark its "
            "open end. For each band the lowest and highest classified members and the most populous member are shown, "
            "listed from lowest to highest beside the three lower bands, with GNI per capita for 2025 (2024 for Bermuda), "
            "among economies with reported data; in the upper-middle band the most populous member (China) is also the highest."),
  "log": NOTE_COMMON + ("drawn on a log scale. The low-income band extends down to zero and the high-income band has no "
            "upper bound; the fading segments at their outer ends mark the open ends. For each band the lowest and highest "
            "classified members and the most populous member are shown, with GNI per capita for 2025 (2024 for Bermuda), "
            "among economies with reported data; in the upper-middle band the most populous member (China) is also the highest."),
}
CLOSERS = ["", "Thresholds were published in July 2026.",
           "The thresholds shown were published by the World Bank in July 2026.",
           "The thresholds shown are those published by the World Bank in July 2026 for the 2025 data year."]

def money(v): return "\\$" + f"{v:,}"


CLASS_YEAR = 2025          # data year of the classification shown
PUBLISHED = "July 2026"    # when the World Bank published these thresholds

def verify_prose(scale, title):
    """Every number or claim stated in prose must match the embedded data."""
    n = NOTE[scale]; checks = 0
    def ok(cond, msg):
        nonlocal checks; assert cond, "PROSE-CONSISTENCY: " + msg; checks += 1
    ok("low income up to " + money(TH["L"][1]) in n,
       "note phrase 'low income up to ...' no longer matches TH['L'] upper bound %r" % (TH["L"][1],))
    ok("lower-middle " + money(TH["LM"][0]) + " to " + money(TH["LM"][1]) in n,
       "note phrase 'lower-middle ... to ...' no longer matches TH['LM'] = %r" % (TH["LM"],))
    ok("upper-middle " + money(TH["UM"][0]) + " to " + money(TH["UM"][1]) in n,
       "note phrase 'upper-middle ... to ...' no longer matches TH['UM'] = %r" % (TH["UM"],))
    ok("high income above " + money(TH["H"][0]) in n,
       "note phrase 'high income above ...' no longer matches TH['H'] lower bound %r" % (TH["H"][0],))
    ok(TH["LM"][0] == TH["L"][1] + 1 and TH["UM"][0] == TH["LM"][1] + 1 and TH["H"][0] == TH["UM"][1],
       "embedded band bounds are no longer contiguous, contradicting the note's ranges")
    ok(f"{CLASS_YEAR} classification" in n and str(CLASS_YEAR) in title,
       "note/title no longer name classification year %d" % CLASS_YEAR)
    for g, ms in MEMBERS.items():
        vals = [v for _, v, _ in ms]
        ok(vals == sorted(vals), "MEMBERS[%r] is not ordered lowest to highest, contradicting the note" % g)
    um = MEMBERS["UM"]
    ok("(China) is also the highest" in n and um[-1][0] == "China" and um[-1][1] == max(v for _, v, _ in um),
       "note claims China is both most populous and highest in UM, contradicted by MEMBERS['UM']")
    odd_years = sorted((nm, yr) for ms in MEMBERS.values() for nm, _, yr in ms if yr != CLASS_YEAR)
    ok("(2024 for Bermuda)" in n and odd_years == [("Bermuda", 2024)],
       "note claims 2024 applies to Bermuda only, but off-year members are %r" % odd_years)
    ok(all(PUBLISHED in c for c in CLOSERS if c),
       "closing sentences claim publication in %r, contradicted by CLOSERS" % PUBLISHED)
    if scale == "linear":
        ok(TH["UM"][1] / XMAX_LIN < 0.1,
           "note claims the three lower bands cover less than a tenth of the linear axis; %r / %r does not" % (TH["UM"][1], XMAX_LIN))
    return checks

def draw_stripes(ax, x0, direction, n, scale, color, y, h):
    # fading open-end stripes; x0 = bar end; direction +1 rightwards, -1 leftwards
    x = x0
    for i in range(n):
        if scale == "log":
            gap = 10 ** (np.log10(x) + direction * 0.012 * (i + 1)) - x
            w = (10 ** (np.log10(x + gap) + direction * 0.02 * (n - i) / n) - (x + gap))
        else:
            gap = 1200 * (i + 1) * direction
            w = 2200 * (n - i) / n * direction
        x1 = x + gap
        ax.add_patch(Rectangle((min(x1, x1 + w), y - h/2), abs(w), h, color=color, lw=0))
        x = x1 + w


def place_members(fig, ax, members, ytop):
    """Spread member labels along log x so they never overlap; leaders connect value to label."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    texts = []
    for nm, v, _yr in members:
        t = ax.text(v, ytop + 0.5, nm, ha="center", va="baseline", fontsize=10.5, fontweight="bold", color="#444444")
        t2 = ax.text(v, ytop + 0.32, money(v), ha="center", va="baseline", fontsize=9.5, color="#777777")
        texts.append((v, t, t2))
    widths = [max(t.get_window_extent(r).width, t2.get_window_extent(r).width) + 8 for _, t, t2 in texts]
    px = [ax.transData.transform((v, 0))[0] for v, _, _ in texts]
    new = px[:]
    for _ in range(50):
        for i in range(len(new) - 1):
            need = (widths[i] + widths[i + 1]) / 2
            if new[i + 1] - new[i] < need:
                d = (need - (new[i + 1] - new[i])) / 2; new[i] -= d; new[i + 1] += d
    for (v, t, t2), xp in zip(texts, new):
        xd = ax.transData.inverted().transform((xp, 0))[0]
        t.set_x(xd); t2.set_x(xd)
        ax.plot([v, v, xd], [ytop, ytop + 0.1, ytop + 0.22], color="#666666", lw=1.0, solid_capstyle="round")
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    bbs = [t.get_window_extent(r) for _, t, _ in texts]
    for a, b in zip(bbs, bbs[1:]): assert a.x1 < b.x0, ("label overlap", a, b)

def chart(scale):
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI)
    ax = fig.add_axes([0.04, 0.30, 0.93, 0.64])
    for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
    ax.set_yticks([]); ax.set_ylim(-0.7, 4.1 if scale == "linear" else 4.5)
    H_BAR = 0.5
    rows = {"H": 3.2, "UM": 2.15, "LM": 1.1, "L": 0.05} if scale == "linear" else {"H": 3.55, "UM": 2.4, "LM": 1.25, "L": 0.1}
    if scale == "log":
        ax.set_xscale("log"); ax.set_xlim(100, 220000)
        ax.set_xticks([100, 1000, 10000, 100000]); ax.set_xticklabels(["\\$100", "\\$1,000", "\\$10,000", "\\$100,000"], fontsize=12)
        ax.set_xlabel("GNI per capita, Atlas US\\$ (log scale), 2025 thresholds", fontsize=13)
        ends = {"L": (190, 1175), "LM": (1176, 4635), "UM": (4636, 14375), "H": (14375, 143000)}
    else:
        ax.set_xlim(0, XMAX_LIN)
        ax.set_xticks(range(0, 150001, 25000)); ax.set_xticklabels([money(v) for v in range(0, 150001, 25000)], fontsize=12)
        ax.set_xlabel("GNI per capita, Atlas US\\$ (linear scale), 2025 thresholds", fontsize=13)
        ends = {"L": (0, 1175), "LM": (1176, 4635), "UM": (4636, 14375), "H": (14375, 143000)}
    ax.tick_params(axis="x", length=5, width=1, color="#666666")
    ax.spines["bottom"].set_color("#666666")
    for g in ["H", "UM", "LM", "L"]:
        y = rows[g]; a, b = ends[g]
        ax.add_patch(Rectangle((a, y - H_BAR/2), b - a, H_BAR, color=COL[g], lw=0))
        if g == "H": draw_stripes(ax, b, +1, 5, scale, COL[g], y, H_BAR)
        if g == "L" and scale == "log": draw_stripes(ax, a, -1, 5, scale, COL[g], y, H_BAR)
        labcol = LMTXT if g == "LM" else COL[g]
        if scale == "log":
            # member ticks and labels above bar
            place_members(fig, ax, MEMBERS[g], y + H_BAR/2)
            side = "left" if g in ("H", "UM") else "right"
            if side == "left":
                ax.text(a / 1.08, y, NAME[g], ha="right", va="center", fontsize=16, fontweight="bold", color=labcol)
            else:
                ax.text(b * 1.08, y, NAME[g], ha="left", va="center", fontsize=16, fontweight="bold", color=labcol)
        else:
            if g == "H":
                for nm, v, _yr in MEMBERS[g]:
                    ax.plot([v, v], [y + H_BAR/2, y + H_BAR/2 + 0.12], color="#666666", lw=1.2)
                    ax.text(v, y + H_BAR/2 + 0.3, money(v), ha="center", va="baseline", fontsize=9.5, color="#777777")
                    ax.text(v, y + H_BAR/2 + 0.47, nm, ha="center", va="baseline", fontsize=10.5, fontweight="bold", color="#444444")
                ax.text((a + b)/2, y, NAME[g], ha="center", va="center", fontsize=16, fontweight="bold", color="white")
            else:
                ax.text(b + 1500, y + 0.07, NAME[g], ha="left", va="baseline", fontsize=16, fontweight="bold", color=labcol)
                ax.text(b + 1500, y - 0.2, " \u00b7 ".join(f"{nm} {money(v)}" for nm, v, _yr in MEMBERS[g]),
                        ha="left", va="baseline", fontsize=10, color="#777777")
    return fig, ax

# ---------------- caption + watermark ----------------
def probe_w(fig, r, s, fs):
    t = fig.text(0, 0, s, fontsize=fs); w = t.get_window_extent(r).width; t.remove(); return w

def layout_caption(fig, ax, source, note):
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    Wpx, Hpx = fig.get_size_inches() * fig.dpi
    # metrics
    w0 = probe_w(fig, r, "0", CAP_FS); space = probe_w(fig, r, "0 0", CAP_FS) - 2 * w0
    p = fig.text(0.5, 0.5, "0 0", fontsize=CAP_FS, va="baseline"); bb = p.get_window_extent(r)
    descent = 0.5 * Hpx - bb.y0; ascent = bb.height - descent; LH = bb.height * 1.28; p.remove()
    wm_w = probe_w(fig, r, WM_TXT, WM_FS); movi_w = probe_w(fig, r, "movi", WM_FS)
    x_left = LEFT_FIG * Wpx; x_right = Wpx - RIGHT_PX
    full = x_right - x_left; short = full - wm_w - movi_w
    def wrap(words, limit):
        ww = [probe_w(fig, r, w, CAP_FS) for w in words]
        lines, cur, curw = [], [], 0
        for w, wid in zip(words, ww):
            add = wid if not cur else curw + space + wid
            if cur and add > limit: lines.append(" ".join(cur)); cur, curw = [w], wid
            else: cur.append(w); curw = add
        if cur: lines.append(" ".join(cur))
        return lines
    for closer in CLOSERS:
        text = source + " " + note + (" " + closer if closer else "")
        g = wrap(text.split(), full)
        tail = wrap(g[-1].split(), short)
        if len(tail) == 2:
            lines = g[:-1] + tail; break
    else:
        raise RuntimeError("no closer gives a 2-line tail")
    # anchor: lowest axis element
    ylow = min([ax.xaxis.label.get_window_extent(r).y0] + [t.get_window_extent(r).y0 for t in ax.get_xticklabels()])
    top = ylow - 2.0 * LH
    base0 = top - ascent
    arts = []
    for i, ln in enumerate(lines):
        y = (base0 - i * LH) / Hpx
        arts.append(fig.text(LEFT_FIG, y, ln, fontsize=CAP_FS, color="#555555", ha="left", va="baseline"))
    wm = fig.text((Wpx - RIGHT_PX) / Wpx, (base0 - (len(lines) - 1) * LH) / Hpx, WM_TXT,
                  fontsize=WM_FS, color="#999999", ha="right", va="baseline")
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    # ---- assertions ----
    bbs = [a.get_window_extent(r) for a in arts]; wbb = wm.get_window_extent(r)
    for bb in bbs[-2:]:
        assert wbb.x0 - bb.x1 >= movi_w - 0.5, ("gap", wbb.x0 - bb.x1, movi_w)
    for bb in bbs[:-2]:
        assert bb.x1 <= x_right + 0.5, ("overflow", bb.x1, x_right)
    last_base = base0 - (len(lines) - 1) * LH
    assert abs((wbb.y0 + descent * WM_FS / CAP_FS) - last_base) / Hpx < 0.0015, "wm baseline"
    assert min(b.y0 for b in bbs) / Hpx > 0.004, ("bottom", min(b.y0 for b in bbs) / Hpx)
    assert abs((bbs[0].y1 - ylow) / LH + 2.0) < 0.03, ("top gap", (ylow - bbs[0].y1) / LH)
    test = lines[-3] + " " + lines[-2].split()[0]
    assert probe_w(fig, r, test, CAP_FS) > full, "third-to-last not maximal"
    # collision check: caption vs axis
    assert bbs[0].y1 < ylow
    return lines

def composite_title(png, title, out):
    im = Image.open(png).convert("RGB"); arr = np.asarray(im)
    rows = np.where((arr < 250).any(axis=(1, 2)))[0]
    m = 14; im = im.crop((0, max(0, rows[0] - m), im.width, min(im.height, rows[-1] + m + 1)))
    fpath = findfont(FontProperties(family="DejaVu Sans", weight="bold"))
    fs = int(round(19 * DPI / 72)); font = ImageFont.truetype(fpath, fs)
    # wrap title to width
    maxw = im.width - int(0.03 * im.width) - RIGHT_PX; words = title.split(); lines, cur = [], []
    d = ImageDraw.Draw(im)
    for w in words:
        t = " ".join(cur + [w])
        if cur and d.textlength(t, font=font) > maxw: lines.append(" ".join(cur)); cur = [w]
        else: cur.append(w)
    lines.append(" ".join(cur))
    lh = int(fs * 1.25); band_h = int(0.04 * im.width) + lh * len(lines) + int(fs * 0.6)
    canvas = Image.new("RGB", (im.width, band_h + im.height), "white"); canvas.paste(im, (0, band_h))
    d = ImageDraw.Draw(canvas); y = int(0.03 * im.width)
    for ln in lines: d.text((int(0.03 * im.width), y), ln, font=font, fill="#2d2d2d"); y += lh
    canvas.save(out, dpi=(DPI, DPI))

if __name__ == "__main__":
    scale, name, title = 'log', 'chart-7-classification-thresholds-in-logs', 'The 2025 classification thresholds in logs'
    n_checks = verify_prose(scale, title)
    fig, ax = chart(scale)
    lines = layout_caption(fig, ax, SOURCE, NOTE[scale])
    tmp = f"{name}-raw.png"; fig.savefig(tmp, dpi=DPI, facecolor="white"); plt.close(fig)
    composite_title(tmp, title, f"{name}.png")
    print(name, "OK,", len(lines), "caption lines;", n_checks, "prose-consistency asserts passed")
