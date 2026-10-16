"""Rights and voice fell in all ten countries with the weakest change since 2011

Self-contained: embeds its data (also saved as chart-09-ten-weakest-changes-drivers.csv) and the Moving Frontiers house style.
Needs only numpy, pandas, matplotlib and Pillow. Run `python chart-09-ten-weakest-changes-drivers.py` to write chart-09-ten-weakest-changes-drivers.png in the current folder.
Data: Social Progress Imperative, 2026 Global Social Progress Index (ranked countries), frozen October 2026."""
DATA = """\
country,spicountrycode,spiyear,status,score_spi,score_nbmc,score_ws,score_sh,score_ps,score_abk,score_aic,score_hw,score_eq,score_pr,score_pfc,score_incl,score_aae,GDPpc,population
Afghanistan,AFG,2011,Ranked,36.64,45.61,42.4,26.68,62.36,27.5,34.83,35.22,45.26,38.53,43.480000000000004,25.830000000000002,12.02,2848.5861,28284089
Afghanistan,AFG,2025,Ranked,33.43,53.09,45.47,46.87,66.76,22.490000000000002,27.66,35.93,45.67,6.57,30.29,7.38,13.01,1983.8126000000002,42647492
Central African Republic,CAF,2011,Ranked,29.61,22.39,19.18,17.22,47.15,31.18,23.44,31.6,60.34,35.15,28.92,29.89,8.81,1479.4137,4492995
Central African Republic,CAF,2025,Ranked,28.78,32.62,19.46,18.77,47.63,31.62,27.64,26.6,57.480000000000004,19.86,28.39,27.310000000000002,7.95,1111.6533,5330690
Canada,CAN,2011,Ranked,85.86,93.37,95.07000000000001,93.38,81.02,93.97,78.5,78.67,81.78,88.47,91.01,81.41,73.66,52558.440800000004,34005902
Canada,CAN,2025,Ranked,85.11,93.03,94.9,84.91,79.89,91.5,85.94,76.5,83.63,79.45,89.22,84.31,77.99,56691.907,41288599
United Kingdom,GBR,2011,Ranked,85.3,90.98,97.35000000000001,92.81,80.13,93.62,83.95,76.72,86.65,89.13,86.82000000000001,75.69,69.68,47013.8824,62766365
United Kingdom,GBR,2025,Ranked,85.54,91.28,94.4,88.7,81.79,91.77,91.13,74.56,90.98,82.54,87.74,73.88,77.78,52517.9849,69226000
Lebanon,LBN,2011,Ranked,65.24,87.9,70.66,86.08,79.72,62.65,53.870000000000005,64.9,67.28,57.13,66.92,39.02,46.74,17390.758400000002,5041288
Lebanon,LBN,2025,Ranked,65.22,85.36,76.18,84.23,78.05,58.17,68.41,63.43,67.05,44.22,63.7,37.17,56.660000000000004,11330.268600000001,5805962
New Zealand,NZL,2011,Ranked,84.97,91.91,93.75,93.24,72.93,91.51,81.32000000000001,76.34,81.53,93.31,86.65,80.46000000000001,76.73,41270.9285,4350700
New Zealand,NZL,2025,Ranked,85.46000000000001,91.97,92.99,86.59,73.21000000000001,89.67,92.60000000000001,78.29,83.52,91.5,83.98,84.35000000000001,76.83,48162.8611,5338500
South Sudan,SSD,2011,Ranked,28.68,45.230000000000004,19.93,22.07,44.93,33.53,14.44,30.71,65.06,19.31,21.61,23.8,3.6,,9745953
South Sudan,SSD,2025,Ranked,27.71,47.94,20.18,17.3,36.22,31.61,21.79,28.0,65.87,12.35,23.42,22.14,5.71,,11943408
Syria,SYR,2011,Ranked,52.870000000000005,82.65,73.35000000000001,86.21000000000001,78.27,65.16,27.53,50.230000000000004,34.26,22.57,57.85,35.33,21.07,9546.5605,22482421
Syria,SYR,2025,Ranked,48.620000000000005,70.54,69.84,78.62,66.87,47.410000000000004,40.14,48.620000000000005,43.82,13.200000000000001,55.0,12.3,37.1,4189.8374,24672760
United States,USA,2011,Ranked,84.17,91.56,94.08,94.01,74.48,88.48,84.38,68.60000000000001,82.7,87.87,86.49,78.03,79.31,59789.4129,309378227
United States,USA,2025,Ranked,81.76,91.59,93.53,87.23,71.46000000000001,85.33,88.71000000000001,66.95,85.37,78.3,84.28,74.12,74.32000000000001,75491.6084,340110988
Venezuela,VEN,2011,Ranked,62.04,84.21000000000001,77.93,84.68,53.88,70.04,51.74,61.63,57.61,48.14,66.41,60.88,27.39,,28813101
Venezuela,VEN,2025,Ranked,57.32,76.8,70.13,83.24,62.160000000000004,67.79,55.44,50.13,53.0,18.080000000000002,64.13,55.49,31.41,,28405543
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
C=['VEN', 'SYR', 'AFG', 'USA', 'SSD', 'CAF', 'CAN', 'LBN', 'GBR', 'NZL']
NM={'VEN': 'Venezuela', 'SYR': 'Syria', 'AFG': 'Afghanistan', 'USA': 'United States', 'SSD': 'South Sudan', 'CAF': 'Central African Rep.', 'CAN': 'Canada', 'LBN': 'Lebanon', 'GBR': 'United Kingdom', 'NZL': 'New Zealand'}
S=a[a.spicountrycode.isin(C)].pivot(index='spiyear',columns='spicountrycode')
D=pd.DataFrame({k:(S[k].loc[2025,C]-S[k].loc[2011,C])/12 for k in COMP}).T     # contribution to the index change
G={'Rights and voice':['score_pr'],'Other opportunity':['score_pfc','score_incl','score_aae'],
   'Foundations of wellbeing':['score_abk','score_aic','score_hw','score_eq'],'Basic needs':['score_nbmc','score_ws','score_sh','score_ps']}
GC={'Rights and voice':'#C62828','Other opportunity':'#F9A825','Foundations of wellbeing':'#00897B','Basic needs':'#283593'}
GD=pd.DataFrame({g:D.loc[ks].sum() for g,ks in G.items()}); tot=GD.sum(axis=1)
assert np.allclose(tot,(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C]),atol=0.02); tot=(S.score_spi.loc[2025,C]-S.score_spi.loc[2011,C])   # label the published change
order=tot.sort_values(ascending=False).index; OFFX=0.04*((-8.2,4.2)[1]-(-8.2,4.2)[0])          # smallest fall at the bottom
W=H=1200; DPI=200
fig=plt.figure(figsize=(W/DPI,H/DPI),dpi=DPI); fig.patch.set_facecolor('white'); r=fig.canvas.get_renderer(); bb=lambda o:o.get_window_extent(r)
tt=fig.text(0.04,1-22/H,'Rights and voice fell in all ten countries\nwith the weakest change since 2011',fontsize=14.5,fontweight='bold',color='#222',ha='left',va='top',linespacing=1.25); fig.canvas.draw()
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
ax.set_xlim(-8.2,4.2); ax.set_xticks([-8, -6, -4, -2, 0, 2, 4]); ax.set_xticklabels([str(v).replace('-','−') for v in [-8, -6, -4, -2, 0, 2, 4]])
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
fig.savefig('chart-09-ten-weakest-changes-drivers.png',dpi=DPI,facecolor='white')

