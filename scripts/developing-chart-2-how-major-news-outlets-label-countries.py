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
    ('The Japan Times (Japan)', 6.13, 4.08, 0.43),
    ('Al Jazeera (Qatar)', 5.3, 2.64, 0.73),
    ('The New York Times (US)', 3.98, 2.03, 0.56),
    ('The Guardian (UK)', 3.88, 2.06, 0.45),
    ('Punch (Nigeria)', 3.35, 2.96, 0.28),
    ('South China Morning Post (China)', 3.28, 1.96, 0.23),
    ('TASS (Russia)', 3.27, 1.09, 0.04),
    ('CNN (US)', 1.86, 1.08, 0.51),
    ('The Star (Malaysia)', 1.39, 0.71, 0.15),
    ('The Times of India (India)', 1.04, 0.9, 0.1),
    ('BBC (UK)', 0.63, 0.34, 0.09),
    ('Fox News (US)', 0.6, 0.35, 0.07),
]
COLS = ['outlet', 'stories_per_1000_developing_country', 'stories_per_1000_developed_country', 'stories_per_1000_high_income_country']
d = pd.DataFrame(ROWS, columns=COLS)
FIGW,FIGH = 8, 8.4
fig,ax = plt.subplots(figsize=(FIGW,FIGH))
n=len(d); h=0.24
y=np.arange(n)[::-1]
ax.barh(y+h, d['stories_per_1000_developing_country'], h, color=RED,
        label='"Developing country"')
ax.barh(y,    d['stories_per_1000_developed_country'],  h, color=TEAL,
        label='"Developed country"')
ax.barh(y-h,  d['stories_per_1000_high_income_country'],h, color=INDIGO,
        label='"High-income country"')
ax.set_yticks(y); ax.set_yticklabels([o.replace(' (','  (') for o in d['outlet']],fontsize=12)
ax.set_xlim(0,6.5); ax.set_xticks(range(0,7))
ax.set_xlabel('Stories per 1,000 published, 2016 to 2026',fontsize=13)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.tick_params(axis='y',length=0)
ax.legend(loc='upper center',bbox_to_anchor=(0.42,-0.085),ncol=3,frameon=False,fontsize=10.5,columnspacing=1.1,handlelength=1.4)
cap=[
 'Source: Media Cloud story index, January 2016 to July 2026, retrieved August 2026. Queries match the exact phrases developing country or',
 'countries, developed country or countries, and high-income country or countries, language English.',
 'Note: All months, covering the twelve outlets grouped by country: Hong Kong SAR, China (South China Morning Post), India (The Times of',
 'India), Japan (The Japan Times), Malaysia (The Star), Nigeria (Punch), Qatar (Al Jazeera), Russia (Russian News Agency TASS), the United',
 'Kingdom (BBC and The Guardian) and the United States (CNN, Fox News and The New York Times). Shares are stories matching each query per',
 '1,000 stories the outlet published over the whole period. The Japan Times, Punch and the Russian News Agency (TASS) have gaps in daily',
 'index coverage, covering 87, 93 and 93 percent of days, but results do not change significantly compared to a',
 'balanced sample.']
_cap=' '.join(cap)
assert 'twelve outlets' in _cap and len(d)==12, \
    'caption says twelve outlets; embedded table must have 12 rows'
cap_top=caption(fig,cap,FIGH)
fig.tight_layout(rect=[0.02,cap_top+0.03,0.98,0.985])
OUT='chart-2-how-major-news-outlets-label-countries.png'
fig.savefig(OUT,dpi=200); plt.close(fig)
title_band(OUT,'How major news outlets label countries',
           'Mentions per 1,000 stories by outlet, full period')
