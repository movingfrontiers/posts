# =============================================================================
# Chart 8: the middle of the classification is emptying out
#
# Provenance, frozen vintage. Nothing is read from disk or the network.
#   Classifications       : World Bank OGHIST, 1 July 2026, Country Analytical History.
#   GNI per capita        : World Bank WDI, July 2026 vintage, Atlas method, current US$.
#   Vintage freeze date   : 1 July 2026. The chart is pinned to this vintage; do not swap
#                           the embedded data for a live API call.
#
# Reduction: The script reads three columns of its companion csv at the seven-decade span
# 1987-2050. Those columns are embedded here as COLS and ROWS; the csv still ships
# alongside as the published data file.
#
# Values from 2026 are a nowcast inherited from the shared upstream projection
# pipeline (decade-median growth, floored at the threshold drift, capped at the
# group's 90th percentile) and are embedded here already resolved.
# =============================================================================
"""Chart 8: the middle of the classification, in counts and shares.

Reads chart-8-the-middle-of-the-classification-is-emptying-out.csv and writes the png of the same name.
Run from inside this folder:  python3 chart-8-the-middle-of-the-classification-is-emptying-out-build.py
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont

SRC=("Source: World Bank OGHIST (1 July 2026), Country Analytical History, with WDI GNI per capita, Atlas method; author's calculations."+chr(10))

# ---------------------------------------------------------------- shared helpers

def place_marks(fig, ax, YY, series, marks, fontsize=10.5, pad_frac=0.014, align_x=None, override=None, dots=True, dotsize=8.5):
    """Put a value label near its point, clear of every series and every other label."""
    inv=ax.transData.inverted()
    span=ax.get_ylim()[1]-ax.get_ylim()[0]
    pad=span*pad_frac
    out=[]; fixed=[]
    def box(t):
        bb=t.get_window_extent(fig.canvas.get_renderer())
        (a0,b0)=inv.transform((bb.x0,bb.y0)); (a1,b1)=inv.transform((bb.x1,bb.y1))
        return a0,a1,min(b0,b1),max(b0,b1)
    def bad(b,skip=None):
        a0,a1,lo,hi=b
        if a1>ax.get_xlim()[1] or a0<ax.get_xlim()[0]: return True
        if hi>ax.get_ylim()[1] or lo<ax.get_ylim()[0]: return True
        xs=[q for q in YY if a0-0.7<=q<=a1+0.7]
        for s in series:
            if any(lo-pad<=s[YY.index(q)]<=hi+pad for q in xs): return True
        gx,gy=0.8,span*0.018
        for j,ot in enumerate(out):
            if j==skip: continue
            ob=box(ot)
            if a0-gx<ob[1] and ob[0]<a1+gx and lo-gy<ob[3] and ob[2]<hi+gy: return True
        return False
    for item in marks:
        yr,txt,prefer,own,col=item
        yv=own[YY.index(yr)]
        if dots:
            ax.plot([yr],[yv],'o',color=col,ms=dotsize,zorder=30,
                    markeredgecolor='white',markeredgewidth=1.1,clip_on=False)
        cands=[]
        if override and (col,yr) in override:
            ox,oy,oha,ova=override[(col,yr)]; cands=[(ox,oy,oha,ova)]
        elif align_x is not None and yr in align_x:
            lx,ha=align_x[yr]
            for st in (0.045,0.065,0.088,0.113,0.140,0.170,0.203,0.240,0.280):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    cands.append((lx,yv+side*span*st,ha,'bottom' if side>0 else 'top'))
            cands.append((lx,yv,ha,'center'))
        else:
            for st in (0.050,0.070,0.095,0.125,0.160,0.200,0.245):
                for side in ([1,-1] if prefer=='above' else [-1,1]):
                    for dx,ha in ((-0.6,'right'),(0.6,'left'),(0.0,'center'),
                                  (2.5,'left'),(-2.5,'right'),(5.0,'left'),(-5.0,'right'),
                                  (8.0,'left'),(-8.0,'right')):
                        xr=min(max(yr+dx,YY[0]),YY[-1])
                        cands.append((xr,own[YY.index(int(round(xr)))]+side*span*st,ha,
                                      'bottom' if side>0 else 'top'))
        t=ax.text(0,0,txt,fontsize=fontsize,fontweight='bold',color=col,linespacing=1.25,zorder=9)
        out.append(t)
        if override and (col,yr) in override:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            fixed.append(len(out)-1); continue
        ok=False
        for lx,ly,ha,va in cands:
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
            if not bad(box(t),skip=len(out)-1): ok=True; break
        if not ok:
            lx,ly,ha,va=cands[0]
            t.set_position((lx,ly)); t.set_ha(ha); t.set_va(va); fig.canvas.draw()
    for _ in range(60):
        fig.canvas.draw(); moved=False
        for i,t in enumerate(out):
            if i in fixed: continue
            if bad(box(t),skip=i):
                x,y=t.get_position(); up=t.get_va()!='top'
                ny=y+(span*0.030 if up else -span*0.030)
                if ax.get_ylim()[0]<ny<ax.get_ylim()[1]: t.set_y(ny); moved=True
        if not moved: break
    return out

def caption(fig, ax, cap, fs=7.8, gap_lines=2.0):
    """Moving Frontiers caption block: every line runs full width except the last two,
    which stop short so the watermark can sit on the baseline of the last line."""
    fig.canvas.draw(); r=fig.canvas.get_renderer()
    Wpx=fig.get_figwidth()*fig.dpi
    bots=[t.get_window_extent(r).y0 for t in ax.get_xticklabels() if t.get_text()]
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
    lastmax=right-w(URL,UFS)-2.0*CW-x0
    lines=[]
    for para in cap.split(chr(10)):
        cur=''
        for word in para.split():
            z=(cur+' '+word).strip()
            if w(z)<=full or not cur: cur=z
            else: lines.append(cur); cur=word
        lines.append(cur)
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
    fig.canvas.draw()
    lb=objs[-1].get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    fig.text(right,lb.y0,URL,ha='right',va='bottom',fontsize=UFS,color='#999')
    assert lb.y0>0.004,'caption runs off the canvas'
    print('  caption %d lines'%len(lines))

def title_band(path, title, sub, tf=0.0285, sf=0.0168):
        # ---- fonts: DejaVu from matplotlib's bundled ttf, system path only as a fallback ----
    import os as _os
    from matplotlib import font_manager as _fm
    def _dejavu(stem):
        p=_os.path.join(matplotlib.get_data_path(),'fonts','ttf',stem)
        if _os.path.exists(p): return p
        try:
            q=_fm.findfont(_fm.FontProperties(family='DejaVu Sans',
                weight=('bold' if 'Bold' in stem else 'normal')),fallback_to_default=False)
            if _os.path.basename(q)==stem and _os.path.exists(q): return q
        except Exception: pass
        p=_os.path.join('/usr/share/fonts/truetype/dejavu',stem)
        if _os.path.exists(p): return p
        raise FileNotFoundError('DejaVu font not found: '+stem)
    FB=_dejavu('DejaVuSans-Bold.ttf'); FR=_dejavu('DejaVuSans.ttf')
    assert _os.path.exists(FB) and _os.path.exists(FR), 'resolved DejaVu font files must exist'
    im=Image.open(path).convert('RGB')
    a=np.array(im.convert('L')); rr=np.where((a<250).sum(axis=1)>0)[0]
    im=im.crop((0,0,im.size[0],min(im.size[1],int(rr.max())+13)))
    W,H=im.size
    fs=int(W*tf); f1=ImageFont.truetype(FB,fs)
    fss=int(W*sf); f2=ImageFont.truetype(FR,fss)
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
    dr=ImageDraw.Draw(cv); y=int(fs*0.85)+3
    for ln in tl: dr.text((M,y),ln,font=f1,fill=(45,45,45)); y+=lh
    y+=int(fss*0.4)
    for ln in sl: dr.text((M,y),ln,font=f2,fill=(100,100,100)); y+=lhs
    cv.save(path,optimize=True)
    print('  wrote %s  %dx%d'%(path,cv.size[0],cv.size[1]))

AMBER='#F9A825'; AMBERTXT='#B8860B'; RED='#C62828'; INDIGO='#283593'
def panel(ax,ymax,ticks,lab,tickfmt):
    ax.axvspan(2025.5,2050,color='#F4F4F4',zorder=0)
    ax.axvline(2025.5,ls=':',lw=1.4,color='#777',zorder=1)
    ax.grid(axis='y',color='#E6E6E6',lw=0.8,zorder=0); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.set_xlim(1987,2050); ax.set_xticks([1987,2000,2010,2020,2030,2040,2050])
    ax.set_ylim(0,ymax); ax.set_yticks(list(ticks))
    if tickfmt: ax.set_yticklabels([tickfmt(v) for v in ticks])
    ax.set_title(lab,fontsize=13,fontweight='bold',color='#333',pad=8)
def draw(ax,YY,S,col,NH):
    ax.plot(YY[:NH],S[:NH],color=col,lw=2.9,zorder=5,solid_capstyle='round')
    ax.plot(YY[NH-1:],S[NH-1:],color=col,lw=2.5,ls=(0,(4.5,2.2)),zorder=5)

PNG='chart-8-the-middle-of-the-classification-is-emptying-out.png'
LEVCOL='middle_income_economies'
SHCOL='middle_income_share_of_classified_percent'
LEVTTL='Number of economies'
SHTTL='Percent of all classified economies'
YMAXL=152
TICKSL=range(0,131,25)
FMTL=None
YMAXS=70
TICKSS=range(0,61,10)
VALL=lambda v:'%d'%v
VALS=lambda v:'%.0f%%'%v
PKL=1992
PKS=1992
PEAK_LIFT=True
OVR=None
NOTE=("Note: Counts of economies, not people. Middle income combines the lower-middle and upper-middle groups. Classifications are actual "
"through 2025 and projected from 2026. Shares are of all economies classified in that year, a total that rises from 166 in 1987 to 218 "
"from 2025 on as new economies enter, so the counts and the shares carry different information. Projection: GNI per capita grows at each "
"economy's median annual rate over the decade to 2025, floored at the 1.244 percent threshold drift so that no economy is downgraded, "
"and capped at the 90th percentile of decade medians within its own 2025 income group. All three thresholds drift up at 1.244 percent a "
"year, the median annual increase in the published thresholds over the same decade to 2025.")
TITLE="The middle of the classification is emptying out"
SUB="Number of lower-middle and upper-middle-income economies combined, and as a percent of all classified economies"

# ---- embedded data, see the provenance header ----
COLS=['year', 'middle_income_economies', 'middle_income_share_of_classified_percent']
ROWS=[(1987.0,76.0,45.7831),(1988.0,78.0,46.7066),(1989.0,77.0,45.2941),(1990.0,89.0,49.4444),(1991.0,104.0,52.7919),(1992.0,110.0,53.9216),(1993.0,106.0,51.7073),(1994.0,97.0,47.0874),(1995.0,94.0,45.6311),(1996.0,94.0,45.4106),(1997.0,95.0,45.8937),(1998.0,93.0,44.9275),(1999.0,93.0,44.9275),(2000.0,92.0,44.2308),(2001.0,90.0,43.0622),(2002.0,88.0,42.1053),(2003.0,93.0,44.4976),(2004.0,94.0,44.9761),(2005.0,98.0,46.89),(2006.0,96.0,45.7143),(2007.0,95.0,45.2381),(2008.0,101.0,47.8673),(2009.0,104.0,48.5981),(2010.0,110.0,50.9259),(2011.0,108.0,50.2326),(2012.0,103.0,47.907),(2013.0,105.0,48.8372),(2014.0,104.0,48.3721),(2015.0,108.0,49.5413),(2016.0,109.0,50.0),(2017.0,103.0,47.2477),(2018.0,107.0,49.0826),(2019.0,106.0,48.6239),(2020.0,110.0,50.6912),(2021.0,108.0,49.7696),(2022.0,108.0,49.7696),(2023.0,105.0,48.3871),(2024.0,104.0,48.1481),(2025.0,106.0,48.6239),(2026.0,101.0,46.3303),(2027.0,100.0,45.8716),(2028.0,99.0,45.4128),(2029.0,99.0,45.4128),(2030.0,98.0,44.9541),(2031.0,98.0,44.9541),(2032.0,96.0,44.0367),(2033.0,92.0,42.2018),(2034.0,89.0,40.8257),(2035.0,89.0,40.8257),(2036.0,89.0,40.8257),(2037.0,89.0,40.8257),(2038.0,88.0,40.367),(2039.0,87.0,39.9083),(2040.0,86.0,39.4495),(2041.0,87.0,39.9083),(2042.0,87.0,39.9083),(2043.0,86.0,39.4495),(2044.0,83.0,38.0734),(2045.0,82.0,37.6147),(2046.0,80.0,36.6972),(2047.0,80.0,36.6972),(2048.0,79.0,36.2385),(2049.0,78.0,35.7798),(2050.0,78.0,35.7798)]
rows=[dict(zip(COLS,r)) for r in ROWS]
YY=[int(r['year']) for r in rows]
LEV=[float(r[LEVCOL]) for r in rows]
SH=[float(r[SHCOL]) for r in rows]
NH=YY.index(2025)+1
# ---- the chart's stated numbers must follow from the embedded data ----
assert YY[0]==1987 and YY[-1]==2050 and len(YY)==64, 'the series runs 1987 to 2050'
assert PKL==1992 and int(max(LEV))==110, 'the counts peak label states 110 in 1992'
assert PKS==1992 and round(max(SH))==54, 'the shares peak label states 54 percent in 1992'
PLABL='peak %d%s'%(PKL,' (nowcast)' if PKL==2025 else '')+chr(10)+VALL(max(LEV))
PLABS='peak %d'%PKS+chr(10)+VALS(max(SH))
OVR={'sh':{(AMBERTXT,2050):(2049.0,SH[-1]+3.6,'right','bottom')}}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.edgecolor':'#888',
 'axes.linewidth':1.0,'figure.facecolor':'white','xtick.labelsize':12,'ytick.labelsize':12})
fig,axs=plt.subplots(1,2,figsize=(9.6,6.3),dpi=200)
for ax,(S,ttl,ymax,ticks,fmt,vf,pk,plab) in zip(axs,
        [(LEV,LEVTTL,YMAXL,TICKSL,FMTL,VALL,PKL,PLABL),
         (SH,SHTTL,YMAXS,TICKSS,None,VALS,PKS,PLABS)]):
    panel(ax,ymax,ticks,ttl,fmt)
    draw(ax,YY,S,AMBER,NH)
    ax.plot([pk],[S[YY.index(pk)]],'o',mfc='white',mec=AMBERTXT,mew=2.6,ms=13,zorder=30,clip_on=False)
    place_marks(fig,ax,YY,[S],[(pk,plab,'above',S,AMBERTXT)],fontsize=10.5,dots=False)
    if PEAK_LIFT:
        fig.canvas.draw()
        _pr=ax.text(0,0,'0',fontsize=10.5); fig.canvas.draw()
        _bb=_pr.get_window_extent(fig.canvas.get_renderer()); _pr.remove()
        _inv=ax.transData.inverted()
        _h=abs(_inv.transform((0,_bb.height))[1]-_inv.transform((0,0))[1])
        ax.texts[-1].set_y(ax.texts[-1].get_position()[1]+0.5*_h)
    MK=[(1987,vf(S[YY.index(1987)]),'below',S,AMBERTXT)]
    if 2025!=pk: MK.append((2025,vf(S[YY.index(2025)]),'above',S,AMBERTXT))
    MK.append((2050,vf(S[-1]),'above',S,AMBERTXT))
    place_marks(fig,ax,YY,[S],MK,fontsize=10.5,override=(OVR.get('lev' if S is LEV else 'sh') if OVR else None))
    ax.text(2026.4,ymax*0.955,'projected',fontsize=10.5,color='#777',style='italic',ha='left',va='top')
fig.tight_layout(rect=[0,0.300,1,0.985]); fig.subplots_adjust(wspace=0.16)
caption(fig,axs[0],SRC+NOTE)
fig.savefig(PNG,dpi=200); plt.close(fig)
title_band(PNG,TITLE,SUB)
