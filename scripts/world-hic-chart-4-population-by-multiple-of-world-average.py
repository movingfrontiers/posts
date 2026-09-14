"""Chart 4: population by multiple of the world average.

Self-sufficient: the data this chart consumes are embedded below, frozen at the
July 2026 vintage. No external files, downloads or network access. Writes the png
of the same name. Run from any directory:
  python3 chart-4-population-by-multiple-of-world-average-build.py
Requires Python 3 with numpy, matplotlib and Pillow.
"""
# ------------------------------------------------------------------ provenance
# Embedded data, frozen 29 August 2026 from the chart csv of the replication
# bundle for "If the World Were a Country, It Would Be a Very Strange One"
# (https://movingfrontiers.substack.com/p/the-world-turns-rich-this-year).
# Upstream sources: World Bank OGHIST classification and income thresholds,
# release of 1 July 2026; World Bank WDI, GNI per capita, Atlas method
# (NY.GNP.PCAP.CD) and population (SP.POP.TOTL), July 2026 release; UN World
# Population Prospects 2024, medium variant.
# Values for 2026 onward are not raw source data: they are the author's
# nowcast and projection (conservative constant-pace scenario), carried from
# the projection workbook into the bundle csv and frozen here.
# Do not replace the embedded table with a live download or API call: the
# output is pinned to this vintage and must keep running offline.
# The shared helper functions and the caption texts are duplicated verbatim
# across the five chart scripts of this folder; the duplication is deliberate
# so each file stays single-file self-sufficient.
# The caption's world GNI per capita of $14,801 is derived upstream and cannot
# be recomputed from the band totals embedded here; the 8.14 billion population
# total can be, and is asserted below. The in-chart note 'China is nowcast to
# cross the average in 2026, moving 1.4 bn' is country-level detail that is not
# present in this banded table and is likewise not assertable here.
import os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

RED='#C62828'; AMBER='#F9A825'; AMBERTXT='#B8860B'; INDIGO='#283593'; INK='#141414'

SRC=("Source: World Bank OGHIST classification and income thresholds, 1 July 2026; GNI per capita, Atlas method, and population from "
"World Bank WDI, July 2026 release; UN World Population Prospects 2024, medium variant; author's calculations and projections. "
"Schellekens 2026, The Great Income Inversion, Moving Frontiers." + chr(10))
PROJ=("Note: Values are for 2026, which reflects a nowcast based on a conservative constant-pace scenario that replicates country-level "
"median per capita income growth over the last decade. See Schellekens 2026 for methodology. ")
CAVEAT=("World GNI per capita is world GNI divided by world population, $14,801 in 2026, covering 8.14 billion people. Every person "
"carries their own country's average, so this is inequality between countries, not within them. ")

def frame(figsize):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.edgecolor':'#888',
     'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':10,'ytick.labelsize':10})
    fig,ax=plt.subplots(figsize=figsize,dpi=200)
    ax.grid(axis='y',color='#E8E8E8',lw=0.8,zorder=0); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    return fig,ax

# ---------------------------------------------------------------- shared helpers
def caption(fig, ax, cap, fs, url_on_last_line, gap_lines=2.0, use_xlabel=False):
    """Moving Frontiers caption block. The watermark either sits on the baseline of
    the last note line, or on its own line below it."""
    fig.canvas.draw(); r=fig.canvas.get_renderer()
    Wpx=fig.get_figwidth()*fig.dpi
    bots=[t.get_window_extent(r).y0 for t in ax.get_xticklabels() if t.get_text()]
    if use_xlabel and ax.xaxis.label.get_text():
        bots.append(ax.xaxis.label.get_window_extent(r).y0)
    xb=fig.transFigure.inverted().transform((0,min(bots)))[1]
    for lg in fig.legends:
        lb=lg.get_window_extent(r).transformed(fig.transFigure.inverted())
        if lb.y1<xb: xb=min(xb,lb.y0)
    LH=fs*1.2/(72*fig.get_figheight())
    pr=fig.text(0,0,'0',fontsize=fs); fig.canvas.draw()
    CW=pr.get_window_extent(fig.canvas.get_renderer()).width/Wpx; pr.remove()
    def w(t,size=fs):
        tt=fig.text(0,0,t,fontsize=size); fig.canvas.draw()
        v=tt.get_window_extent(fig.canvas.get_renderer()).width/Wpx; tt.remove(); return v
    URL='movingfrontiers.substack.com'; UFS=fs*1.2
    x0=0.012; right=1.0-70.0/Wpx
    full=right-x0
    lastmax=right-w(URL,UFS)-2.0*CW-x0 if url_on_last_line else full
    lines=[]
    for para in cap.split(chr(10)):
        cur=''
        for word in para.split():
            z=(cur+' '+word).strip()
            if w(z)<=full or not cur: cur=z
            else: lines.append(cur); cur=word
        lines.append(cur)
    if url_on_last_line:
        for _ in range(400):
            if w(lines[-1])>lastmax and ' ' in lines[-1]:
                h,_,t=lines[-1].rpartition(' '); lines[-1]=h; lines.append(t); continue
            if len(lines)>=2 and w(lines[-2])>lastmax and ' ' in lines[-2]:
                h,_,t=lines[-2].rpartition(' ')
                lines[-2]=h; lines[-1]=(t+' '+lines[-1]).strip(); continue
            break
        if len(lines)>=2:
            while ' ' in lines[-2]:
                h,_,t=lines[-2].rpartition(' ')
                cand=(t+' '+lines[-1]).strip()
                if w(cand)>lastmax: break
                if abs(w(cand)-w(h))>=abs(w(lines[-1])-w(lines[-2])): break
                lines[-2]=h; lines[-1]=cand
    top=xb-gap_lines*LH
    objs=[fig.text(x0,top-i*LH,ln,fontsize=fs,color='#666',va='top') for i,ln in enumerate(lines)]
    fig.canvas.draw(); r2=fig.canvas.get_renderer()
    lb=objs[-1].get_window_extent(r2).transformed(fig.transFigure.inverted())
    if url_on_last_line:
        fig.text(right,lb.y0,URL,ha='right',va='bottom',fontsize=UFS,color='#999')
        assert lb.y0>0.004,'caption runs off the canvas'
    else:
        fig.text(right,lb.y0-0.45*LH,URL,ha='right',va='top',fontsize=UFS,color='#999')
        assert lb.y0-0.45*LH>0.004,'caption runs off the canvas'
    print('  caption %d lines'%len(lines))

def title_band(path, title, sub, title_frac, sub_frac):
    """Composite the title and subtitle above the rendered figure with PIL, after
    cropping the figure to its ink, so a two-line title never squeezes the plot."""
    _ttf=os.path.join(matplotlib.get_data_path(),'fonts','ttf')
    FB=os.path.join(_ttf,'DejaVuSans-Bold.ttf')
    FR=os.path.join(_ttf,'DejaVuSans.ttf')
    if not os.path.isfile(FB): FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.isfile(FR): FR='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    assert os.path.isfile(FB) and os.path.isfile(FR), 'DejaVu Sans fonts not found in the matplotlib bundle or the system path'
    im=Image.open(path).convert('RGB')
    a=np.array(im.convert('L')); rr=np.where((a<250).sum(axis=1)>0)[0]
    im=im.crop((0,0,im.size[0],min(im.size[1],int(rr.max())+10)))
    W,H=im.size
    fs=int(W*title_frac); f1=ImageFont.truetype(FB,fs)
    fss=int(W*sub_frac);  f2=ImageFont.truetype(FR,fss)
    dd=ImageDraw.Draw(im); M=int(W*0.03); LIM=W-2*M
    def wrap(t,f):
        o=[];cur=''
        for x in t.split():
            z=(cur+' '+x).strip()
            if dd.textlength(z,font=f)<=LIM: cur=z
            else: o.append(cur); cur=x
        o.append(cur); return o
    tl=wrap(title,f1); sl=wrap(sub,f2)
    lh=int(fs*1.25); lhs=int(fss*1.35)
    bh=int(fs*0.85)+lh*len(tl)+int(fss*0.55)+lhs*len(sl)+int(fs*0.22)
    cv=Image.new('RGB',(W,H+bh),'white'); cv.paste(im,(0,bh))
    dr=ImageDraw.Draw(cv); y=int(fs*0.85)
    for ln in tl: dr.text((M,y),ln,font=f1,fill=(45,45,45)); y+=lh
    y+=int(fss*0.4)
    for ln in sl: dr.text((M,y),ln,font=f2,fill=(100,100,100)); y+=lhs
    cv.save(path,optimize=True)
    print('  wrote %s  %dx%d'%(path,cv.size[0],cv.size[1]))

# --------------------------------------------- embedded data (see provenance)
BANDS=(  # (band, population_billions, n_economies), csv row order poorest band first
('under 0.1x',1.08,26),
('0.1 to 0.25x',2.442,29),
('0.25 to 0.5x',1.047,36),
('0.5 to 1x',0.631,30),
('1 to 2x',1.817,29),
('2 to 4x',0.57,26),
('over 4x',0.549,21),
)
ALL_BANDS=(8.137,197)  # the csv "all bands" totals row: population_billions, n_economies
LABS=['under'+chr(10)+'0.1x','0.1-'+chr(10)+'0.25x','0.25-'+chr(10)+'0.5x','0.5-'+chr(10)+'1x','1-2x','2-4x','over'+chr(10)+'4x']
pop=np.array([b[1] for b in BANDS])
n=[b[2] for b in BANDS]
below=pop[:4].sum(); above=pop[4:].sum()
assert round(float(pop.sum()),2)==8.14 and round(ALL_BANDS[0],2)==8.14, 'caption: "covering 8.14 billion people" (band sum and the all-bands row)'
assert sum(b[2] for b in BANDS)==ALL_BANDS[1]==197, 'economy counts inside the bars must sum to the all-bands total of 197'
assert round(float(100*below/(below+above)))==64, 'title "Two in three people live in a country poorer than the world average" rests on the 64 percent below-average share'
fig,ax=frame((7.6,7.1))
fig.tight_layout(rect=[0.02,0.385,0.99,0.985])
x=np.arange(len(BANDS)); col=[RED]*4+[INDIGO]*3
ax.bar(x,pop,0.74,color=col,zorder=5)
ax.axvline(3.5,ls='--',lw=1.8,color=INK,zorder=6)
for i,(v,c) in enumerate(zip(pop,n)):
    ax.text(i,v+0.055,'%.2f bn'%v,ha='center',va='bottom',fontsize=10,fontweight='bold',
            color=RED if i<4 else INDIGO,zorder=7)
    ax.text(i,0.045,'%d'%c,ha='center',va='bottom',fontsize=8.5,color='white',fontweight='bold',zorder=7)
ax.text(1.5,3.16,'Below the world average'+chr(10)+'%.2f bn people, %.0f%% of humanity'%(below,100*below/(below+above)),
        fontsize=10.5,fontweight='bold',color=RED,ha='center',va='top',linespacing=1.35,zorder=8)
ax.text(4.9,3.16,'Above'+chr(10)+'%.2f bn, %.0f%%'%(above,100*above/(below+above)),
        fontsize=10.5,fontweight='bold',color=INDIGO,ha='center',va='top',linespacing=1.35,zorder=8)
_ct=ax.text(4.62,2.36,'China is nowcast to'+chr(10)+'cross the average in'+chr(10)+'2026, moving 1.4 bn',
    fontsize=9.5,fontweight='bold',color=INDIGO,ha='left',va='top',linespacing=1.3,zorder=9)
fig.canvas.draw()
_bb=_ct.get_window_extent(fig.canvas.get_renderer()); _inv=ax.transData.inverted()
(_x0,_y0)=_inv.transform((_bb.x0,_bb.y0)); (_x1,_y1)=_inv.transform((_bb.x1,_bb.y1))
ax.plot([min(_x0,_x1)-0.08,4.34],[(min(_y0,_y1)+max(_y0,_y1))/2,pop[4]+0.10],color=INDIGO,lw=0.6,zorder=8)
ax.set_xticks(x); ax.set_xticklabels(LABS,fontsize=9.5)
ax.set_ylim(0,3.24); ax.set_yticks([0,0.5,1.0,1.5,2.0,2.5])
ax.set_xlabel('GNI per capita as a multiple of world GNI per capita',fontsize=10.5)
ax.set_ylabel('Billions of people',fontsize=10.5)
caption(fig,ax,SRC+PROJ+CAVEAT+("Bars show how many people live in economies in each band, with the number of economies in "
 "white inside each bar. The dashed line is the world average."),7.6,url_on_last_line=False,gap_lines=1.19,use_xlabel=True)
fig.savefig('chart-4-population-by-multiple-of-world-average.png',dpi=200); plt.close(fig)
title_band('chart-4-population-by-multiple-of-world-average.png','Two in three people live in a country poorer than the world average',
 'Population by economy GNI per capita relative to the world average, billions of people, 2026',0.0285,0.0168)
