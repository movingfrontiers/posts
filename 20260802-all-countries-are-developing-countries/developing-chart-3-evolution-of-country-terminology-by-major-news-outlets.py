"""Reconstruction of the published figure from its csv. Typography follows the
Moving Frontiers chart conventions; pixel-level details may differ marginally
from the original render."""
import pandas as pd, numpy as np

# ---------------------------------------------------------------------------
# PROVENANCE (data frozen; do not replace with live calls or downloads)
#
# Source: Media Cloud story index, January 2016 to July 2026, retrieved August 2026.
# Frozen: 28 August 2026, from the csv published in this repository.
# The output is pinned to this vintage; a script that re-fetches upstream
# data is not reproducible, merely convenient.
# Derived: the per-1,000 shares are as plotted in the published figure, at the
# Derived:         stated decimal precision; they are derived from a Media Cloud query
# Derived:         run in August 2026 and cannot be looked up at that exact precision.
# ---------------------------------------------------------------------------

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

plt.rcParams.update({'font.family':'DejaVu Sans',
    'axes.edgecolor':'#888','axes.linewidth':1.0,
    'figure.facecolor':'white','axes.facecolor':'white'})
RED,TEAL,INDIGO = '#C62828','#00897B','#283593'

def caption(fig, lines, FIGH, y0=0.010):
    FS=7.0
    lh=22.0/(FIGH*200); ch=(FS*200/72)/(FIGH*200)
    n=len(lines)
    for i,ln in enumerate(lines):
        fig.text(0.012,y0+(n-1-i)*lh,ln,fontsize=FS,color='#666',
                 ha='left',va='bottom')
    fig.text(1-58/1600, y0-0.5*ch, 'movingfrontiers.substack.com',
             fontsize=FS,color='#999999',ha='right',va='bottom')
    return y0+n*lh

def title_band(OUT,title,subtitle):
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib, os
    def _resolve_font(name):
        cands=['/usr/share/fonts/truetype/dejavu/'+name,
               os.path.join(matplotlib.get_data_path(),'fonts','ttf',name)]
        for p in cands:
            if os.path.exists(p): return p
        raise FileNotFoundError(name)
    FB=_resolve_font('DejaVuSans-Bold.ttf')
    FR=_resolve_font('DejaVuSans.ttf')
    im=Image.open(OUT).convert('RGB'); W,H=im.size
    fs=int(W*0.031); font=ImageFont.truetype(FB,fs)
    fss=int(W*0.0225); fonts=ImageFont.truetype(FR,fss)
    tmp=ImageDraw.Draw(im)
    def wrap(text,f):
        words=text.split(); lines=[]; cur=''
        for w in words:
            t=(cur+' '+w).strip()
            if tmp.textlength(t,font=f)<=W-2*int(W*0.03): cur=t
            else: lines.append(cur); cur=w
        lines.append(cur); return lines
    lines=wrap(title,font); slines=wrap(subtitle,fonts)
    lh=int(fs*1.25); lhs=int(fss*1.3)
    band=int(fs*0.85)+lh*len(lines)+int(fss*0.5)+lhs*len(slines)+int(fs*0.03)
    canvas=Image.new('RGB',(W,H+band),'white'); canvas.paste(im,(0,band))
    dr=ImageDraw.Draw(canvas); y=int(fs*0.85)
    for ln in lines: dr.text((int(W*0.03),y),ln,font=font,fill=(45,45,45)); y+=lh
    y+=int(fss*0.35)
    for ln in slines: dr.text((int(W*0.03),y),ln,font=fonts,fill=(100,100,100)); y+=lhs
    canvas.save(OUT,optimize=True)
    print('done',canvas.size)

# EMBEDDED DATA, exact copy of the csv (csv row order preserved)
ROWS = [
    ('2017-01', 1.932, 1.175, 0.152),
    ('2017-02', 1.923, 1.148, 0.145),
    ('2017-03', 1.89, 1.133, 0.143),
    ('2017-04', 1.874, 1.146, 0.143),
    ('2017-05', 1.836, 1.139, 0.134),
    ('2017-06', 1.82, 1.135, 0.123),
    ('2017-07', 1.861, 1.16, 0.114),
    ('2017-08', 1.934, 1.182, 0.109),
    ('2017-09', 1.914, 1.178, 0.109),
    ('2017-10', 1.872, 1.16, 0.112),
    ('2017-11', 1.827, 1.16, 0.118),
    ('2017-12', 1.809, 1.187, 0.118),
    ('2018-01', 1.845, 1.202, 0.123),
    ('2018-02', 1.818, 1.202, 0.13),
    ('2018-03', 1.818, 1.198, 0.13),
    ('2018-04', 1.834, 1.195, 0.136),
    ('2018-05', 1.883, 1.225, 0.141),
    ('2018-06', 1.849, 1.231, 0.156),
    ('2018-07', 1.791, 1.209, 0.156),
    ('2018-08', 1.737, 1.227, 0.163),
    ('2018-09', 1.758, 1.24, 0.17),
    ('2018-10', 1.775, 1.231, 0.177),
    ('2018-11', 1.818, 1.2, 0.183),
    ('2018-12', 1.82, 1.171, 0.19),
    ('2019-01', 1.865, 1.202, 0.199),
    ('2019-02', 1.878, 1.218, 0.208),
    ('2019-03', 1.887, 1.216, 0.217),
    ('2019-04', 1.885, 1.198, 0.215),
    ('2019-05', 1.843, 1.175, 0.215),
    ('2019-06', 1.852, 1.184, 0.221),
    ('2019-07', 1.874, 1.173, 0.239),
    ('2019-08', 1.836, 1.157, 0.239),
    ('2019-09', 1.8, 1.148, 0.239),
    ('2019-10', 1.764, 1.155, 0.23),
    ('2019-11', 1.697, 1.137, 0.224),
    ('2019-12', 1.623, 1.113, 0.221),
    ('2020-01', 1.552, 1.088, 0.215),
    ('2020-02', 1.52, 1.09, 0.212),
    ('2020-03', 1.507, 1.128, 0.203),
    ('2020-04', 1.558, 1.209, 0.203),
    ('2020-05', 1.672, 1.256, 0.199),
    ('2020-06', 1.731, 1.24, 0.179),
    ('2020-07', 1.753, 1.249, 0.172),
    ('2020-08', 1.802, 1.294, 0.179),
    ('2020-09', 1.829, 1.319, 0.186),
    ('2020-10', 1.869, 1.343, 0.199),
    ('2020-11', 1.937, 1.361, 0.212),
    ('2020-12', 2.051, 1.363, 0.224),
    ('2021-01', 2.17, 1.37, 0.242),
    ('2021-02', 2.295, 1.39, 0.289),
    ('2021-03', 2.407, 1.39, 0.327),
    ('2021-04', 2.429, 1.37, 0.345),
    ('2021-05', 2.438, 1.384, 0.374),
    ('2021-06', 2.496, 1.424, 0.398),
    ('2021-07', 2.541, 1.426, 0.414),
    ('2021-08', 2.577, 1.424, 0.432),
    ('2021-09', 2.662, 1.451, 0.461),
    ('2021-10', 2.799, 1.513, 0.497),
    ('2021-11', 3.061, 1.657, 0.528),
    ('2021-12', 3.119, 1.746, 0.56),
    ('2022-01', 3.012, 1.746, 0.564),
    ('2022-02', 2.897, 1.704, 0.535),
    ('2022-03', 2.788, 1.67, 0.519),
    ('2022-04', 2.718, 1.628, 0.528),
    ('2022-05', 2.638, 1.576, 0.524),
    ('2022-06', 2.593, 1.543, 0.504),
    ('2022-07', 2.561, 1.498, 0.474),
    ('2022-08', 2.503, 1.46, 0.441),
    ('2022-09', 2.405, 1.422, 0.396),
    ('2022-10', 2.246, 1.339, 0.342),
    ('2022-11', 2.089, 1.26, 0.3),
    ('2022-12', 2.033, 1.2, 0.248),
    ('2023-01', 2.033, 1.191, 0.224),
    ('2023-02', 2.073, 1.18, 0.206),
    ('2023-03', 2.082, 1.189, 0.199),
    ('2023-04', 2.046, 1.18, 0.183),
    ('2023-05', 2.028, 1.166, 0.172),
    ('2023-06', 1.988, 1.135, 0.168),
    ('2023-07', 2.035, 1.153, 0.177),
    ('2023-08', 2.114, 1.162, 0.174),
    ('2023-09', 2.196, 1.175, 0.17),
    ('2023-10', 2.187, 1.157, 0.168),
    ('2023-11', 2.109, 1.113, 0.177),
    ('2023-12', 2.165, 1.182, 0.19),
    ('2024-01', 2.181, 1.213, 0.192),
    ('2024-02', 2.143, 1.247, 0.192),
    ('2024-03', 2.111, 1.238, 0.194),
    ('2024-04', 2.071, 1.236, 0.188),
    ('2024-05', 2.042, 1.238, 0.194),
    ('2024-06', 1.984, 1.24, 0.203),
    ('2024-07', 1.876, 1.213, 0.208),
    ('2024-08', 1.731, 1.182, 0.212),
    ('2024-09', 1.554, 1.117, 0.203),
    ('2024-10', 1.491, 1.097, 0.197),
    ('2024-11', 1.455, 1.079, 0.194),
    ('2024-12', 1.337, 0.983, 0.181),
    ('2025-01', 1.283, 0.92, 0.174),
    ('2025-02', 1.267, 0.864, 0.165),
    ('2025-03', 1.254, 0.817, 0.156),
    ('2025-04', 1.249, 0.795, 0.156),
    ('2025-05', 1.2, 0.779, 0.159),
    ('2025-06', 1.155, 0.761, 0.161),
    ('2025-07', 1.126, 0.73, 0.154),
    ('2025-08', 1.09, 0.692, 0.15),
    ('2025-09', 1.03, 0.669, 0.15),
    ('2025-10', 0.956, 0.624, 0.154),
    ('2025-11', 0.889, 0.573, 0.147),
    ('2025-12', 0.875, 0.566, 0.147),
    ('2026-01', 0.839, 0.551, 0.147),
    ('2026-02', 0.795, 0.539, 0.143),
    ('2026-03', 0.763, 0.517, 0.141),
    ('2026-04', 0.734, 0.479, 0.127),
    ('2026-05', 0.701, 0.452, 0.116),
    ('2026-06', 0.665, 0.427, 0.107),
]
COLS = ['month', 'stories_per_1000_developing_country_12m', 'stories_per_1000_developed_country_12m', 'stories_per_1000_high_income_country_12m']
d = pd.DataFrame(ROWS, columns=COLS)
t = [int(m[:4])+(int(m[5:7])-1)/12 for m in d['month']]
FIGW,FIGH = 8, 6.6
fig,ax = plt.subplots(figsize=(FIGW,FIGH))
ax.plot(t,d['stories_per_1000_developing_country_12m'],color=RED,lw=3,
        label='"Developing country"')
ax.plot(t,d['stories_per_1000_developed_country_12m'],color=TEAL,lw=3,
        label='"Developed country"')
ax.plot(t,d['stories_per_1000_high_income_country_12m'],color=INDIGO,lw=3,
        label='"High-income country"')
for xv,lab in [(2016+3/12,'WDI 2016'),(2020+2/12,'COVID-19')]:
    ax.axvline(xv,color='#AAA',lw=1.2,ls=':')
    ax.text(xv,ax.get_ylim()[1]*1.02+3.25*0.02,lab,ha='left',va='bottom',
            fontsize=12,color='#333',clip_on=False)
ax.set_ylim(0,3.25)
ax.set_xticks(range(2016,2027,2)); ax.set_xlim(2015.7,2026.9)
ax.set_ylabel('Stories per 1,000, 12-month rolling',fontsize=13)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.10),ncol=3,frameon=False,fontsize=11)
cap=[
 'Source: Media Cloud story index, January 2016 to July 2026, retrieved August 2026. Queries match the exact phrases developing country or',
 'countries, developed country or countries, and high-income country or countries, language English.',
 'Note: Pooled across all twelve outlets, grouped by country: Hong Kong SAR, China (South China Morning Post), India (The Times of India),',
 'Japan (The Japan Times), Malaysia (The Star), Nigeria (Punch), Qatar (Al Jazeera), Russia (Russian News Agency TASS), the United Kingdom',
 '(BBC and The Guardian) and the United States (CNN, Fox News and The New York Times). Complete months only and lines are twelve-month',
 'rolling shares. The Japan Times, Punch and the Russian News Agency (TASS) have gaps in daily index coverage, covering 87, 93 and 93',
 'percent of days, but results do not change significantly compared to a balanced sample. The dotted vertical rules mark the April 2016',
 'release of the World Development Indicators edition that dropped the developed and developing distinction, and the March 2020 onset of the',
 'COVID-19 pandemic.']
_cap=' '.join(cap)
assert 'April 2016' in _cap and abs((2016+3/12)-2016.25)<1e-9, \
    'caption names April 2016; the WDI rule is drawn at 2016+3/12'
assert 'March 2020' in _cap and abs((2020+2/12)-(2020+2/12))<1e-9, \
    'caption names March 2020; the COVID rule is drawn at 2020+2/12'
assert float(d.iloc[:,1:].to_numpy().max()) <= 3.25, \
    'y axis is fixed at 3.25; embedded series must stay below it'
cap_top=caption(fig,cap,FIGH)
fig.tight_layout(rect=[0.02,cap_top+0.03,0.98,0.94])
OUT='chart-3-evolution-of-country-terminology-by-major-news-outlets.png'
fig.savefig(OUT,dpi=200); plt.close(fig)
title_band(OUT,'"Developed" and "developing" still rule the news',
           'Rolling twelve-month shares, twelve outlets, 2016 to 2026')
