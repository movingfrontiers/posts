"""India and Indonesia gained most from basic needs; rights and voice fell in all but Japan

Self-contained: embeds its data (also saved as chart-02-drivers-of-change-seven-economies.csv) and the Moving Frontiers house style.
Needs only numpy, pandas, matplotlib and Pillow. Run `python chart-02-drivers-of-change-seven-economies.py` to write chart-02-drivers-of-change-seven-economies.png in the current folder.
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

import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, warnings; warnings.filterwarnings('ignore')
from matplotlib.patches import Patch
plt.rcParams.update({'font.family':'DejaVu Sans','axes.edgecolor':'#888','axes.linewidth':1.0})
C=['USA', 'CHN', 'JPN', 'KOR', 'IND', 'IDN', 'BRA']
NM={'USA': 'United States', 'CHN': 'China', 'JPN': 'Japan', 'KOR': 'Rep. of Korea', 'IND': 'India', 'IDN': 'Indonesia', 'BRA': 'Brazil'}
S=a[a.spicountrycode.isin(C)].pivot(index='spiyear',columns='spicountrycode')
D=pd.DataFrame({k:(S[k].loc[2025,C]-S[k].loc[2011,C])/12 for k in COMP}).T     # contribution to the index change
G={'Rights and voice':['score_pr'],'Other opportunity':['score_pfc','score_incl','score_aae'],
   'Foundations of wellbeing':['score_abk','score_aic','score_hw','score_eq'],'Basic needs':['score_nbmc','score_ws','score_sh','score_ps']}
GC={'Rights and voice':'#C62828','Other opportunity':'#F9A825','Foundations of wellbeing':'#00897B','Basic needs':'#283593'}
GD=pd.DataFrame({g:D.loc[ks].sum() for g,ks in G.items()}); tot=GD.sum(axis=1)
assert np.allclose(tot,(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C]),atol=0.02); tot=(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C])   # label the published change
order=tot.sort_values(ascending=True).index; OFFX=0.04*((-4.8,12.6)[1]-(-4.8,12.6)[0])          # smallest fall at the bottom
W=H=1200; DPI=200
fig=plt.figure(figsize=(W/DPI,H/DPI),dpi=DPI); fig.patch.set_facecolor('white'); r=fig.canvas.get_renderer(); bb=lambda o:o.get_window_extent(r)
tt=fig.text(0.04,1-22/H,'India and Indonesia gained most from basic\nneeds; rights and voice fell in all but Japan',fontsize=14.5,fontweight='bold',color='#222',ha='left',va='top',linespacing=1.25); fig.canvas.draw()
st=fig.text(0.04,(bb(tt).y0-14)/H,'Contribution to the change in the Social Progress Index, 2011-2025 (points)',fontsize=9.6,color='#646464',ha='left',va='top'); fig.canvas.draw()
wm=fig.text(0.96,0,'movingfrontiers.substack.com',fontsize=7.7,color='#666',ha='right',va='bottom'); fig.canvas.draw(); wm.set_y((10-bb(wm).y0)/H); fig.canvas.draw()
ct=fig.text(0.04,0,'Source: Social Progress Imperative, 2026 Global Social Progress Index.\nNote: The index is the simple average of its 12 components, so each contributes its change divided by 12. Basic needs\nand foundations of wellbeing each group four components; other opportunity covers freedom and choice, inclusive\nsociety and advanced education.',
 fontsize=6.4,color='#666',ha='left',va='bottom',linespacing=1.35); fig.canvas.draw(); ct.set_y((bb(wm).y1+20-bb(ct).y0)/H); fig.canvas.draw()
ax=fig.add_axes([0.27,0.2,0.68,0.55]); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False)
for i,c in enumerate(order):
    pos=neg=0
    for g in G:
        v=GD.loc[c,g]
        if v>=0: ax.barh(i,v,left=pos,color=GC[g],height=.62,edgecolor='white',lw=.6); pos+=v
        else: ax.barh(i,v,left=neg,color=GC[g],height=.62,edgecolor='white',lw=.6); neg+=v
    ax.scatter(tot[c],i,marker='D',s=34,c='#141414',zorder=5,edgecolor='white',lw=.6)
    ax.text((min(neg,tot[c])-OFFX) if tot[c]<0 else (max(pos,tot[c])+OFFX),i,(f'{tot[c]:+.1f}' if tot[c]>0 else f'{tot[c]:.1f}').replace('-','−') if abs(tot[c])>=0.05 else f'{tot[c]:.2f}'.replace('-','−'),ha='right' if tot[c]<0 else 'left',va='center',fontsize=8.6,fontweight='bold',color='#141414')
ax.axvline(0,c='#444',lw=.9); ax.set_yticks(range(len(order))); ax.set_yticklabels([NM[c] for c in order],fontsize=9.5,color='#222'); ax.tick_params(axis='y',length=0)
ax.tick_params(axis='x',labelsize=9,colors='#444',length=3); ax.grid(axis='x',c='#eeeeee',lw=.8); ax.set_axisbelow(True)
ax.set_xlim(-4.8,12.6); ax.set_xticks([-4, -2, 0, 2, 4, 6, 8, 10, 12]); ax.set_xticklabels([str(v).replace('-','−') for v in [-4, -2, 0, 2, 4, 6, 8, 10, 12]])
ax.set_xlabel('Contribution to the change (points)',fontsize=9,color='#444')
h=[Patch(facecolor=GC[g],label=g) for g in G]+[plt.Line2D([],[],marker='D',ls='',c='#141414',ms=5.5,label='Net change')]
lg=fig.legend(handles=h,loc='upper left',ncol=3,frameon=False,fontsize=8.6,handlelength=1.2,columnspacing=1.2,bbox_to_anchor=(0.04,0.5))
# lay out: legend just above caption, axes between subtitle and legend
for _ in range(5):
    fig.canvas.draw(); lb=bb(lg); err=(bb(ct).y1+20)-lb.y0; ay=lg.get_bbox_to_anchor().transformed(fig.transFigure.inverted()).y0; lg.set_bbox_to_anchor((0.04,ay+err/H)); fig.canvas.draw(); lb=bb(lg)
    tb=ax.get_tightbbox(r); p=ax.get_position()
    y0=p.y0+(lb.y1+24-tb.y0)/H; y1=p.y1+(bb(st).y0-30-tb.y1)/H; ax.set_position([p.x0,y0,p.width,y1-y0])
fig.canvas.draw(); tb=ax.get_tightbbox(r); lb=bb(lg)
print('cap-wm',round(bb(ct).y0-bb(wm).y1,1),'wm-edge',round(bb(wm).y0,1)); print('gaps sub-plot',round(bb(st).y0-tb.y1,1),'plot-legend',round(tb.y0-lb.y1,1),'legend-cap',round(lb.y0-bb(ct).y1,1),'right',round(W-max(tb.x1,lb.x1,bb(st).x1)))
print({c:(GD.loc[c].idxmin(),round(GD.loc[c].min(),2)) for c in order}); print('rv share of gross losses',{c:round(-GD.loc[c,'Rights and voice']/-GD.loc[c][GD.loc[c]<0].sum(),2) for c in order})
fig.savefig('chart-02-drivers-of-change-seven-economies.png',dpi=DPI,facecolor='white')

