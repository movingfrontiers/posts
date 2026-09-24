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

SLUG='chart-5-fairness-vs-performance'
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
# system, % of science variance explained by socio-economic status, mean science score, Asian system flag (OECD PISA 2025, Tables I.1 and I.2)
DATA=[('Albania*', 8.7, 435.0, 0), ('Argentina', 11.8, 393.0, 0), ('Armenia', 4.3, 369.0, 0), ('Australia', 9.5, 509.0, 0), ('Austria', 14.0, 497.0, 0), ('Azerbaijan', 7.1, 409.0, 0), ('B-S-J-Z (China)', 9.7, 597.0, 1), ('Belgium', 14.6, 490.0, 0), ('Brazil', 15.9, 409.0, 0), ('Brunei Darussalam', 12.8, 439.0, 1), ('Bulgaria', 13.8, 421.0, 0), ('Cambodia', 0.5, 382.0, 1), ('Canada*', 6.0, 510.0, 0), ('Chile', 11.4, 442.0, 0), ('Chinese Taipei', 11.4, 540.0, 1), ('Colombia', 17.4, 414.0, 0), ('Croatia', 11.9, 476.0, 0), ('Cyprus', 6.6, 411.0, 0), ('Czechia', 15.0, 490.0, 0), ('Denmark', 9.6, 478.0, 0), ('Dominican Republic', 10.4, 361.0, 0), ('Dushanbe (Tajikistan)', 7.5, 334.0, 1), ('Ecuador', 20.4, 393.0, 0), ('El Salvador', 13.7, 385.0, 0), ('Estonia', 9.6, 527.0, 0), ('Finland', 9.0, 504.0, 0), ('France', 13.5, 483.0, 0), ('Georgia', 4.4, 422.0, 0), ('Germany', 19.0, 486.0, 0), ('Greece', 10.4, 434.0, 0), ('Guatemala', 17.1, 351.0, 0), ('Hong Kong (China)', 6.2, 496.0, 1), ('Hungary', 17.9, 480.0, 0), ('Iceland', 7.1, 441.0, 0), ('Indonesia', 8.6, 389.0, 1), ('Ireland', 9.6, 500.0, 0), ('Israel', 9.2, 442.0, 0), ('Italy', 11.3, 483.0, 0), ('Japan', 7.6, 538.0, 1), ('Jordan', 4.1, 407.0, 0), ('Kazakhstan', 4.6, 420.0, 1), ('Kenya', 0.2, 335.0, 0), ('Korea', 7.7, 526.0, 1), ('Kosovo', 4.8, 357.0, 0), ('Kurdistan Region (Iraq)', 1.5, 352.0, 0), ('Kyrgyzstan', 6.1, 363.0, 1), ('Latvia', 5.5, 468.0, 0), ('Lebanon', 7.7, 372.0, 0), ('Lithuania', 7.9, 488.0, 0), ('Luxembourg', 21.7, 474.0, 0), ('Macao (China)', 3.7, 541.0, 1), ('Malaysia', 15.7, 419.0, 1), ('Malta', 6.3, 453.0, 0), ('Mauritius', 12.5, 438.0, 0), ('Mexico', 11.9, 414.0, 0), ('Moldova', 13.4, 422.0, 0), ('Mongolia', 11.8, 424.0, 1), ('Montenegro', 8.2, 435.0, 0), ('Morocco', 9.1, 358.0, 0), ('Netherlands*', 13.9, 485.0, 0), ('New Zealand*', 11.1, 509.0, 0), ('North Macedonia', 6.8, 378.0, 0), ('Norway*', 8.2, 470.0, 0), ('Palestinian Authority', 5.4, 359.0, 0), ('Paraguay', 12.0, 355.0, 0), ('Peru', 13.7, 406.0, 0), ('Philippines', 12.9, 373.0, 1), ('Poland', 11.3, 495.0, 0), ('Portugal', 13.3, 482.0, 0), ('Qatar', 4.0, 434.0, 0), ('Romania', 21.7, 425.0, 0), ('Rwanda', 3.1, 317.0, 0), ('Saudi Arabia', 5.6, 413.0, 0), ('Serbia', 9.1, 429.0, 0), ('Singapore', 12.5, 560.0, 1), ('Slovak Republic', 20.7, 475.0, 0), ('Slovenia', 8.5, 484.0, 0), ('Spain', 9.2, 477.0, 0), ('Sweden', 12.0, 485.0, 0), ('Switzerland', 13.6, 501.0, 0), ('Thailand', 7.0, 432.0, 1), ('Türkiye', 10.4, 494.0, 0), ('Ukrainian regions (17 of 27)', 8.0, 448.0, 0), ('United Arab Emirates', 3.3, 458.0, 0), ('United Kingdom', 8.5, 511.0, 0), ('United States*', 11.0, 502.0, 0), ('Uruguay', 14.9, 445.0, 0), ('Uzbekistan', 1.3, 438.0, 1), ('Viet Nam', 17.5, 457.0, 1), ('Zambia', 37.8, 337.0, 0)]
O_STRENGTH,O_SCI=11.6,482.0
seven=['B-S-J-Z (China)','Canada*','Estonia','Ireland','Japan','Korea','Macao (China)']
save_csv(SLUG+'.csv',['system','escs_variance_pct','science_mean','asian_system','equitable_high_performer'],[(n.replace('*',''),v,m,a,int(n in seven)) for n,v,m,a in DATA])
DD={n:(v,m,a) for n,v,m,a in DATA}
fig,ax=new_fig(h=8.8,left=0.14,right=0.96,bottom=0.24,top=0.98)
ax.add_patch(Rectangle((0,O_SCI),10,640-O_SCI,color='#E8EAF6',lw=0,zorder=0))
ax.axvline(O_STRENGTH,color=INK,ls='--',lw=1.1,zorder=1); ax.axhline(O_SCI,color=INK,ls='--',lw=1.1,zorder=1); ax.axvline(10,color=INK,ls=':',lw=1.2,zorder=1)
P3=palette(3)
rest=[(v,m) for n,v,m,a in DATA if not a and n not in seven]; asia=[(v,m) for n,v,m,a in DATA if a and n not in seven]; sv=[DD[n][:2] for n in seven]
ax.scatter(*zip(*rest),s=44,color=P3[2],edgecolor='white',lw=0.5,zorder=2)
ax.scatter(*zip(*asia),s=70,color=P3[1],edgecolor='white',lw=0.6,zorder=3)
ax.scatter(*zip(*sv),s=130,color=P3[0],edgecolor='white',lw=0.9,zorder=4)
P={'B-S-J-Z (China)':(9.0,589,'left'),'Macao (China)':(3.7,556,'center'),'Japan':(8.3,546,'right'),'Korea':(7.0,521,'left'),'Canada*':(5.3,505,'left'),
'Estonia':(10.3,528,'right'),'Ireland':(10.3,500,'right'),'Singapore':(12.0,560,'left'),'Chinese Taipei':(12.0,540,'right'),'Hong Kong (China)':(5.5,491,'left'),
'Viet Nam':(16.8,457,'left'),'Malaysia':(15.0,419,'left'),'Thailand':(7.6,436,'right'),'Philippines':(12.2,373,'left'),'Indonesia':(9.3,393,'right'),'Cambodia':(1.2,389,'right'),'Uzbekistan':(1.9,442,'right')}
for n,(x,y,ha) in P.items():
    sev=n in seven; ax.text(x,y,n,ha=ha,va='center',fontsize=13,color=P3[0] if sev else P3[1],fontweight='bold' if sev else 'normal',zorder=6)
ax.set_xlim(22.5,-0.5); ax.set_ylim(310,625)
ax.set_xlabel('Science variance explained by socio-economic status (%)\n\u2190 birth matters more          birth matters less \u2192',labelpad=6)
ax.set_ylabel('Mean score in science')
ax.text(0.4,622,'Fairer and above\nOECD average',color=INK,fontsize=13,va='top',ha='right')
h=[Line2D([],[],marker='o',ls='',color=P3[0],ms=10,label='Fair and excellent (OECD)'),Line2D([],[],marker='o',ls='',color=P3[1],ms=9,label='Other Asian system'),
   Line2D([],[],marker='o',ls='',color=P3[2],ms=8,label='Rest of world'),Line2D([],[],color=INK,ls='--',lw=1.1,label='OECD average')]
ax.legend(handles=h,loc='upper center',bbox_to_anchor=(0.42,-0.19),ncol=2,frameon=False,fontsize=13.5,columnspacing=0.8,handletextpad=0.3)
compose(fig,'How much birth decides is a policy choice',
 'Science performance against the share of variance explained by socio-economic status, PISA 2025',
 'OECD (2026), PISA 2025 Results (Volume I), Tables I.1 and I.2.',
 "The OECD's fair-and-excellent classification also requires inclusion above 75% and above-average scores in all three subjects. Very low gradients in several low-scoring systems reflect uniformly weak results rather than fairness. Canada* did not meet all sampling standards. Zambia (37.8%, 337 points) lies outside the plotted range.",
 SLUG+'.png')
