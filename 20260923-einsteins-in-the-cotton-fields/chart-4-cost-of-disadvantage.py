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

SLUG='chart-4-cost-of-disadvantage'
YEAR=20
D=[('Socio-economic status gap',85),('Material deprivation',64),('Social deprivation',53),('Any deprivation',52),('Immigrant background',43)]
save_csv(SLUG+'.csv',['gap','science_score_points','approx_years_of_schooling_at_20_points'],[(n,v,round(v/YEAR,1)) for n,v in D])
fig,ax=new_fig(h=6.8,left=0.40,right=0.96,bottom=0.2,top=0.97,aspect=None)
R=D[::-1]; y=np.arange(len(R))
ax.barh(y,[v for n,v in R],color=palette(1)[0],height=0.62,zorder=3)
for i,(n,v) in enumerate(R): ax.text(v+1.5,i,f'{v} pts  ≈ {v/YEAR:.1f} years',va='center',fontsize=15,fontweight='bold')
for k in range(1,6): ax.axvline(k*YEAR,color='#E3E3E3',lw=1,zorder=0)
ax.set_yticks(y); ax.set_yticklabels([n for n,v in R],fontsize=16); ax.tick_params(axis='y',length=0)
ax.set_xlim(0,150); ax.set_xticks([0,20,40,60,80,100]); ax.set_ylim(-0.6,len(R)-0.4)
ax.set_xlabel('Score points (each gridline = 1 school year)')
compose(fig,'By 15, a disadvantaged start costs about four years of learning in science',
 'Science score gaps associated with socio-economic status, deprivation and immigrant background, PISA 2025',
 'OECD (2026), PISA 2025 Results (Volume I), Table I.2, Box I.2.2 and Chapter 2.',
 'The OECD puts the average yearly learning gain around age 15 at roughly 20 score points, which the year equivalents use. Deprivation gaps are averages across participating systems, the others OECD averages. Immigrant gaps are before adjusting for socio-economic status and language. On the OECD average, 37% of disadvantaged students are low performers in science, against 12% of advantaged students.',
 SLUG+'.png')
