# ---- Moving Frontiers house style (inlined) ----
import io, os, csv, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
RED='#C62828'; GOLD='#F9A825'; GREEN='#00897B'; BLUE='#283593'; GREY='#888888'; INK='#141414'; LIGHT='#CFCFCF'
PALETTE={1:[BLUE],2:[RED,BLUE],3:[RED,BLUE,GOLD],4:[RED,GOLD,GREEN,BLUE]}
def palette(n): return PALETTE[n]
REF_W=1980; W=1980; S=W/REF_W
GAP_TITLE_SUB=int(25*S); GAP_SUB_PLOT=int(70*S); GAP_PLOT_CAP=int(60*S); GAP_CAP_MARK=int(20*S); BORDER=int(70*S)
_FD=os.path.join(os.path.dirname(matplotlib.__file__),'mpl-data/fonts/ttf')
_REG=os.path.join(_FD,'DejaVuSans.ttf'); _BOLD=os.path.join(_FD,'DejaVuSans-Bold.ttf')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'xtick.labelsize':16,'ytick.labelsize':16,'legend.fontsize':16,
 'axes.labelsize':17,'axes.edgecolor':'#888','axes.linewidth':1.0,'axes.facecolor':'white','figure.facecolor':'white',
 'axes.spines.top':False,'axes.spines.right':False,'text.color':INK,'axes.labelcolor':INK,'xtick.color':'#444','ytick.color':'#444'})
PLOT_W=W-2*BORDER
def new_fig(h=7.4,left=0.12,right=0.96,bottom=0.14,top=0.97,aspect=0.798):
    fig,ax=plt.subplots(figsize=(PLOT_W/200,h),dpi=200)
    fig.subplots_adjust(left=left,right=right,bottom=bottom,top=top)
    if aspect: ax.set_box_aspect(aspect)
    return fig,ax
def save_csv(path,header,rows):
    with open(path,'w',newline='') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)
def _wrap(d,text,font,width):
    out=[];cur=''
    for w in text.split():
        t=(cur+' '+w).strip()
        if d.textlength(t,font=font)<=width: cur=t
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out
def _block(d,lines,font,top,pitch,fill,right=False):
    b0=d.textbbox((0,0),lines[0],font=font,anchor='ls'); base=top-b0[1]; low=top; boxes=[]
    for i,l in enumerate(lines):
        bl=base+i*pitch; bb=d.textbbox((0,bl),l,font=font,anchor='ls')
        x=(W-BORDER-bb[2]) if right else (BORDER-bb[0])
        d.text((x,bl),l,font=font,fill=fill,anchor='ls'); bb=d.textbbox((x,bl),l,font=font,anchor='ls')
        low=max(low,bb[3]-1); boxes.append(bb)
    return low,boxes
def _ink(img):
    a=np.asarray(img.convert('RGB')); m=(a<245).any(axis=2)
    ys=np.where(m.any(axis=1))[0]; xs=np.where(m.any(axis=0))[0]
    return xs[0],ys[0],xs[-1],ys[-1]
def compose(fig,title,subtitle,source,note,out):
    from matplotlib.text import Text
    fig.canvas.draw(); r=fig.canvas.get_renderer(); fw,fh=fig.bbox.width,fig.bbox.height
    skip=set()
    for a in fig.axes:
        for axis in (a.xaxis,a.yaxis):
            lo,hi=sorted(axis.get_view_interval())
            for tk in axis.get_major_ticks()+axis.get_minor_ticks():
                if not (lo-1e-9<=tk.get_loc()<=hi+1e-9): skip.update([id(tk.label1),id(tk.label2)])
    for t in fig.findobj(Text):
        if id(t) in skip: continue
        if t.get_visible() and t.get_text().strip():
            e=t.get_window_extent(r)
            assert e.x0>=-1 and e.x1<=fw+1 and e.y0>=-1 and e.y1<=fh+1, ('text outside figure',t.get_text()[:40])
    buf=io.BytesIO(); fig.savefig(buf,format='png',dpi=200,facecolor='white',bbox_inches='tight',pad_inches=0.12); plt.close(fig)
    ch=Image.open(buf).convert('RGB'); x0,y0,x1,y1=_ink(ch); ch=ch.crop((x0,y0,x1+1,y1+1))
    assert ch.width<=PLOT_W, ('plot too wide',ch.width,PLOT_W)
    tf=ImageFont.truetype(_BOLD,int(round(0.031*W))); sf=ImageFont.truetype(_REG,int(40*S))
    cf=ImageFont.truetype(_REG,int(27*S)); wf=ImageFont.truetype(_REG,int(32*S))
    tmp=Image.new('RGB',(W,6000),'white'); d=ImageDraw.Draw(tmp); G={}
    y,_=_block(d,_wrap(d,title,tf,PLOT_W),tf,BORDER,int(tf.size*1.25),(45,45,45)); G['title_bottom']=y
    y,_=_block(d,_wrap(d,subtitle,sf,PLOT_W),sf,y+1+GAP_TITLE_SUB,int(sf.size*1.3),(100,100,100)); G['sub_bottom']=y
    ptop=y+1+GAP_SUB_PLOT; tmp.paste(ch,(BORDER,ptop)); pbot=ptop+ch.height-1; G['plot_top']=ptop; G['plot_bottom']=pbot
    cap=_wrap(d,'Source: '+source,cf,PLOT_W)+(_wrap(d,'Note: '+note,cf,PLOT_W) if note else [])
    y,_=_block(d,cap,cf,pbot+1+GAP_PLOT_CAP,int(cf.size*1.38),(102,102,102)); G['cap_top']=pbot+1+GAP_PLOT_CAP; G['cap_bottom']=y
    y,_=_block(d,['movingfrontiers.substack.com'],wf,y+1+GAP_CAP_MARK,40,(102,102,102),right=True); G['mark_top']=G['cap_bottom']+1+GAP_CAP_MARK; G['mark_bottom']=y
    img=tmp.crop((0,0,W,y+1+BORDER)); img.save(out); verify(out,G); return out
def verify(path,G):
    img=Image.open(path); x0,y0,x1,y1=_ink(img)
    a=np.asarray(img.convert('RGB')); rows=(a<245).any(axis=2).any(axis=1)
    def gap_after(r):
        r0=r+1
        while not rows[r0]: r0+=1
        return r0-r-1
    def last_ink(r):
        while not rows[r]: r-=1
        return r
    chk={'top border':(y0,BORDER),'left border':(x0,BORDER),'bottom border':(img.height-1-y1,BORDER),
         'subtitle to plot':(gap_after(last_ink(G['sub_bottom'])),GAP_SUB_PLOT),
         'plot to caption':(gap_after(G['plot_bottom']),GAP_PLOT_CAP),
         'caption to mark':(gap_after(last_ink(G['cap_bottom'])),GAP_CAP_MARK)}
    for k,(got,want) in chk.items(): assert abs(got-want)<=1,(k,got,want)
    assert x1<=W-BORDER,('right border',x1)
    return True
# ---- end style ----

SLUG='chart-1-top-performers'
POOL={'B-S-J-Z (China)':27.2,'United States*':24.7,'Japan':8.7,'United Kingdom':4.7,'Türkiye':3.6,'Germany':3.6,'Korea':3.3,'France':2.7,'Canada*':2.2,
'Chinese Taipei':1.9,'Australia':1.8,'Poland':1.5,'Italy':1.2,'Brazil':1.1,'Spain':1.0,'Viet Nam':0.9,'Netherlands*':0.8,'Singapore':0.6,'Sweden':0.5}
# Share of students who are top performers (Level 5 or 6) in science, reading or mathematics, OECD PISA 2025 Table I.1
TOP={'B-S-J-Z (China)': 55.5, 'United States*': 17.8, 'Japan': 27.1, 'United Kingdom': 18.2, 'Türkiye': 11.1, 'Germany': 14.0, 'Korea': 28.1, 'France': 9.8, 'Canada*': 17.4, 'Chinese Taipei': 35.0, 'Australia': 18.2, 'Poland': 14.4, 'Italy': 10.1, 'Brazil': 1.8, 'Spain': 7.0, 'Viet Nam': 4.2, 'Netherlands*': 15.7, 'Singapore': 42.3, 'Sweden': 14.1, 'Malaysia': 0.8, 'Philippines': 0.3, 'Indonesia': 0.1, 'Thailand': 1.2, 'Cambodia': 0.0}
EXTRA=['Thailand','Malaysia','Philippines','Indonesia','Cambodia']
AP={'B-S-J-Z (China)','Japan','Korea','Chinese Taipei','Australia','Viet Nam','Singapore','Malaysia','Philippines','Indonesia','Thailand','Cambodia'}
rows=[(n,TOP[n],v) for n,v in POOL.items()]+[(n,TOP[n],None) for n in EXTRA]
save_csv(SLUG+'.csv',['system','top_performers_any_subject_pct','share_of_global_top_science_pool_pct','top_science_performers_estimated','asia_pacific'],
 [(n.replace('*',''),s,'' if p is None else p,'under 9400' if p is None else round(p/100*1875018),int(n in AP)) for n,s,p in rows])
AC,OC=palette(2)
import matplotlib.pyplot as plt
fig,(a1,a2)=plt.subplots(1,2,figsize=(PLOT_W/200,10.4),dpi=200); fig.subplots_adjust(left=0.19,right=0.97,bottom=0.1,top=0.92,wspace=0.45)
def panel(ax,data,key,xmax,fmt,title,short=False):
    data=sorted(data,key=lambda r:(-1+r[1]/1000 if key(r) is None else key(r)),reverse=False)
    y=np.arange(len(data))
    ax.barh(y,[key(r) or 0 for r in data],color=[AC if r[0] in AP else OC for r in data],height=0.66,zorder=3)
    for i,r in enumerate(data):
        v=key(r); ax.text((v or 0)+xmax*0.015,i,fmt(v),va='center',fontsize=13,color=INK)
    ax.set_yticks(y); ax.set_yticklabels([(r[0].replace(' (China)','') if short else r[0]).replace('*','') for r in data],fontsize=14); ax.tick_params(axis='y',length=0)
    for t,r in zip(ax.get_yticklabels(),data):
        if r[0] in AP: t.set_color(AC); t.set_fontweight('bold')
    ax.set_xlim(0,xmax); ax.set_ylim(-0.6,len(data)-0.4); ax.grid(axis='x',color='#EEEEEE',lw=0.8,zorder=0)
    ax.set_title(title,fontsize=15,loc='left',color=INK,x=-0.02)
panel(a1,rows,lambda r:r[1],66,lambda v:f'{v:.1f}','Top performers in any subject\n(% of each system\'s students)')
TOT=1875018
panel(a2,rows,lambda r:None if r[2] is None else r[2]/100*TOT/1000,580,lambda v:f'{v:,.0f}' if v is not None else 'under 9','Top science performers\n(thousands)',short=True)
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=AC,label='Asia-Pacific'),Patch(color=OC,label='Rest of world')],loc='lower center',bbox_to_anchor=(0.55,0.0),ncol=2,frameon=False,fontsize=15)
compose(fig,'Four Chinese provinces and the United States hold half the world\'s top science performers',
 'Share of top-performing students, and number of top science performers, PISA 2025',
 'OECD (2026), PISA 2025 Results (Volume I), Table I.1 and Figure I.1.4.',
 'The left panel counts students at Level 5 or 6 in science, reading or mathematics; the right panel science only, across all 91 participants.',
 SLUG+'.png')
