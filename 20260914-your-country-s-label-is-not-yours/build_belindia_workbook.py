"""Build belindia_replication.xlsx: live 2025 engine plus every result as values."""
import pandas as pd, numpy as np, pickle, os, json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter as L
RUN='run2'
GRP=['L','LM','UM','H']; GL={'L':'Low income','LM':'Lower-middle income','UM':'Upper-middle income','H':'High income'}
LO,HI,STEP,BW,EPS=np.log(0.1),np.log(2000.0),0.05,0.2,1e-3
GRID=np.arange(0,int(round((HI-LO)/STEP))+1)*STEP+LO; NGE=len(GRID); NC=NGE-1; KMAX=40
D=pickle.load(open('typ_data.pkl','rb')); E=D['E']; W25=D['W'][2025]
inp=json.load(open('repl/inputs.json'))
codes=sorted(inp, key=lambda c: (inp[c]['reg'], inp[c]['sub'], inp[c]['name']))
N=len(codes); R0=5; R1=R0+N-1
pop=pd.read_pickle('typ_data.pkl')['E']
OUT='/home/claude/belindia_workbook.xlsx'
wb=Workbook(); wb.remove(wb.active)
A=lambda **k: Font(name='Calibri', size=k.pop('size',11), **k)
TITLE,BOLD,NORM,BLUE,ITAL,GREEN=A(size=13,bold=True),A(bold=True),A(),A(color='FF0000FF'),A(italic=True,color='FF555555'),A(color='FF008000')
YEL=PatternFill('solid',fgColor='FFFFF6CC')
def put(ws,ref,v,font=NORM,fmt=None,fill=None):
    c=ws[ref]; c.value=v; c.font=font
    if fmt: c.number_format=fmt
    if fill: c.fill=fill
    return c
def text_sheet(name,title,lines,width=130):
    ws=wb.create_sheet(name); put(ws,'A1',title,TITLE)
    for i,t in enumerate(lines,3):
        c=put(ws,f'A{i}',t,BOLD if (t.isupper() and t.strip()) else NORM); c.alignment=Alignment(wrap_text=True,vertical='top')
    ws.column_dimensions['A'].width=width; return ws
def frame(name,title,note,df,index=False,fmts=None,width=28):
    ws=wb.create_sheet(name[:31]); put(ws,'A1',title,TITLE); put(ws,'A2',note,ITAL)
    fmts=fmts or {}
    cols=([df.index.name or 'code'] if index else [])+[str(c) for c in df.columns]
    for j,h in enumerate(cols,1): put(ws,f'{L(j)}4',h,BOLD)
    for i,(ix,row) in enumerate(df.iterrows(),5):
        vals=([ix] if index else [])+list(row.values)
        for j,v in enumerate(vals,1):
            if isinstance(v,(np.floating,np.integer)): v=v.item()
            if isinstance(v,float) and np.isnan(v): v=None
            c=ws.cell(i,j,v); c.font=NORM
            key=cols[j-1]
            if fmts.get(key): c.number_format=fmts[key]
    ws.freeze_panes='A5'; ws.column_dimensions['A'].width=width
    return ws

# ---------------- Read me / method / limitations ----------------
text_sheet('Read me','Belindia replication workbook: Your Country\'s Label Is Not Yours',[
 'WHAT THIS WORKBOOK IS',
 'The complete data and results behind Moving Frontiers Post 6 (September 2026). Nothing here refers to an external file. This workbook is built by build_belindia_workbook.py from the output of belindia_replication.py, so it can be rebuilt from the World Bank 1000-bin file alone. The 2025 engine is live: change the bandwidth on "Assumptions" and the curves, the typicality lines, every economy\'s shares and the Belindia matrix all recompute from the distributions on "Bins 2025". Every other result is a value produced by belindia_replication.py, which uses the identical method and can be re-run from the World Bank\'s 1000-bin file alone.',
 '',
 'THE QUESTION',
 'The World Bank sorts countries into four income groups on GNI per capita, an average that says nothing about how income is shared. This workbook asks how many people inside each group actually live at a standard typical of that group, and how many live at a standard typical of a poorer or a richer one.',
 '',
 'THE METHOD IN ONE PARAGRAPH',
 'Pool the people of all low-income countries and draw the curve of their daily welfare on a log scale. Do the same for the lower-middle, upper-middle and high-income groups. Each curve is scaled to the same area, so the groups are compared on shape and not on size. Where the low-income curve stops being the highest and the lower-middle curve takes over is the first typicality line; two more follow. A person is then assigned to the group whose curve is highest at their welfare, which is the standard they live at, and that is compared with the group their country belongs to.',
 '',
 'HEADLINE (2025, 218 countries, 8.21 billion people)',
 'Lines: $3.80, $9.21 and $26.86 per person per day, 2021 PPP.',
 'The label describes the living standard of 61% of humanity. 22% live poorer than their label, 17% richer.',
 '1990: the label fitted 70% of people against today\'s standards. It fell to 48% by 2010 as India and China crossed thresholds, and recovered to 61%.',
 '2026 nowcast: China joins the high-income group. Against 2025 standards the fit drops to 54%, almost entirely through relabelling.',
 '',
 'SHEETS',
 'Assumptions: the two live inputs. Inputs: every country, its published income group for each year 1990-2026, survey type, 2025 Atlas GNI, UN region.',
 'Bins 2025: the 1000 sorted bins per country. CDF grid 2025, Curves 2025, Engine 2025, Matrix 2025: the live calculation.',
 'Matrices: the matrix for 1990, 2025 and 2026 on both own and fixed lines. Shares: the same as percentages of each group.',
 'History 1990-2026, Skewness, World distribution, Group curves: the series behind the charts.',
 'Check smoothing, Check giants, Check missing rich, Check yardsticks, Check survey type: Annex 1 robustness.',
 'Inequality decomposition, Off-diagonal sources, Threshold translation, Rho by economy: the rest of Annex 1.',
 'Country results: Annex 2, every country by UN region.',
 '',
 'COLOUR CONVENTION',
 'Blue on a yellow fill: a live input you may change. Black: a formula or a value. Green: a check cell that should read zero.'])

text_sheet('Method','Method, step by step, and where each step lives in this workbook',[
 'INPUTS',
 '"Bins 2025" holds 1,000 sorted bin means per country in 2021 PPP dollars a day, each bin covering a tenth of a percent of that country\'s population. "Inputs" holds the published income group for every year from 1990 to 2026, taken from the World Bank\'s OGHIST lists and never recomputed from GNI, so Argentina and Turkiye stay upper-middle income in 2025. The 2026 groups are the projection of the Great Income Inversion post, in which China crosses the high-income threshold. All 218 classified countries are counted; the 46 without a household survey carry distributions imputed by the Bank and are marked n.',
 '',
 'STEP A. Share of each country below each grid edge ("CDF grid 2025")',
 'A log grid of 199 edges from $0.10 to $2,000 a day in steps of 0.05, about five percent of welfare per cell. For country i and edge x the share is MATCH(x, bins_i, 1) / 1000.',
 '',
 'STEP B. Group curves ("Curves 2025", columns D to G)',
 'For group c and cell j the raw density is the population-weighted share of the group\'s people in that cell, divided by the cell width in log welfare, so each curve integrates to one.',
 '',
 'STEP C. Smoothing ("Curves 2025", columns I to L; weights in AA to AC)',
 'A Gaussian kernel of bandwidth b, set on "Assumptions", truncated at five bandwidths and normalised. The table is padded with zero rows so every cell uses the same fixed-length window.',
 '',
 'STEP D. Most typical group ("Curves 2025", column N)',
 'In each cell, the group whose smoothed curve is highest, provided the highest curve exceeds the density floor on "Assumptions".',
 '',
 'STEP E. The lines ("Curves 2025", block "Peaks and lines")',
 'Line k is the first cell at or beyond the peak of group k where the most typical group is k+1 or higher. Within that cell the crossing is placed by linear interpolation on the difference between the two curves involved. Starting the search at the peak keeps the bottom-coded tails, which the Bank floors at $0.28 a day, from producing spurious crossings.',
 '',
 'STEP F. Shares at each standard ("Engine 2025")',
 'The share of country i below line z is m = MATCH(z, bins_i, 1); share = (m - 0.5 + (z - bin_m) / (bin_m+1 - bin_m)) / 1000, which interpolates linearly between bin means. The four standards are the gaps between the three lines.',
 '',
 'STEP G. The matrix ("Matrix 2025")',
 'People at each standard are the shares times population, summed by the country\'s own income group. The diagonal is the population whose label fits, the cells below it are people living poorer than their label and those above it people living richer.',
 '',
 'STEP H. Everything else (belindia_replication.py)',
 'The same seven steps are repeated for every year from 1990 to 2026, for the robustness variants, for the counterfactual distributions and for the threshold-translation alternative. Those results are carried here as values; the 2025 row of each reconciles with the live sheets.'])

text_sheet('Limitations','What this measure does and does not support',[
 '1. Typical means typical of whoever is in the group. The lower-middle curve is largely India and the upper-middle curve largely China. Excluding both from the estimation moves the middle line from $9.21 to $7.96 and the fit from 61.0% to 60.0% ("Check giants").',
 '2. Lined up, not surveyed. The 2025 and 2026 distributions are each country\'s latest survey moved with national-accounts growth, at 70 percent passthrough for consumption surveys and full passthrough for income surveys. Inequality within a country is frozen between surveys.',
 '3. Income and consumption are mixed. Latin America and nearly all high-income countries report income, most of Asia and Africa consumption. Income is more dispersed at the same living standard, so income-measured countries look more Belindian at both ends ("Check survey type").',
 '4. The missing rich. Surveys undercount the top. Because all three lines sit well below the top decile of every group, doubling the top decile moves the fit by 0.3 points and adds only to the richer-than-label count ("Check missing rich").',
 '5. Imputed distributions. 46 countries have no PIP survey; their bins are World Bank imputations and are marked n. They are counted but never used to estimate the lines. North Korea is the clearest case where the imputation and the classification disagree.',
 '6. Coverage in 1990. 43 countries, about 6 percent of the bins population, were not yet classified and enter the history only from the year they appear on the list.',
 '7. Bottom coding. Welfare below $0.28 a day is set to $0.28, which is why the search for each line starts at the peak of the lower group.',
 '8. Within-country inequality is understated throughout, because each bin is the mean of a tenth of a percent of a population and the variation inside a bin is lost.',
 '9. 2026 is a nowcast: PIP\'s 2026 line-up for the distributions and a projection for the groups.'])

# ---------------- Assumptions ----------------
AS=wb.create_sheet('Assumptions')
put(AS,'A1','Assumptions. Blue cells on yellow are live; everything downstream recomputes.',TITLE)
for j,h in enumerate(['Parameter','Value','What it does'],1): put(AS,f'{L(j)}3',h,BOLD)
put(AS,'A4','Kernel bandwidth (log units)'); put(AS,'B4',BW,BLUE,'0.00',YEL)
put(AS,'C4','Smoothing of each group curve. 0.2 is about 20 percent of welfare. The lines move by under 4 percent for any value between 0.05 and 0.4 (see "Check smoothing").')
put(AS,'A5','Density floor for a cell to count'); put(AS,'B5',EPS,BLUE,'0.000',YEL)
put(AS,'C5','A cell enters the search for the most typical group only if some curve exceeds this, which keeps near-empty tails out.')
put(AS,'A6','Grid: lowest edge, $ a day'); put(AS,'B6',0.1,NORM,'0.00'); put(AS,'C6','Fixed; change only together with the grid on "CDF grid 2025".')
put(AS,'A7','Grid: highest edge, $ a day'); put(AS,'B7',2000,NORM,'0'); put(AS,'C7','As above.')
put(AS,'A8','Grid step (log units)'); put(AS,'B8',STEP,NORM,'0.00'); put(AS,'C8','As above. 199 edges, 198 cells.')
put(AS,'A9','Kernel half-width (cells)'); put(AS,'B9',KMAX,NORM,'0'); put(AS,'C9','Fixed length of the weight vector; weights beyond five bandwidths are zero, so any bandwidth up to 0.4 is exact.')
AS.column_dimensions['A'].width=34; AS.column_dimensions['B'].width=10; AS.column_dimensions['C'].width=110
BWr,EPSr,LOr,STEPr='Assumptions!$B$4','Assumptions!$B$5','Assumptions!$B$6','Assumptions!$B$8'

# ---------------- Inputs ----------------
IN=wb.create_sheet('Inputs')
put(IN,'A1','Countries: published income group each year, survey type, 2025 Atlas GNI, UN region, population',TITLE)
put(IN,'A2','Income groups from the World Bank OGHIST lists; 2026 is the Great Income Inversion projection. Survey: c consumption, i income, n no survey (imputed bins). Population is the sum of the 1000 bins, in millions. Blank group means the country was not classified that year.',ITAL)
hdr=['Economy','Code','UN region','UN subregion','Survey','GNI per capita 2025 (Atlas US$)','Pop 1990 (m)','Pop 2025 (m)','Pop 2026 (m)','Group 1990','Group 2025','Group 2026']+[str(y) for y in range(1990,2027)]
for j,h in enumerate(hdr,1): put(IN,f'{L(j)}4',h,BOLD)
CH={'L':'L','M':'LM','U':'UM','H':'H'}
for i,c in enumerate(codes):
    r=R0+i; v=inp[c]; seq=v['cls']
    IN.cell(r,1,v['name']); IN.cell(r,2,c); IN.cell(r,3,v['reg']); IN.cell(r,4,v['sub']); IN.cell(r,5,v['survey'])
    IN.cell(r,6,v['gni']).number_format='#,##0'
    for j,y in enumerate([1990,2025,2026]):
        p=E.loc[c,f'pop{y}']; IN.cell(r,7+j, None if pd.isna(p) else round(float(p),3)).number_format='#,##0.0'
        IN.cell(r,10+j, CH.get(seq[[1990,2025,2026].index(y) if False else (y-1990)],''))
    for j,y in enumerate(range(1990,2027)): IN.cell(r,13+j, CH.get(seq[j],''))
IN.freeze_panes='C5'; IN.column_dimensions['A'].width=30; IN.column_dimensions['D'].width=24; IN.column_dimensions['F'].width=14
CLS25='K'; POP25='H'

# ---------------- Bins 2025 ----------------
B=wb.create_sheet('Bins 2025')
put(B,'A1','Lined-up distributions, 2025: 1,000 bins per country, mean daily welfare of each tenth of a percent of the population (2021 PPP $)',TITLE)
put(B,'A2','World Bank 1000 Binned Global Distribution, PIP March 2026 vintage. Rows sorted ascending; bin q holds the people between percentile (q-1)/10 and q/10. Column C is the median, the average of bins 500 and 501.',ITAL)
put(B,'A4','Economy',BOLD); put(B,'B4','Code',BOLD); put(B,'C4','Median',BOLD)
for q in range(1,1001): B.cell(4,3+q,q)
for i,c in enumerate(codes):
    r=R0+i; B.cell(r,1,inp[c]['name']); B.cell(r,2,c)
    w=W25.loc[c].values
    if np.isnan(w).all(): continue
    B.cell(r,3,f'=AVERAGE(SI{r},SJ{r})').number_format='0.00'
    for q in range(1000): B.cell(r,4+q,round(float(w[q]),5))
B.freeze_panes='D5'; B.column_dimensions['A'].width=26
ROW=lambda r: f"'Bins 2025'!$D{r}:$ALO{r}"

# ---------------- CDF grid ----------------
G=wb.create_sheet('CDF grid 2025')
put(G,'A1','Share of each country\'s people at or below each grid edge, 2025 (live)',TITLE)
put(G,'A2','Row 3 is the edge in dollars a day, row 4 its logarithm. Each cell counts the bins at or below the edge and divides by 1,000.',ITAL)
put(G,'A3','$ a day',BOLD); put(G,'A4','log edge',BOLD); put(G,'B4','Code',BOLD); put(G,'C4','Group',BOLD); put(G,'D4','Pop (m)',BOLD)
for j in range(NGE):
    col=L(5+j); put(G,f'{col}4',f'=LN({LOr})+{j}*{STEPr}',NORM,'0.000'); put(G,f'{col}3',f'=EXP({col}4)',NORM,'0.00')
for i,c in enumerate(codes):
    r=R0+i; G.cell(r,2,f'=Inputs!B{r}'); G.cell(r,3,f'=Inputs!{CLS25}{r}'); G.cell(r,4,f'=N(Inputs!{POP25}{r})')
    if np.isnan(W25.loc[c].values).all(): continue
    for j in range(NGE):
        col=L(5+j); G[f'{col}{r}']=f'=IFERROR(MATCH({col}$3,{ROW(r)},1),0)/1000'
G.freeze_panes='E5'

# ---------------- Curves and lines ----------------
C=wb.create_sheet('Curves 2025')
put(C,'A1','Group curves, the most typical group and the typicality lines, 2025 (live)',TITLE)
put(C,'A2','Raw density of a group in a cell is the population-weighted share of the group\'s people in that cell divided by the cell width, so each curve integrates to one. Smoothed applies the Gaussian weights in columns AA to AC. The most typical group is the highest smoothed curve where some curve exceeds the density floor. Line k is the first cell at or beyond the peak of group k where the most typical group is k+1 or higher, interpolated on the difference between the two curves.',ITAL)
put(C,'AA3','Kernel weights',BOLD); put(C,'AA4','offset (cells)',BOLD); put(C,'AB4','raw',BOLD); put(C,'AC4','normalised',BOLD)
KR0=5
for k in range(-KMAX,KMAX+1):
    r=KR0+k+KMAX; put(C,f'AA{r}',k)
    put(C,f'AB{r}',f'=IF(ABS(AA{r})<=CEILING(5*{BWr}/{STEPr},1),EXP(-0.5*(AA{r}*{STEPr}/{BWr})^2),0)',NORM,'0.0000')
    put(C,f'AC{r}',f'=AB{r}/SUM($AB${KR0}:$AB${KR0+2*KMAX})',NORM,'0.0000')
WTS=f'$AC${KR0}:$AC${KR0+2*KMAX}'
hd=['cell','log mid','$ mid','raw L','raw LM','raw UM','raw H','','smooth L','smooth LM','smooth UM','smooth H','max','most typical (1-4)','flag 1','flag 2','flag 3']
HR=5; TOP=HR+1+KMAX
for j,h in enumerate(hd,1): put(C,f'{L(j)}{HR}',h,BOLD)
put(C,f'H{HR-1}','(rows above and below the table are zero padding for the smoothing window)',ITAL)
for pr in list(range(HR+1,TOP))+list(range(TOP+NC,TOP+NC+KMAX)):
    for col in 'DEFG': C[f'{col}{pr}']=0
popr=f"'CDF grid 2025'!$D${R0}:$D${R1}"; clsr=f"'CDF grid 2025'!$C${R0}:$C${R1}"
for j in range(NC):
    r=TOP+j; e0=L(5+j); e1=L(6+j)
    put(C,f'A{r}',j+1); put(C,f'B{r}',f"=('CDF grid 2025'!{e0}$4+'CDF grid 2025'!{e1}$4)/2",NORM,'0.000'); put(C,f'C{r}',f'=EXP(B{r})',NORM,'0.00')
    for k,g in enumerate(GRP):
        col=L(4+k); r0=f"'CDF grid 2025'!{e0}${R0}:{e0}${R1}"; r1=f"'CDF grid 2025'!{e1}${R0}:{e1}${R1}"
        put(C,f'{col}{r}',f'=IFERROR(SUMPRODUCT(({clsr}="{g}")*{popr}*({r1}-{r0}))/SUMPRODUCT(({clsr}="{g}")*{popr})/{STEPr},0)',NORM,'0.0000')
        s=L(9+k); put(C,f'{s}{r}',f'=SUMPRODUCT({WTS},{col}{r-KMAX}:{col}{r+KMAX})',NORM,'0.0000')
    put(C,f'M{r}',f'=MAX(I{r}:L{r})',NORM,'0.0000')
    put(C,f'N{r}',f'=IF(M{r}>{EPSr},MATCH(M{r},I{r}:L{r},0),0)')
S0,S1=TOP,TOP+NC-1; PB=TOP+NC+KMAX+2
put(C,f'A{PB}','PEAKS AND LINES',BOLD); put(C,f'A{PB+1}','Peak cell of group',BOLD)
for k,g in enumerate(GRP):
    put(C,f'{L(2+k)}{PB+1}',g,BOLD); s=L(9+k)
    put(C,f'{L(2+k)}{PB+2}',f'=MATCH(MAX({s}{S0}:{s}{S1}),{s}{S0}:{s}{S1},0)')
for k in range(1,4):
    f=L(14+k)
    for j in range(NC):
        r=TOP+j; C[f'{f}{r}']=f'=(A{r}>=${L(1+k)}${PB+2})*(N{r}>={k+1})'
for j,h in enumerate(['Line','Between','first cell','group before','group at','d0','d1','t','log crossing','$ a day'],1): put(C,f'{L(j)}{PB+4}',h,BOLD)
LINES=[]
for k in range(1,4):
    r=PB+4+k; f=L(14+k)
    put(C,f'A{r}',f'line {k}'); put(C,f'B{r}',f'{GRP[k-1]} / {GRP[k]}')
    put(C,f'C{r}',f'=IFERROR(MATCH(1,{f}{S0}:{f}{S1},0),NA())')
    put(C,f'D{r}',f'=IF(C{r}=1,{k},IF(INDEX($N${S0}:$N${S1},C{r}-1)<=0,{k},INDEX($N${S0}:$N${S1},C{r}-1)))')
    put(C,f'E{r}',f'=INDEX($N${S0}:$N${S1},C{r})')
    put(C,f'F{r}',f'=IF(C{r}=1,0,INDEX($I${S0}:$L${S1},C{r}-1,D{r})-INDEX($I${S0}:$L${S1},C{r}-1,E{r}))',NORM,'0.0000')
    put(C,f'G{r}',f'=INDEX($I${S0}:$L${S1},C{r},D{r})-INDEX($I${S0}:$L${S1},C{r},E{r})',NORM,'0.0000')
    put(C,f'H{r}',f'=IF(C{r}=1,0,IF(F{r}-G{r}=0,0.5,MIN(1,MAX(0,F{r}/(F{r}-G{r})))))',NORM,'0.000')
    put(C,f'I{r}',f'=IF(C{r}=1,INDEX($B${S0}:$B${S1},1),INDEX($B${S0}:$B${S1},C{r}-1)+H{r}*{STEPr})',NORM,'0.000')
    put(C,f'J{r}',f'=EXP(I{r})',BOLD,'0.00')
    LINES.append(f"'Curves 2025'!$J${r}")
C.freeze_panes=f'A{HR+1}'

# ---------------- Engine ----------------
def bform(z,br):
    row=f"'Bins 2025'!$D{br}:$ALO{br}"; first=f"'Bins 2025'!$D{br}"; last=f"'Bins 2025'!$ALO{br}"; m=f'MATCH({z},{row},1)'
    return f'=IF({first}="",0,IF({z}<{first},0.0005*{z}/{first},IF({z}>={last},1,({m}-0.5+({z}-INDEX({row},1,{m}))/(INDEX({row},1,{m}+1)-INDEX({row},1,{m})))/1000)))'
EN=wb.create_sheet('Engine 2025')
put(EN,'A1','Engine 2025: share of each country\'s people at each standard, using the live lines (live)',TITLE)
put(EN,'A2','Columns E to G give the share below each line, read from the sorted bins with linear interpolation between bin means. The four standards are the gaps between the lines. Fits is the share at the standard of the country\'s own group, poorer the share below it and richer the share above it.',ITAL)
hd=['Economy','Code','Group','Pop (m)','below line 1','below line 2','below line 3','at L-std','at LM-std','at UM-std','at H-std','fits','poorer','richer','fits (m)','poorer (m)','richer (m)']
for j,h in enumerate(hd,1): put(EN,f'{L(j)}4',h,BOLD)
for i,c in enumerate(codes):
    r=R0+i
    EN[f'A{r}']=f'=Inputs!A{r}'; EN[f'B{r}']=f'=Inputs!B{r}'; EN[f'C{r}']=f'=Inputs!{CLS25}{r}'
    EN[f'D{r}']=f'=N(Inputs!{POP25}{r})'; EN[f'D{r}'].number_format='#,##0.0'
    for k in range(3):
        EN[f'{L(5+k)}{r}']=bform(LINES[k],r); EN[f'{L(5+k)}{r}'].number_format='0.0000'
    EN[f'H{r}']=f'=E{r}'; EN[f'I{r}']=f'=F{r}-E{r}'; EN[f'J{r}']=f'=G{r}-F{r}'; EN[f'K{r}']=f'=1-G{r}'
    EN[f'L{r}']=f'=IF(C{r}="L",H{r},IF(C{r}="LM",I{r},IF(C{r}="UM",J{r},IF(C{r}="H",K{r},0))))'
    EN[f'M{r}']=f'=IF(C{r}="L",0,IF(C{r}="LM",H{r},IF(C{r}="UM",H{r}+I{r},IF(C{r}="H",H{r}+I{r}+J{r},0))))'
    EN[f'N{r}']=f'=IF(C{r}="L",1-H{r},IF(C{r}="LM",1-H{r}-I{r},IF(C{r}="UM",K{r},0)))'
    for x in 'HIJKLMN': EN[f'{x}{r}'].number_format='0.0%'
    for j,x in enumerate('OPQ'): EN[f'{x}{r}']=f'={"LMN"[j]}{r}*D{r}'; EN[f'{x}{r}'].number_format='#,##0.0'
EN.freeze_panes='E5'; EN.column_dimensions['A'].width=26

# ---------------- Matrix (live) ----------------
MX=wb.create_sheet('Matrix 2025')
put(MX,'A1','The Belindia matrix, 2025 (live)',TITLE)
put(MX,'A2','Millions of people. Rows: the income group of the country. Columns: the standard its people live at. The diagonal is where the label fits.',ITAL)
put(MX,'A4','Typicality lines ($ a day)',BOLD)
for k in range(3): put(MX,f'{L(2+k)}4',f'={LINES[k]}',BOLD,'0.00')
for j,h in enumerate(['Group \\ standard','at L-std','at LM-std','at UM-std','at H-std','Total'],1): put(MX,f'{L(j)}6',h,BOLD)
Cr=f"'Engine 2025'!$C${R0}:$C${R1}"; Pr=f"'Engine 2025'!$D${R0}:$D${R1}"
for ci,g in enumerate(GRP):
    r=7+ci; put(MX,f'A{r}',GL[g])
    for k in range(4):
        hc=L(8+k); put(MX,f'{L(2+k)}{r}',f'=SUMPRODUCT(({Cr}="{g}")*\'Engine 2025\'!${hc}${R0}:${hc}${R1}*{Pr})',BOLD if k==ci else NORM,'#,##0')
    put(MX,f'F{r}',f'=SUM(B{r}:E{r})',NORM,'#,##0')
put(MX,'A11','Total')
for k in range(5): put(MX,f'{L(2+k)}11',f'=SUM({L(2+k)}7:{L(2+k)}10)',NORM,'#,##0')
put(MX,'A13','Summary',BOLD)
for j,h in enumerate(['','Millions','Share'],1): put(MX,f'{L(j)}14',h,BOLD)
put(MX,'A15','Label fits'); put(MX,'B15',f"=SUM('Engine 2025'!$O${R0}:$O${R1})",BOLD,'#,##0'); put(MX,'C15','=B15/$B$18',BOLD,'0.0%')
put(MX,'A16','Poorer than the label'); put(MX,'B16',f"=SUM('Engine 2025'!$P${R0}:$P${R1})",NORM,'#,##0'); put(MX,'C16','=B16/$B$18',NORM,'0.0%')
put(MX,'A17','Richer than the label'); put(MX,'B17',f"=SUM('Engine 2025'!$Q${R0}:$Q${R1})",NORM,'#,##0'); put(MX,'C17','=B17/$B$18',NORM,'0.0%')
put(MX,'A18','Total'); put(MX,'B18','=F11',NORM,'#,##0')
put(MX,'A20','Check against the Python run (should be zero)',ITAL)
MX.column_dimensions['A'].width=26
pickle.dump(dict(LINES=LINES),open('repl_layout.pkl','wb'))

# ---------------- value sheets from the script output ----------------
P4='0.0%'; D2='0.00'; M0='#,##0'
_OUT=pd.read_excel(f'{RUN}/belindia_replication_output.xlsx', sheet_name=None, header=3)
_MAP={'matrix-2025':'Matrix 2025','matrix-1990':'Matrix 1990','matrix-1990-at-2025-lines':'Matrix 1990 at 2025 lines',
      'matrix-2026-nowcast':'Matrix 2026 nowcast','matrix-2026-at-2025-lines':'Matrix 2026 at 2025 lines',
      'shares-2025':'Shares 2025','shares-2026':'Shares 2026','history-1990-2026':'History 1990-2026',
      'skewness-by-economy':'Skewness by economy','world-distribution-2025':'World distribution 2025',
      'group-curves-2025':'Group curves 2025','check-smoothing':'Check smoothing','check-giants':'Check giants',
      'check-missing-rich':'Check missing rich','check-yardsticks':'Check yardsticks','check-survey-type':'Check survey type',
      'inequality-decomposition':'Inequality decomposition','off-diagonal-sources':'Off-diagonal sources',
      'threshold-translation':'Threshold translation','rho-by-economy':'Rho by economy','country-results':'Country results'}
def rd(n):
    d=_OUT[_MAP[n]].copy()
    d=d.loc[:, ~d.columns.astype(str).str.startswith('Unnamed')]
    return d.dropna(how='all')
mat={}
for tag in ['2025','1990','1990-at-2025-lines','2026-nowcast','2026-at-2025-lines']:
    d=rd('matrix-'+tag).rename(columns={'group':'Group'}).set_index('Group')
    mat[tag]=d
    if tag=='2025': continue          # the live sheet "Matrix 2025" already shows this year
    nm='Matrix '+tag.replace('-',' ')
    frame(nm, f'Belindia matrix, {tag.replace("-"," ")}','Millions of people; rows are the income group, columns the standard lived at. Values from belindia_replication.py.',d,index=True,fmts={c:M0 for c in d.columns})
for y,n in [('2025','shares-2025'),('2026','shares-2026')]:
    d=rd(n); frame(f'Shares {y}',f'Share of each group at its own standard, {y}','Poorer, fits and richer are shares of the group population; population in millions.',d,fmts={'population':M0,'poorer':P4,'fits':P4,'richer':P4})
h=rd('history-1990-2026')
frame('History 1990-2026','Label fit by year, 1990 to 2026','fixed_* uses the 2025 lines, year_* re-estimates them each year, pooled_* uses lines from all years pooled.',h,
      fmts={**{c:P4 for c in h.columns if c.endswith('_share')},**{c:D2 for c in h.columns if c.startswith('line')},**{c:M0 for c in h.columns if c.startswith('pop') or c.endswith(('fits','poorer','richer'))}})
sk=rd('skewness-by-economy'); frame('Skewness','Median over mean daily welfare (gamma) by country, 2025','gamma below one means a right-skewed distribution; below_own_mean is the share of people living below their own country mean.',sk,fmts={'gamma':'0.000','below_own_mean':P4,'median':D2,'mean':D2,'pop':'#,##0.0'})
wd=rd('world-distribution-2025'); frame('World distribution','Density of daily welfare across the world, 2025','Actual and the two counterfactuals: everyone at their country mean, and every country rescaled to the world mean.',wd,fmts={'welfare':D2})
gc=rd('group-curves-2025'); frame('Group curves','Welfare density of each income group, 2025','Each curve integrates to one. The lines are where the highest curve changes hands.',gc,fmts={'welfare':D2})
for n,t,note in [('check-smoothing','Annex 1a. Bandwidth and kernel shape','Lines and shares re-derived under each smoothing choice.'),
                 ('check-giants','Annex 1b. Large economies out of the estimation','Excluded countries are still counted in the matrix.'),
                 ('check-missing-rich','Annex 1c. Scaling up the top decile','Welfare multiplied by a factor rising from one at the 90th percentile to the stated value at the 100th.'),
                 ('check-yardsticks','Annex 1d. Fixed, yearly and pooled lines','Pooled lines: $3.78, $7.72, $23.29.'),
                 ('check-survey-type','Annex 1e. Income versus consumption surveys','Income distributions compressed towards their median to mimic a consumption survey.')]:
    d=rd(n); frame(n.replace('-',' ').title()[:31],t,note,d,fmts={**{c:D2 for c in d.columns if c.startswith('line') or c.startswith('rho')},**{c:P4 for c in d.columns if c in ('label_fits','poorer','richer','mean_uplift','fixed_2025_lines','lines_each_year','pooled_lines','UM_fit_consumption_surveys','UM_fit_income_surveys')}})
de=rd('inequality-decomposition'); frame('Inequality decomposition','Mean log deviation split into three levels, 1990 to 2026','The first term is what the classification captures by construction; the other two are what it cannot see.',de,fmts={c:'0.000' for c in de.columns if c!='year'})
od=rd('off-diagonal-sources'); frame('Off-diagonal sources','Where the off-diagonal comes from, 2025','Counterfactual distributions read against the 2025 lines.',od,fmts={c:P4 for c in ('label_fits','poorer','richer')})
tt=rd('threshold-translation'); frame('Threshold translation','Converting the GNI thresholds instead, 2025','rho is welfare times 365 over Atlas GNI per capita, taken as the median across countries within the window of each threshold.',tt,fmts={**{c:D2 for c in tt.columns if c.startswith('line') or c.startswith('rho')},**{c:P4 for c in ('label_fits','poorer','richer')}})
rh=rd('rho-by-economy'); frame('Rho by economy','Survey welfare as a share of GNI per capita, 2025','Only countries with both a survey and a 2025 Atlas GNI figure.',rh,fmts={'gni_2025':M0,'pop':'#,##0.0','rho_mean':'0.000','rho_median':'0.000'})
cr=rd('country-results'); frame('Country results','Annex 2. Every country, by UN region and subregion','at_L to at_H are the shares living at each standard in 2025; the 1990 and 2026 columns repeat the exercise for those years.',cr,
      fmts={**{c:P4 for c in cr.columns if c.startswith('at_') or c=='below_own_mean'},**{'pop':'#,##0.0','median':D2,'mean':D2,'gamma':'0.000','gni_2025':M0}})
# check cell on the live matrix
mx=mat['2025']; tot=mx.values.sum(); fits=np.trace(mx.values)
put(MX,'B20',fits/tot,BLUE,'0.000%'); put(MX,'C20','Python value; C15 minus this should be zero',ITAL)
put(MX,'D20','=C15-B20',GREEN,'0.000%')
wb.save(OUT); print('saved',OUT, os.path.getsize(OUT)//1024,'KB')
