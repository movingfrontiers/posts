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

SLUG='chart-6-stem-conversion'
T1=1875018; T2=1024311
D=[('B-S-J-Z (China)',27.2,17.1,1),('United States',24.7,29.9,0),('Japan',8.7,7.1,1),('United Kingdom',4.7,5.5,0),('Germany',3.6,3.3,0),
('Türkiye',3.6,4.5,0),('Korea',3.3,3.5,1),('France',2.7,4.0,0),('Canada',2.2,3.1,0),('Chinese Taipei',1.9,2.1,1),('Australia',1.8,2.1,1),
('Poland',1.5,1.5,0),('Italy',1.2,1.2,0),('Brazil',1.1,1.7,0),('Spain',1.0,1.2,0),('Viet Nam',0.9,0.7,1),('Netherlands',0.8,0.8,0)]
R=sorted([(n,100*(p2*T2)/(p1*T1),a) for n,p1,p2,a in D],key=lambda r:r[1])
save_csv(SLUG+'.csv',['system','implied_pct_of_top_science_performers_expecting_stem','asia_pacific'],[(n,round(v,1),a) for n,v,a in R])
fig,ax=new_fig(h=8.0,left=0.24,right=0.96,bottom=0.12,top=0.98)
y=np.arange(len(R))
ax.barh(y,[v for n,v,a in R],color=[palette(2)[0] if a else palette(2)[1] for n,v,a in R],height=0.66,zorder=3)
for i,(n,v,a) in enumerate(R): ax.text(v+1.2,i,f'{v:.0f}%',va='center',fontsize=14,color=INK)
ax.axvline(100*T2/T1,color=INK,ls='--',lw=1.6,zorder=4)
ax.text(100*T2/T1+1,len(R)-0.2,'All participants: 55%',color=INK,fontsize=14,va='center')
ax.set_yticks(y); ax.set_yticklabels([n for n,v,a in R])
for t,(n,v,a) in zip(ax.get_yticklabels(),R):
    if a: t.set_color(palette(2)[0]); t.set_fontweight('bold')
ax.tick_params(axis='y',length=0); ax.set_xlim(0,100); ax.set_ylim(-0.7,len(R)+0.2)
ax.set_xlabel('Expect to work in a STEM occupation at age 30 (%)')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=palette(2)[0],label='Asia-Pacific'),Patch(color=palette(2)[1],label='Rest of world')],loc='upper center',bbox_to_anchor=(0.4,-0.13),ncol=2,frameon=False,fontsize=15)
compose(fig,'Only about a third of top science performers in B-S-J-Z expect a STEM career, half the US rate',
 'Implied share of students at Level 5 or 6 in science who expect a STEM-related occupation at age 30, PISA 2025',
 'OECD (2026), PISA 2025 Results (Volume I), Figure I.1.4; ratios derived by the author.',
 'Each ratio divides a system\'s share of the STEM-expecting pool by its share of the top-performer pool, both published to one decimal, so ratios for systems under 2% of the pool can be off by several points. Expectations are self-reported at 15 and are not career outcomes; non-response may be treated differently across systems.',
 SLUG+'.png')
