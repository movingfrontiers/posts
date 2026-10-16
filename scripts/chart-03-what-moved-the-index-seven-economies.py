"""What moved the index most in each economy

Self-contained: embeds its data (also saved as chart-03-what-moved-the-index-seven-economies.csv) and the Moving Frontiers house style.
Needs only numpy, pandas, matplotlib and Pillow. Run `python chart-03-what-moved-the-index-seven-economies.py` to write chart-03-what-moved-the-index-seven-economies.png in the current folder.
Data: Social Progress Imperative, 2026 Global Social Progress Index (ranked countries), frozen October 2026."""
DATA = """\
country,spicountrycode,spiyear,status,score_spi,score_nbmc,score_ws,score_sh,score_ps,score_abk,score_aic,score_hw,score_eq,score_pr,score_pfc,score_incl,score_aae,GDPpc,population
Brazil,BRA,2011,Ranked,68.01,85.74,77.8,82.35000000000001,61.09,64.82000000000001,57.13,57.56,69.87,71.35000000000001,76.78,68.19,43.46,18062.1581,193701929
Brazil,BRA,2025,Ranked,72.74,86.64,81.44,87.18,66.4,70.49,83.19,62.32,73.45,68.11,79.92,63.35,50.42,19647.909600000003,211998573
China,CHN,2011,Ranked,59.94,88.71000000000001,71.93,74.0,75.74,72.67,46.37,58.81,50.93,25.93,74.74,44.28,35.13,10476.3124,1337705000
China,CHN,2025,Ranked,68.82000000000001,92.58,79.18,88.43,84.14,73.08,79.45,64.18,55.6,25.13,72.86,52.620000000000005,58.64,23845.619700000003,1408975000
Indonesia,IDN,2011,Ranked,59.95,67.76,68.18,63.79,82.55,72.05,39.35,48.36,60.63,62.38,69.79,48.230000000000004,36.38,8848.2247,246305322
Indonesia,IDN,2025,Ranked,68.11,76.9,75.71000000000001,91.92,83.17,78.08,69.37,51.34,59.800000000000004,59.81,75.32000000000001,48.71,47.15,14470.4372,283487931
India,IND,2011,Ranked,51.300000000000004,56.5,49.84,50.660000000000004,74.35000000000001,54.64,43.99,46.92,43.61,64.43,56.19,41.38,33.12,5059.282700000001,1243481564
India,IND,2025,Ranked,58.79,70.08,66.47,76.37,76.34,68.0,63.36,48.95,38.56,52.39,63.9,43.56,37.480000000000004,9817.070800000001,1450935791
Japan,JPN,2011,Ranked,84.88,92.74,92.94,96.12,82.71000000000001,94.23,75.63,85.72,91.60000000000001,90.09,80.12,74.12,62.49,40881.7972,128070000
Japan,JPN,2025,Ranked,87.23,91.76,92.81,95.98,85.97,95.67,86.35000000000001,86.36,92.14,90.54,84.37,80.39,64.47,46097.43,123975371
"Korea, Republic of",KOR,2011,Ranked,82.12,93.7,91.88,93.66,76.69,85.77,88.41,78.77,83.08,80.21000000000001,75.84,63.88,73.57000000000001,37610.9729,49554112
"Korea, Republic of",KOR,2025,Ranked,85.14,94.10000000000001,93.05,92.71000000000001,84.79,89.56,91.62,83.83,84.0,78.03,80.65,71.28,78.08,50414.207,51751065
United States,USA,2011,Ranked,84.17,91.56,94.08,94.01,74.48,88.48,84.38,68.60000000000001,82.7,87.87,86.49,78.03,79.31,59789.4129,309378227
United States,USA,2025,Ranked,81.76,91.59,93.53,87.23,71.46000000000001,85.33,88.71000000000001,66.95,85.37,78.3,84.28,74.12,74.32000000000001,75491.6084,340110988
"""

# ---- data (embedded) and the few shared definitions the chart code expects ----
import io, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
a=pd.read_csv(io.StringIO(DATA))
COMP=['score_nbmc','score_ws','score_sh','score_ps','score_abk','score_aic','score_hw','score_eq','score_pr','score_pfc','score_incl','score_aae']
CN=['Nutrition and medical care','Water and sanitation','Housing','Safety','Basic education','Information and communications','Health','Environmental quality','Rights and voice','Freedom and choice','Inclusive society','Advanced education']
cn=dict(zip(COMP,CN))

"""Chart: the components that moved the index most in each of the seven economies, 2011-2025."""
import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, sys
"""Moving Frontiers house style (inlined), rebuilt to the saved spec: matplotlib draws the plot,
compose() lays out title, subtitle, caption and watermark in PIL with every gap measured
ink to ink, and verify() re-measures the gaps from the pixels."""
import numpy as np, os, matplotlib
from PIL import Image, ImageDraw, ImageFont
RED,GOLD,GREEN,BLUE,GREY='#C62828','#F9A825','#00897B','#283593','#888888'
GAP_TITLE_SUB,GAP_SUB_PLOT,GAP_PLOT_CAP,GAP_CAP_MARK,BORDER=25,70,60,20,70
REF_W=1980; MARK='movingfrontiers.substack.com'
def _font(name,px):
    for p in ['/usr/share/fonts/truetype/dejavu/'+name,os.path.join(matplotlib.get_data_path(),'fonts','ttf',name)]:
        if os.path.exists(p): return ImageFont.truetype(p,px)
    raise FileNotFoundError(name)
def _ink(im):
    a=np.array(im.convert('L')); ys,xs=np.where(a<250); return xs.min(),ys.min(),xs.max(),ys.max()
_tmp=ImageDraw.Draw(Image.new('RGB',(10,10)))
def _wrap(text,f,width):
    out=[]
    for para in text.split('\n'):
        cur=''
        for w in para.split():
            t=(cur+' '+w).strip()
            if (f.getbbox(t,anchor='la')[2]-f.getbbox(t,anchor='la')[0])<=width: cur=t
            else: out.append(cur); cur=w
        out.append(cur)
    return out
def _block(lines,f,ls):
    lh=round(f.size*ls); top=bot=None
    for i,ln in enumerate(lines):
        b=f.getbbox(ln,anchor='la'); t,bo=i*lh+b[1],i*lh+b[3]
        top=t if top is None else min(top,t); bot=bo if bot is None else max(bot,bo)
    return top,bot,lh
PLOT_W=1840
def compose(plot_png,out,title,subtitle,caption,mark=True):
    P=Image.open(plot_png).convert('RGB'); x0,y0,x1,y1=_ink(P); P=P.crop((x0,y0,x1+1,y1+1))
    if P.width>PLOT_W: P=P.resize((PLOT_W,round(P.height*PLOT_W/P.width)),Image.LANCZOS)
    elif P.width<PLOT_W:
        Q=Image.new('RGB',(PLOT_W,P.height),'white'); Q.paste(P,(0,0)); P=Q
    W=P.width+2*BORDER; sc=W/REF_W; BW=W-2*BORDER
    FT,FS,FC,FW=_font('DejaVuSans-Bold.ttf',round(61*sc)),_font('DejaVuSans.ttf',round(36*sc)),_font('DejaVuSans.ttf',round(25*sc)),_font('DejaVuSans.ttf',round(30*sc))
    y=BORDER; plan=[]
    for txt,f,col,ls,gap in ((title,FT,(45,45,45),1.22,GAP_TITLE_SUB),(subtitle,FS,(100,100,100),1.3,GAP_SUB_PLOT)):
        L=_wrap(txt,f,BW); top,bot,lh=_block(L,f,1.22 if f is FT else 1.3); plan.append((L,f,col,lh,y-top)); y+=bot-top+gap
    plot_y=y; y+=P.height+GAP_PLOT_CAP
    L=_wrap(caption,FC,BW); top,bot,lh=_block(L,FC,1.35); plan.append((L,FC,(102,102,102),lh,y-top)); cap_bot=y+bot-top
    wb=FW.getbbox(MARK,anchor='la')
    Hc=(cap_bot+GAP_CAP_MARK+(wb[3]-wb[1]) if mark else cap_bot)+BORDER
    C=Image.new('RGB',(W,Hc),'white'); C.paste(P,(BORDER,plot_y)); dr=ImageDraw.Draw(C)
    for L,f,col,lh,yy in plan:
        for i,ln in enumerate(L): dr.text((BORDER-f.getbbox(ln,anchor='la')[0],yy+i*lh),ln,font=f,fill=col,anchor='la')   # ink, not the pen, starts at the border
    if mark: dr.text((W-BORDER-wb[2],cap_bot+GAP_CAP_MARK-wb[1]),MARK,font=FW,fill=(102,102,102),anchor='la')
    C.save(out,optimize=True); verify(C,plot_y,P.height,W,Hc); return C.size
def verify(C,pt,ph,W,Hc):
    A=np.array(C.convert('L'))<250; rows=np.where(A.any(axis=1))[0]; cols=np.where(A.any(axis=0))[0]
    runs=np.split(rows,np.where(np.diff(rows)>1)[0]+1); pb=pt+ph-1
    assert rows.min()==BORDER and Hc-1-rows.max()==BORDER and cols.min()==BORDER and W-1-cols.max()>=BORDER-1, ('border off',rows.min(),Hc-1-rows.max(),cols.min(),W-1-cols.max())
    sub_bot=max(r[-1] for r in runs if r[-1]<pt); cap_top=min(r[0] for r in runs if r[0]>pb)
    assert pt-sub_bot-1==GAP_SUB_PLOT and cap_top-pb-1==GAP_PLOT_CAP, (pt-sub_bot-1,cap_top-pb-1)

plt.rcParams.update({'font.family':'DejaVu Sans','axes.edgecolor':'#888','axes.linewidth':1.0,'figure.facecolor':'white','axes.facecolor':'white'})
a=a[a.status=='Ranked']
CN={'score_nbmc':'Nutrition and basic medical care','score_ws':'Water and sanitation','score_sh':'Shelter','score_ps':'Personal safety','score_abk':'Access to basic knowledge','score_aic':'Information and communications','score_hw':'Health and wellness','score_eq':'Environmental quality','score_pr':'Rights and voice','score_pfc':'Personal freedom and choice','score_incl':'Inclusiveness','score_aae':'Access to advanced education'}
p=a.pivot(index='spiyear',columns='spicountrycode',values=list(CN)+['score_spi']).astype(float); d=(p.loc[2025]-p.loc[2011]).unstack(0)
ORDER=[('CHN','China'),('IDN','Indonesia'),('IND','India'),('BRA','Brazil'),('JPN','Japan'),('KOR','Rep. of Korea'),('USA','United States')]
rows=[]   # (y, label, value, colour, is_header)
y=0; GAP=1.1
for c,nm in ORDER:
    s=d.loc[c,list(CN)]; top=s.abs().sort_values(ascending=False).head(3).index.tolist()
    sign=np.sign(s[top].sum()); opp=s[s*sign<0]
    if len(opp): top.append(opp.abs().idxmax())
    top=sorted(top,key=lambda k:-s[k])
    rows.append((y,f'{nm}  ({d.loc[c,"score_spi"]:+.1f} on the index)',None,None,True)); y+=1
    for k in top: rows.append((y,CN[k],s[k],GREEN if s[k]>=0 else RED,False)); y+=1
    y+=GAP-1
DPI=200; PW=1840
fig=plt.figure(figsize=(PW/DPI,2400/DPI),dpi=DPI); ax=fig.add_axes([0.36,0.05,0.62,0.94])
for sp in ('top','right','left'): ax.spines[sp].set_visible(False)
ax.axvline(0,c='#888',lw=1)
for yy,lab,v,col,hdr in rows:
    if hdr: ax.text(-0.50,yy,lab,transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=12,fontweight='bold',color='#222')
    else:
        ax.barh(yy,v,height=0.68,color=col,zorder=3)
        ax.text(-0.012,yy,lab,transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=11,color='#444')
        ax.text(v+(0.5 if v>=0 else -0.5),yy,f'{v:+.1f}',ha='left' if v>=0 else 'right',va='center',fontsize=10.5,color=col,fontweight='bold')
ax.set_ylim(y-GAP+0.4,-0.7); ax.set_yticks([])
ax.set_xlim(-19,37); ax.set_xticks([-10,0,10,20,30]); ax.tick_params(labelsize=11,colors='#444',length=4)
ax.grid(axis='x',c='#eeeeee',lw=.8); ax.set_axisbelow(True)
ax.set_xlabel('Change in component score, 2011 to 2025 (points, 0-100 scale)',fontsize=12.5,color='#444',labelpad=8)
fig.savefig('_top3_plot.png',dpi=DPI,facecolor='white',bbox_inches='tight',pad_inches=0.05)
TITLE='What moved the index most in each economy'
SUB='The three components with the largest change between 2011 and 2025, plus the largest move in the opposite direction, for the seven economies'
CAP=('Source: Social Progress Imperative, 2026 Global Social Progress Index. '
     'Note: The index is a simple average of twelve components, so each component change shown here moves the headline index by one twelfth of its value. '
     'Components are selected by the size of their change in either direction; the fourth bar in each group is the largest change of the opposite sign.')
out='chart-03-what-moved-the-index-seven-economies.png'
print(compose('_top3_plot.png',out,TITLE,SUB,CAP))

