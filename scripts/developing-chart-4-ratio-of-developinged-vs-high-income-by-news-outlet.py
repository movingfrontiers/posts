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
# Derived: the ratios are the integer labels of the published figure.
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
    ('TASS (Russia)', 28),
    ('Punch (Nigeria)', 10),
    ('The Japan Times (Japan)', 9),
    ('The Times of India (India)', 9),
    ('South China Morning Post (China)', 8),
    ('The Guardian (UK)', 5),
    ('Fox News (US)', 5),
    ('The Star (Malaysia)', 5),
    ('BBC (UK)', 4),
    ('The New York Times (US)', 4),
    ('Al Jazeera (Qatar)', 4),
    ('CNN (US)', 2),
]
COLS = ['outlet', 'developed_stories_per_high_income_story_2016_2026']
d = pd.DataFrame(ROWS, columns=COLS)
FIGW,FIGH = 8, 7.8
fig,ax = plt.subplots(figsize=(FIGW,FIGH))
n=len(d); y=np.arange(n)[::-1]
vals=d['developed_stories_per_high_income_story_2016_2026']
ax.barh(y,vals,0.55,color=TEAL)
ax.axvline(1,color='#999',lw=1.6,zorder=0)
for yi,v in zip(y,vals):
    ax.text(v+0.4,yi,str(int(v)),va='center',fontsize=13,color='#333')
ax.set_yticks(y); ax.set_yticklabels([o.replace(' (','  (') for o in d['outlet']],fontsize=12)
ax.set_xlim(0,30.5); ax.set_xticks(range(0,31,5))
ax.set_xlabel('"Developed" stories per "high-income" story, 2016 to 2026',fontsize=12)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.tick_params(axis='y',length=0)
cap=[
 'Source: Media Cloud story index, January 2016 to July 2026, retrieved August 2026. Queries match the exact phrases developing country or',
 'countries, developed country or countries, and high-income country or countries, language English.',
 'Note: The Russian News Agency (TASS) mentioned the high-income country term in only 10 stories across the',
 'whole decade.']
assert len(d)==12, 'chart shows twelve outlets; embedded table must have 12 rows'
assert list(d.iloc[:,1])==sorted(d.iloc[:,1],reverse=True), \
    'bars are drawn in the embedded order, which must be descending'
# The caption figure of 10 TASS stories is query metadata, not derivable from
# the embedded ratios; it is recorded here as a documented constant.
cap_top=caption(fig,cap,FIGH)
fig.tight_layout(rect=[0.02,cap_top+0.03,0.98,0.985])
OUT='chart-4-ratio-of-developed-vs-high-income-by-news-outlet.png'
fig.savefig(OUT,dpi=200); plt.close(fig)
title_band(OUT,'Non-Western media favor "developed" over "high income" more strongly',
           'Ratio of developed to high-income mentions by outlet')
