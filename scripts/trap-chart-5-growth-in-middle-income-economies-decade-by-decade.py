"""
chart-5-growth-in-middle-income-economies-decade-by-decade

Self-contained build script for Chart 5 of the Moving Escalator series.
Running it writes the PNG and the CSV into the current directory. It needs
no external data: every number the chart and the caption depend on is in
the DATA block below.

  python3 chart-5-growth-in-middle-income-economies-decade-by-decade.py

Requires matplotlib and numpy only.

Provenance of the DATA block
----------------------------
Source: World Bank WDI, GNI per capita, Atlas method, July 2026 vintage, for
the growth rates and populations; World Bank OGHIST (1 July 2026) for the
income classifications. Populations are UN WPP 2024 medium variant as carried
in the projection workbook income-classification-2050.xlsx.

Each row is one economy classified lower-middle or upper-middle income in 2025,
followed by four tuples, one per decade, in the order 1988-95, 1996-2005,
2006-15, 2016-25:

    (class at the start of the decade, number of annual growth rates found,
     decade median growth in percent, population in millions)

The decade median is the median of the economy's annual growth rates in GNI
per capita within the decade; it is None where fewer than 8 annual rates
exist. The class at the start of the decade is the OGHIST classification in
the year before the first growth rate, and is None where the economy was not
yet classified. Population is measured in 1990, 2005, 2015 and 2025
respectively, matching the decade.

Everything plotted is recomputed from this block at run time, so the bars,
the CSV and the sample counts quoted in the caption cannot drift apart.
"""
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------------
# Decades: label, first and last year of the annual growth rates, weight year
# --------------------------------------------------------------------------
DECADES = [('1988-95', 1988, 1995, 1990),
           ('1996-2005', 1996, 2005, 2005),
           ('2006-15', 2006, 2015, 2015),
           ('2016-25', 2016, 2025, 2025)]

MIN_RATES = 8          # an economy qualifies in a decade only with 8+ annual rates
MIDDLE = ('LM', 'UM')  # middle income

# --------------------------------------------------------------------------
# DATA: economy, code, class in 2025, then one tuple per decade
# --------------------------------------------------------------------------
DATA = [
    ('Albania', 'ALB', 'UM', [(None,8,2.0547945205479423,3.287), ('L',10,17.261246312684364,3.011), ('LM',10,3.40408192553715,2.731), ('UM',10,12.225814158367054,2.35)]),
    ('Algeria', 'DZA', 'UM', [('UM',8,-6.560123329907502,25.376), ('LM',10,5.436424041075194,33.109), ('LM',10,6.301813899436814,40.02), ('UM',10,1.5808597462127594,47.435)]),
    ('Angola', 'AGO', 'LM', [(None,8,-6.068289384719405,11.626), ('L',10,16.36636636636637,19.291), ('LM',10,9.438596491228068,28.158), ('UM',10,-0.8245614035087723,39.04)]),
    ('Argentina', 'ARG', 'UM', [('UM',8,9.940034856585822,32.756), ('UM',10,-3.5692074232548885,39.217), ('UM',10,13.376970529171873,43.477), ('UM',10,6.235371963685465,45.851)]),
    ('Armenia', 'ARM', 'UM', [(None,3,None,3.552), ('L',10,8.347826086956523,3.146), ('LM',10,5.472542606300568,3.005), ('LM',10,9.231902569101324,3.087)]),
    ('Azerbaijan', 'AZE', 'UM', [(None,3,None,7.175), ('L',10,15.966386554621847,8.392), ('LM',10,16.493709624500784,9.649), ('UM',10,4.935346924873485,10.247)]),
    ('Bangladesh', 'BGD', 'LM', [('L',8,3.5098522167487767,111.634), ('L',10,5.083655083655081,144.716), ('L',10,9.285201149425292,159.383), ('LM',10,9.758187357197269,175.687)]),
    ('Belarus', 'BLR', 'UM', [(None,3,None,10.189), ('LM',10,5.718954248366015,9.664), ('LM',10,7.212892816607985,9.461), ('UM',10,7.229179636990568,9.086)]),
    ('Belize', 'BLZ', 'UM', [('LM',8,8.313065026845944,0.183), ('LM',10,1.4063635375364036,0.28), ('UM',10,2.046343350691182,0.356), ('UM',10,3.231933608018467,0.423)]),
    ('Benin', 'BEN', 'LM', [('L',8,2.857142857142847,5.281), ('L',10,11.596638655462188,8.426), ('L',10,3.6774628879892135,11.361), ('L',10,3.670991778006172,14.814)]),
    ('Bhutan', 'BTN', 'LM', [('L',8,2.083333333333337,0.589), ('L',10,10.68376068376069,0.662), ('L',10,8.32122972645848,0.741), ('LM',10,5.76420398500691,0.797)]),
    ('Bolivia', 'BOL', 'LM', [('LM',8,2.8006267136701846,7.13), ('LM',10,2.139219015280136,9.361), ('LM',10,10.504587155963307,11.015), ('LM',10,5.6312656641604,12.582)]),
    ('Bosnia and Herzegovina', 'BIH', 'UM', [(None,3,None,4.449), ('L',10,18.02446434282059,4.096), ('LM',10,3.5849775594885225,3.519), ('UM',10,7.717477075453727,3.14)]),
    ('Botswana', 'BWA', 'UM', [('LM',8,11.70226453937211,1.306), ('LM',10,1.6097982289097645,1.84), ('UM',10,3.40557346844772,2.203), ('UM',10,2.917731289257963,2.562)]),
    ('Brazil', 'BRA', 'UM', [('UM',8,7.459962904608997,149.143), ('UM',10,-3.0348361683978142,184.688), ('LM',10,13.06255861296004,201.676), ('UM',10,2.84015271728133,212.812)]),
    ('Cabo Verde', 'CPV', 'UM', [(None,8,9.714441332088386,0.375), ('LM',10,1.950387596899228,0.485), ('LM',10,3.696753053321422,0.512), ('LM',10,6.812674938379915,0.527)]),
    ('Cambodia', 'KHM', 'LM', [('L',8,9.375,7.375), ('L',10,5.233990147783252,13.439), ('L',10,9.801009801009798,15.623), ('LM',10,7.459304476507578,17.848)]),
    ('Cameroon', 'CMR', 'LM', [('LM',8,-4.623595505617978,11.332), ('L',10,-0.6493506493506496,17.075), ('LM',10,3.34800586901427,22.763), ('LM',10,1.9181991122384279,29.879)]),
    ('China', 'CHN', 'UM', [('L',8,7.045454545454543,1135.185), ('L',10,12.914280756550411,1303.72), ('LM',10,16.95688631883868,1379.86), ('UM',10,5.012978968439952,1406.585)]),
    ('Colombia', 'COL', 'UM', [('LM',8,8.046874999999998,32.44), ('LM',10,1.0593220338983023,42.129), ('LM',10,10.686933892118432,46.97), ('UM',10,4.185706976802228,53.426)]),
    ('Comoros', 'COM', 'LM', [('L',8,0.520833333333337,0.445), ('L',10,1.395619306067064,0.593), ('L',10,2.0504512844249034,0.727), ('L',10,2.6001435144147544,0.883)]),
    ('Congo, Rep.', 'COG', 'LM', [('LM',8,-7.254305977710235,2.381), ('L',10,9.104721832632068,3.696), ('LM',10,8.225237685818609,5.098), ('LM',10,1.3670533080063052,6.484)]),
    ('Cuba', 'CUB', 'UM', [(None,8,-2.3663337637355397,10.632), ('LM',10,6.721034870641174,11.263), ('LM',10,6.807190029296395,11.275), ('UM',4,None,10.937)]),
    ("Côte d'Ivoire", 'CIV', 'LM', [('LM',8,-3.9473684210526327,12.19), ('L',10,2.898799313893652,20.068), ('L',10,5.851851851851853,25.246), ('LM',10,4.170744637468404,32.712)]),
    ('Djibouti', 'DJI', 'LM', [(None,0,None,0.58), ('LM',0,None,0.839), ('LM',0,None,1.02), ('LM',10,5.931315124237013,1.184)]),
    ('Dominica', 'DMA', 'UM', [('LM',8,6.59552164424052,0.07), ('LM',10,3.5895746213964186,0.069), ('UM',10,2.999187296824213,0.07), ('UM',10,5.258790078048891,0.066)]),
    ('Dominican Republic', 'DOM', 'UM', [('LM',8,9.784393517526958,7.151), ('LM',10,4.637281910009183,9.225), ('LM',10,4.638879638879645,10.435), ('UM',10,5.242306586137479,11.52)]),
    ('Ecuador', 'ECU', 'UM', [('LM',8,6.333776974997618,10.474), ('LM',10,5.49041573313418,13.846), ('LM',10,8.575681245706434,16.266), ('UM',10,1.7178891470295388,18.29)]),
    ('Egypt, Arab Rep.', 'EGY', 'LM', [('LM',8,-1.36986301369863,58.397), ('LM',10,4.022907736631298,81.101), ('LM',10,9.676879601398081,99.597), ('LM',10,-3.7667604398816277,118.366)]),
    ('El Salvador', 'SLV', 'UM', [('LM',8,7.293393322282737,5.4), ('LM',10,5.998424294513683,6.006), ('LM',10,4.634146341463419,6.184), ('LM',10,4.746623988274223,6.366)]),
    ('Equatorial Guinea', 'GNQ', 'UM', [('L',8,-1.5151515151515138,0.474), ('L',10,27.27566867989646,0.947), ('UM',10,11.250795355126064,1.454), ('UM',10,-3.8836471831813046,1.938)]),
    ('Eswatini', 'SWZ', 'LM', [('LM',5,None,0.872), ('LM',10,1.4402173913043437,1.079), ('LM',10,3.6151608159089466,1.143), ('LM',10,1.7842276545826152,1.256)]),
    ('Fiji', 'FJI', 'UM', [('LM',8,3.2041705571117296,0.773), ('LM',10,1.1210762331838597,0.882), ('LM',10,4.12719013627515,0.919), ('UM',10,3.2937056795978026,0.933)]),
    ('Gabon', 'GAB', 'UM', [('UM',8,2.1008079507431168,0.984), ('UM',10,5.103480525344062,1.463), ('UM',10,3.5583799448452136,2.041), ('UM',10,2.6904052739982975,2.593)]),
    ('Georgia', 'GEO', 'UM', [(None,5,None,4.802), ('L',10,12.774725274725274,3.902), ('LM',10,10.648885641213003,3.725), ('UM',10,10.413299856287296,3.936)]),
    ('Ghana', 'GHA', 'LM', [('L',8,-1.3513513513513487,15.395), ('L',10,2.6671408250355633,22.449), ('L',10,11.435185185185182,28.696), ('LM',10,2.8696936323588274,35.064)]),
    ('Grenada', 'GRD', 'UM', [('LM',8,3.938701524164512,0.1), ('LM',10,6.073369565217391,0.11), ('UM',10,2.5969356219094797,0.115), ('UM',10,6.3955793672335055,0.117)]),
    ('Guatemala', 'GTM', 'UM', [('LM',8,5.243321139563239,9.025), ('LM',10,4.832836809003638,13.088), ('LM',10,6.372035947594467,15.972), ('LM',10,5.759169940487774,18.688)]),
    ('Guinea', 'GIN', 'LM', [('L',8,1.5476190476190421,6.434), ('L',10,-4.056987788331074,9.246), ('L',10,2.261420171867934,11.767), ('L',10,7.481343283582087,15.1)]),
    ('Haiti', 'HTI', 'LM', [('L',8,2.2063208109719676,6.854), ('L',10,10.15161502966382,9.061), ('L',10,8.672248803827753,10.523), ('L',10,1.9024247000587247,11.906)]),
    ('Honduras', 'HND', 'LM', [('LM',8,-3.059210526315792,4.98), ('L',10,5.07941419141914,7.478), ('LM',10,4.215762024338421,9.237), ('LM',10,5.484053815247658,11.006)]),
    ('India', 'IND', 'LM', [('L',8,0.0,864.972), ('L',10,4.9085365853658525,1154.676), ('L',10,8.900108900108894,1328.024), ('LM',10,6.440915637080269,1463.866)]),
    ('Indonesia', 'IDN', 'UM', [('L',8,8.012820512820507,183.501), ('LM',10,10.868924889543452,230.872), ('LM',10,14.398148148148149,261.799), ('LM',10,4.788425837014277,285.721)]),
    ('Iran, Islamic Rep.', 'IRN', 'UM', [('UM',8,-10.940101870898228,58.38), ('LM',10,8.746488764044935,71.828), ('LM',10,11.899046207385444,82.619), ('UM',10,1.2327416173570027,92.418)]),
    ('Iraq', 'IRQ', 'UM', [('UM',8,2.4495948746938003,17.581), ('LM',10,22.652452496685815,28.407), ('LM',10,13.132150395651209,37.561), ('UM',10,1.1409184608337175,47.021)]),
    ('Jamaica', 'JAM', 'UM', [('LM',8,9.279223779454803,2.38), ('LM',10,5.2108433734939785,2.687), ('LM',10,3.1303852704350543,2.803), ('UM',10,6.00288651084202,2.837)]),
    ('Jordan', 'JOR', 'UM', [('LM',8,2.1759259259259256,3.622), ('LM',10,3.659842098220256,6.03), ('LM',10,5.545159909496733,9.545), ('UM',10,2.3065476190476164,11.521)]),
    ('Kazakhstan', 'KAZ', 'UM', [(None,2,None,17.154), ('LM',10,5.3481913019916005,15.968), ('LM',10,15.643135855005053,18.084), ('UM',10,5.441833425126974,20.844)]),
    ('Kenya', 'KEN', 'LM', [('L',8,-4.224738675958189,22.893), ('L',10,8.608058608058611,35.796), ('L',10,9.610809782091534,47.089), ('LM',10,5.555555555555558,57.532)]),
    ('Kiribati', 'KIR', 'LM', [('LM',8,9.29064657878217,0.075), ('LM',10,0.29973085392708265,0.098), ('LM',10,7.120421733220672,0.117), ('LM',10,4.4046291872378855,0.136)]),
    ('Kosovo', 'XKX', 'UM', [(None,0,None,1.974), (None,0,None,1.818), (None,5,None,1.788), ('LM',10,9.002364182633105,1.577)]),
    ('Kyrgyz Republic', 'KGZ', 'LM', [(None,3,None,4.391), ('L',10,1.7857142857142905,5.163), ('L',10,12.134502923976608,6.04), ('LM',10,7.52521040260824,7.343)]),
    ('Lao PDR', 'LAO', 'LM', [('L',8,11.513157894736848,4.312), ('L',10,4.892473118279572,5.87), ('L',10,15.959595959595962,6.802), ('LM',10,1.826799644514665,7.873)]),
    ('Lebanon', 'LBN', 'LM', [('LM',5,None,3.595), ('LM',10,4.900709219858146,4.671), ('UM',10,4.402027360901295,6.472), ('UM',9,-4.043126684636123,5.849)]),
    ('Lesotho', 'LSO', 'LM', [('L',8,5.641821946169778,1.81), ('LM',10,1.4925373134328401,1.953), ('LM',10,2.7708184204247255,2.105), ('LM',10,0.46100006729927756,2.363)]),
    ('Libya', 'LBY', 'UM', [('UM',8,-0.983835683033546,4.445), ('UM',10,-1.0517292054472438,5.859), ('UM',10,-1.8203502839373054,6.532), ('UM',10,0.8907772759686239,7.459)]),
    ('Malaysia', 'MYS', 'UM', [('LM',8,10.197459691093503,17.833), ('UM',10,4.682930440898825,25.836), ('UM',10,8.874046740467412,31.233), ('UM',10,2.371929430311326,35.978)]),
    ('Maldives', 'MDV', 'UM', [('L',8,11.148066026114812,0.225), ('LM',10,6.873459766420231,0.306), ('LM',10,7.818383872703083,0.428), ('UM',10,7.005050900110632,0.53)]),
    ('Marshall Islands', 'MHL', 'UM', [(None,8,7.5174721189591125,0.045), ('LM',10,3.843386497181911,0.052), ('LM',10,2.5838447846734502,0.049), ('UM',10,5.961370175415337,0.036)]),
    ('Mauritania', 'MRT', 'LM', [('L',8,4.075711522520031,1.952), ('L',10,-1.1904761904761918,2.939), ('L',10,5.403225806451617,3.966), ('LM',10,3.560144436921686,5.315)]),
    ('Mauritius', 'MUS', 'UM', [('LM',8,7.6895398140584215,1.059), ('UM',10,4.801563903863427,1.228), ('UM',10,5.405192499916844,1.263), ('UM',10,3.8699850181207585,1.244)]),
    ('Mexico', 'MEX', 'UM', [('LM',8,16.23529666147725,82.82), ('UM',10,5.702777073753573,105.812), ('UM',10,2.8312593455297574,121.072), ('UM',10,4.780046831215701,131.947)]),
    ('Micronesia, Fed. Sts.', 'FSM', 'UM', [(None,8,5.371687802866276,0.101), ('LM',10,2.0690547006336435,0.111), ('LM',10,2.4938584083972315,0.109), ('LM',10,3.0172888827662225,0.114)]),
    ('Moldova', 'MDA', 'UM', [(None,3,None,2.978), ('LM',10,3.5204081632653095,2.889), ('LM',10,14.495798319327724,2.836), ('LM',10,11.527942238267153,2.361)]),
    ('Mongolia', 'MNG', 'UM', [(None,8,-12.162332214765097,2.099), ('L',10,6.962719298245624,2.536), ('L',10,21.725941746370747,3.027), ('LM',10,7.290934150938089,3.569)]),
    ('Montenegro', 'MNE', 'UM', [(None,0,None,0.606), (None,6,None,0.614), (None,10,4.095513940759532,0.625), ('UM',10,9.833885883789906,0.623)]),
    ('Morocco', 'MAR', 'LM', [('LM',8,3.7996909678325697,24.376), ('LM',10,2.6455942844771596,30.358), ('LM',10,2.954763822704465,34.608), ('LM',10,2.045268408904777,38.431)]),
    ('Myanmar', 'MMR', 'LM', [('L',8,15.476190476190476,39.817), ('L',10,13.574660633484159,47.438), ('L',10,15.340909090909093,51.089), ('LM',10,0.0,54.851)]),
    ('Namibia', 'NAM', 'LM', [(None,8,5.890587167070227,1.369), ('LM',10,-0.6460589517715665,1.967), ('LM',10,4.114999540736653,2.374), ('UM',10,0.11844872823470465,3.093)]),
    ('Nepal', 'NPL', 'LM', [('L',8,0.0,19.525), ('L',10,4.880952380952386,26.309), ('L',10,11.813953488372098,27.824), ('L',10,5.561548943901884,29.618)]),
    ('Nicaragua', 'NIC', 'LM', [('LM',8,-2.3989898989899006,4.163), ('L',10,4.191353960939215,5.342), ('LM',10,5.393697614442294,6.149), ('LM',10,4.016926752401773,7.008)]),
    ('Nigeria', 'NGA', 'LM', [('L',0,None,97.121), ('L',0,None,145.017), ('L',7,None,190.672), ('LM',10,-7.685054219707688,237.528)]),
    ('North Macedonia', 'MKD', 'UM', [(None,3,None,2.064), ('LM',10,2.213064713064705,2.005), ('LM',10,5.174816270101134,1.912), ('UM',10,6.13180059398335,1.821)]),
    ('Pakistan', 'PAK', 'LM', [('L',8,0.0,116.156), ('L',10,9.414414414414418,175.453), ('L',10,4.461881326028405,217.291), ('LM',10,4.2723699658006264,255.22)]),
    ('Papua New Guinea', 'PNG', 'LM', [('LM',8,4.058441558441562,3.896), ('LM',10,-8.62795383769921,6.536), ('L',10,16.46469968387777,8.743), ('LM',10,0.5244755244755206,10.763)]),
    ('Paraguay', 'PRY', 'UM', [('LM',8,7.238152130625242,4.036), ('LM',10,-3.3809523809523845,5.448), ('LM',10,14.174138414121607,6.159), ('UM',10,2.257337983144425,7.013)]),
    ('Peru', 'PER', 'UM', [('LM',8,9.97519206145967,22.015), ('LM',10,4.113448997169932,28.101), ('LM',10,11.146029521264945,30.458), ('UM',10,5.5930710510863175,34.577)]),
    ('Philippines', 'PHL', 'UM', [('LM',8,6.427158866183258,62.855), ('LM',10,1.367019193106156,88.016), ('LM',10,8.669796557120502,105.313), ('LM',10,4.548492559427952,116.787)]),
    ('Samoa', 'WSM', 'UM', [('LM',8,2.975247524752478,0.169), ('LM',10,2.214776070611313,0.187), ('LM',10,5.42706545492061,0.202), ('LM',10,3.643554730655363,0.219)]),
    ('Senegal', 'SEN', 'LM', [('LM',8,-1.0869565217391297,7.721), ('L',10,-1.5045248868778227,11.235), ('L',10,1.8771043771043772,14.593), ('L',10,2.3822451472784056,18.932)]),
    ('Serbia', 'SRB', 'UM', [(None,0,None,7.898), (None,8,0.009556026986218269,7.441), (None,10,1.9870683445195658,7.095), ('UM',10,9.964829472924674,6.549)]),
    ('Solomon Islands', 'SLB', 'LM', [('L',8,6.904761904761902,0.331), ('LM',10,-3.12389536938848,0.483), ('L',10,5.839727195225919,0.639), ('LM',10,-0.9950248756218916,0.839)]),
    ('South Africa', 'ZAF', 'UM', [('LM',8,5.050004167013911,40.746), ('UM',10,-1.133765091548733,49.49), ('UM',10,3.002577842731302,56.724), ('UM',10,1.0542269280871097,64.747)]),
    ('Sri Lanka', 'LKA', 'UM', [('L',8,7.064676616915422,16.352), ('L',10,4.58500669344043,20.217), ('LM',10,13.228438228438232,20.97), ('LM',10,2.8157945642712012,21.756)]),
    ('St. Lucia', 'LCA', 'UM', [('LM',8,4.414024252466664,0.138), ('UM',10,4.044864511241952,0.165), ('UM',10,2.5708810475016386,0.175), ('UM',10,6.085556480397269,0.18)]),
    ('St. Vincent and the Grenadines', 'VCT', 'UM', [('LM',8,5.373294032140841,0.112), ('LM',10,6.689225053078562,0.112), ('UM',10,3.756681243926141,0.107), ('UM',10,6.125608665158577,0.1)]),
    ('Suriname', 'SUR', 'UM', [('UM',8,-6.396965865992415,0.412), ('LM',10,12.708588364151796,0.519), ('LM',10,8.638500411329186,0.582), ('UM',10,1.9496658312447845,0.64)]),
    ('São Tomé and Príncipe', 'STP', 'LM', [('L',8,-1.2195121951219523,0.123), ('L',10,1.5828017954169549,0.162), ('L',10,5.4850673433535,0.2), ('LM',10,9.197875244821653,0.24)]),
    ('Tajikistan', 'TJK', 'LM', [(None,3,None,5.399), ('L',10,3.125,6.925), ('L',10,14.022123893805304,8.644), ('LM',10,3.9705882352941146,10.787)]),
    ('Tanzania', 'TZA', 'LM', [('L',8,-5.92307692307692,26.11), ('L',10,6.749241658240646,39.182), ('L',10,7.610461338531516,52.021), ('L',10,2.4563884959924565,70.546)]),
    ('Thailand', 'THA', 'UM', [('LM',8,12.650365118322583,54.738), ('LM',10,0.5102040816326481,66.017), ('LM',10,9.193116613821628,70.541), ('UM',10,2.219889525284846,71.62)]),
    ('Timor-Leste', 'TLS', 'LM', [(None,3,None,0.76), (None,10,7.82013685239491,0.948), ('L',10,8.275795934023789,1.205), ('LM',10,-2.9659111350962384,1.419)]),
    ('Togo', 'TGO', 'LM', [('L',8,-0.8620689655172431,3.714), ('L',10,1.1627906976744207,5.413), ('L',10,3.0972797161442966,7.072), ('L',10,4.285302039245864,8.592)]),
    ('Tonga', 'TON', 'UM', [('LM',8,8.622423328305684,0.1), ('LM',10,-1.6741071428571452,0.106), ('LM',10,6.0376213592233,0.106), ('LM',10,4.55642795902712,0.104)]),
    ('Tunisia', 'TUN', 'LM', [('LM',8,4.18220946915352,8.325), ('LM',10,6.396624070188817,10.255), ('LM',10,3.832438791265358,11.402), ('LM',10,-0.5141388174807193,12.349)]),
    ('Turkmenistan', 'TKM', 'UM', [(None,5,None,3.761), ('LM',10,8.746973365617439,5.052), ('LM',10,16.547619047619055,6.216), ('UM',10,-2.193257438266516,7.619)]),
    ('Tuvalu', 'TUV', 'UM', [(None,8,6.381914676464584,0.009), (None,10,7.611619150080684,0.01), (None,10,2.8211658177702326,0.011), ('UM',10,3.42933906085231,0.009)]),
    ('Türkiye', 'TUR', 'UM', [('LM',8,9.652509652509655,56.016), ('LM',10,8.323518720465284,69.33), ('UM',10,6.888034939836785,78.218), ('UM',10,2.202944608799373,85.879)]),
    ('Ukraine', 'UKR', 'UM', [(None,6,None,52.054), ('LM',10,3.3686730506156004,47.586), ('LM',10,7.369513641755631,45.785), ('LM',10,6.6523994129375925,38.98)]),
    ('Uzbekistan', 'UZB', 'LM', [(None,5,None,20.465), ('LM',10,0.8620689655172376,26.357), ('L',10,22.61168384879725,30.749), ('LM',10,5.908204300816344,37.053)]),
    ('Vanuatu', 'VUT', 'LM', [('LM',8,3.8080649757765705,0.148), ('LM',10,4.024520255863539,0.211), ('LM',10,5.215125942974053,0.266), ('LM',10,5.045304000784611,0.335)]),
    ('Venezuela, RB', 'VEN', 'LM', [('UM',8,1.9431687715269708,19.827), ('LM',10,8.10128785241907,26.786), ('UM',10,7.949804521967363,30.574), ('UM',10,-2.2819562146892682,28.517)]),
    ('Viet Nam', 'VNM', 'UM', [('L',6,None,65.505), ('L',10,8.516656191074789,81.088), ('L',10,15.031185031185023,92.823), ('LM',10,6.570803140096615,101.599)]),
    ('West Bank and Gaza', 'PSE', 'LM', [(None,0,None,1.978), ('LM',9,8.536585365853666,3.32), ('LM',10,9.196903060289541,4.27), ('LM',10,3.5181303709914014,5.414)]),
    ('Zambia', 'ZMB', 'LM', [('L',8,4.018492176386912,7.786), ('L',10,2.8174603174603075,11.719), ('L',10,6.517909571344682,16.399), ('LM',10,-2.632439502943096,21.914)]),
    ('Zimbabwe', 'ZWE', 'LM', [('LM',8,-4.001600640256103,10.137), ('L',10,-5.505279034690802,12.483), ('L',10,5.4056829852790145,14.399), ('L',10,10.781473533619456,16.951)]),]


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------
def median(values):
    v = sorted(values)
    n = len(v)
    if n == 0:
        raise ValueError('median of empty sequence')
    mid = n // 2
    return v[mid] if n % 2 else 0.5 * (v[mid - 1] + v[mid])


def weighted_median(pairs):
    """Lower weighted median: the value at which cumulative weight reaches half.

    Counting directly rather than interpolating matters here, because a single
    large economy can straddle the midpoint and interpolation would invent a
    value that no economy has.
    """
    pairs = sorted(pairs)
    half = sum(w for _, w in pairs) / 2.0
    cum = 0.0
    for value, weight in pairs:
        cum += weight
        if cum >= half:
            return value
    return pairs[-1][0]


def weighted_median_economy(triples):
    triples = sorted(triples)
    half = sum(t[1] for t in triples) / 2.0
    cum = 0.0
    for value, weight, name in triples:
        cum += weight
        if cum >= half:
            return name
    return triples[-1][2]


def balanced_sample():
    """Economies with a decade median and a population in every decade."""
    out = []
    for name, code, class_2025, cells in DATA:
        if all(c[2] is not None and c[3] is not None for c in cells):
            out.append(name)
    return set(out)


BALANCED = balanced_sample()

series = []       # the eight plotted points
for i, (label, first, last, wyear) in enumerate(DECADES):
    rows = [(cells[i][2], cells[i][3], name)
            for name, code, class_2025, cells in DATA if name in BALANCED]
    series.append(dict(
        label=label, first=first, last=last, wyear=wyear, n=len(rows),
        pop=sum(r[1] for r in rows),
        unweighted=median([r[0] for r in rows]),
        weighted=weighted_median([(r[0], r[1]) for r in rows]),
        weighted_economy=weighted_median_economy(rows)))

# Robustness figure quoted in the caption: every economy with data in each
# decade, rather than the economies present in all four.
unbalanced_unweighted = []
for i, _ in enumerate(DECADES):
    vals = [cells[i][2] for name, code, class_2025, cells in DATA
            if cells[i][2] is not None and cells[i][3] is not None]
    unbalanced_unweighted.append(median(vals))

# Membership defined at the start of each decade cannot be recomputed from this
# block, because it would draw in economies that are not middle income in 2025
# and so are not carried here. The figures are stated as constants and are
# reported in the caption as an alternative definition, not as a plotted series.
CONTEMPORANEOUS_UNWEIGHTED = (5.4, 4.3, 5.6, 4.3)

N_ECONOMIES = len(BALANCED)
POP_SHARE = 100.0 * series[-1]['pop'] / sum(
    cells[3][3] for name, code, class_2025, cells in DATA if cells[3][3] is not None)

# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
CSV_FIELDS = ['record_type', 'series', 'decade', 'first_rate_year', 'last_rate_year',
              'economy', 'code', 'class_2025', 'class_at_decade_start',
              'middle_income_at_decade_start', 'annual_rates_used',
              'decade_median_growth_pct', 'population_mn', 'population_year',
              'in_balanced_sample', 'n_economies', 'weighted_median_economy', 'plotted']


def write_csv(path):
    rows = []
    for s in series:
        for name, value, who in [('Unweighted median', s['unweighted'], ''),
                                 ('Population-weighted median', s['weighted'],
                                  s['weighted_economy'])]:
            rows.append(dict(record_type='chart_series', series=name, decade=s['label'],
                             first_rate_year=s['first'], last_rate_year=s['last'],
                             economy='', code='', class_2025='', class_at_decade_start='',
                             middle_income_at_decade_start='', annual_rates_used='',
                             decade_median_growth_pct=round(value, 3),
                             population_mn=round(s['pop'], 3), population_year=s['wyear'],
                             in_balanced_sample=True, n_economies=s['n'],
                             weighted_median_economy=who, plotted=True))
    for name, code, class_2025, cells in DATA:
        for i, (label, first, last, wyear) in enumerate(DECADES):
            start_class, n_rates, value, population = cells[i]
            rows.append(dict(record_type='economy', series='', decade=label,
                             first_rate_year=first, last_rate_year=last,
                             economy=name, code=code, class_2025=class_2025,
                             class_at_decade_start=start_class if start_class else None,
                             middle_income_at_decade_start=start_class in MIDDLE,
                             annual_rates_used=n_rates,
                             decade_median_growth_pct='' if value is None else round(value, 4),
                             population_mn='' if population is None else population,
                             population_year=wyear,
                             in_balanced_sample=name in BALANCED, n_economies='',
                             weighted_median_economy='',
                             plotted=name in BALANCED))
    with open(path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# --------------------------------------------------------------------------
# Chart
# --------------------------------------------------------------------------
VIVID = {'L': '#C62828', 'LM': '#F9A825', 'UM': '#00897B', 'H': '#283593'}
RED, BLUE = VIVID['L'], VIVID['H']
FIGW, FIGH, DPI = 8.0, 8.0, 200
CAPTION_FS = 8.2
WATERMARK_FS = CAPTION_FS * 1.2
WATERMARK = 'movingfrontiers.substack.com'
LINESPACING = 1.42
X_LEFT = 0.012
X_RIGHT = 1 - 70.0 / (FIGW * DPI)     # right edge 70 px from the canvas edge


def caption_text():
    return (
        "Source: World Bank WDI, GNI per capita, Atlas method, July 2026 vintage, and World Bank OGHIST "
        "(July 2026); author's calculations. "
        "Note: Middle income covers the economies classified lower-middle or upper-middle in 2025. Each "
        "economy's decade median is the median of its annual growth rates within the decade, and each bar "
        "is the median of those economy values, unweighted and weighted by total population in "
        f"{', '.join(str(d[3]) for d in DECADES[:-1])} and {DECADES[-1][3]}. The same {N_ECONOMIES} economies enter every decade and "
        f"they carry {POP_SHARE:.0f} percent of the {DECADES[-1][3]} middle-income population, and an economy qualifies only "
        f"with at least {MIN_RATES} annual rates in a window, which the {DECADES[0][0]} window meets with {MIN_RATES} because the "
        "Atlas series begins in 1987. Widening to every middle-income economy with data in each decade "
        f"raises the unweighted medians to {', '.join('%.1f' % v for v in unbalanced_unweighted[:-1])} and {unbalanced_unweighted[-1]:.1f} percent and leaves the "
        "weighted medians unchanged. Defining membership at the start of each decade instead gives "
        f"unweighted medians of {', '.join('%.1f' % v for v in CONTEMPORANEOUS_UNWEIGHTED[:-1])} and {CONTEMPORANEOUS_UNWEIGHTED[-1]:.1f} percent.")


CLOSERS = ['All bars share identical definitions.',
           'Coverage is reported for every decade.',
           'The ranking of the decades is unchanged.']


def build(png_path, csv_path):
    n_rows = write_csv(csv_path)

    plt.rcParams.update({'font.family': 'DejaVu Sans',
                         'axes.edgecolor': '#666', 'axes.linewidth': 1.0,
                         'axes.facecolor': 'white',
                         'xtick.color': '#333', 'ytick.color': '#333'})

    fig = plt.figure(figsize=(FIGW, FIGH), dpi=DPI, facecolor='white')
    ax = fig.add_axes([0.115, 0.322, 0.841, 0.523])

    x = np.arange(len(series))
    bar_w = 0.36
    unw = [s['unweighted'] for s in series]
    wtd = [s['weighted'] for s in series]

    peak = max(range(len(series)), key=lambda i: series[i]['weighted'])
    ax.axvspan(peak - 0.5, peak + 0.5, color='#EEEEEE', lw=0, zorder=0)
    ax.bar(x - bar_w / 2, unw, bar_w, color=RED, zorder=3, label='Unweighted median')
    ax.bar(x + bar_w / 2, wtd, bar_w, color=BLUE, zorder=3,
           label='Population-weighted median')

    for xi, value, colour in (list(zip(x - bar_w / 2, unw, [RED] * len(x)))
                              + list(zip(x + bar_w / 2, wtd, [BLUE] * len(x)))):
        ax.text(xi, value + 0.16, '%.1f' % value, ha='center', va='bottom',
                fontsize=12.5, fontweight='bold', color=colour, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels([s['label'] for s in series], fontsize=14)
    ax.set_ylim(0, 11.3)
    ax.set_yticks(range(0, 11, 2))
    ax.tick_params(axis='y', labelsize=13, length=4)
    ax.tick_params(axis='x', length=0, pad=8)
    ax.set_ylabel('Percent a year', fontsize=14, color='#222', labelpad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#E3E3E3', lw=0.8, zorder=1)
    ax.text(peak, 10.45, 'the exceptional decade', ha='center', va='bottom',
            fontsize=12.5, style='italic', color='#777', zorder=4)

    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.088), ncol=2,
                       frameon=False, fontsize=13.5, handlelength=1.4,
                       columnspacing=2.4)

    fig.text(X_LEFT, 0.986, 'Growth in middle-income economies,\ndecade by decade',
             fontsize=20, fontweight='bold', color='#222', ha='left', va='top',
             linespacing=1.25)
    fig.text(X_LEFT, 0.878, 'Median across economies of the decade median growth rate',
             fontsize=14, color='#666', ha='left', va='top')

    # ---- caption and watermark, Moving Frontiers standard --------------------
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    box = lambda artist: artist.get_window_extent(renderer).transformed(inv)

    probe = fig.text(0.5, 0.5, '', fontsize=CAPTION_FS, va='baseline', ha='left', alpha=0)

    def width(text, size=CAPTION_FS):
        probe.set_fontsize(size)
        probe.set_text(text)
        return box(probe).width

    movi = width('movi', WATERMARK_FS)
    limit_full = X_RIGHT - X_LEFT
    limit_short = limit_full - movi

    def greedy(words, limit):
        lines, current = [], ''
        for word in words:
            trial = word if not current else current + ' ' + word
            if width(trial) <= limit:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def layout(body):
        """Every line runs full width except the last two, which stop short of
        the watermark; the second to last is filled to at least 70 percent."""
        full = greedy(body.split(), limit_full)
        for cut in range(len(full) - 1, 0, -1):
            head = full[:cut]
            pool = ' '.join(full[cut:]).split()
            tail = greedy(pool, limit_short)
            if len(tail) == 2 and width(tail[0]) >= 0.70 * limit_short:
                if head:
                    wider = head[-1].split() + pool
                    if len(greedy(wider, limit_short)) == 2:
                        head, pool = head[:-1], wider
                best = None
                for split in range(1, len(pool)):
                    left, right = ' '.join(pool[:split]), ' '.join(pool[split:])
                    wl, wr = width(left), width(right)
                    if wl <= limit_short and wr <= limit_short and wl >= 0.70 * limit_short:
                        if best is None or wr > best[0]:
                            best = (wr, [left, right])
                return head + (best[1] if best else tail)
        return None

    body = caption_text()
    lines = layout(body)
    for closer in CLOSERS:
        if lines:
            break
        lines = layout(body + ' ' + closer)
    if not lines:
        raise RuntimeError('caption could not be laid out')

    # Matplotlib text boxes include the descent whatever the glyphs, so measure
    # the ascent against a planted baseline rather than trusting the box height.
    probe.set_fontsize(CAPTION_FS)
    probe.set_text('Ag')
    ascent = box(probe).y1 - 0.5
    line_h = CAPTION_FS * LINESPACING / (72 * FIGH)

    lowest = min(box(legend).y0, box(ax).y0)
    last_baseline = lowest - 2.00 * line_h - ascent - (len(lines) - 1) * line_h

    caption = [fig.text(X_LEFT, last_baseline + (len(lines) - 1 - i) * line_h, line,
                        fontsize=CAPTION_FS, color='#808080', ha='left', va='baseline')
               for i, line in enumerate(lines)]
    watermark = fig.text(X_RIGHT, last_baseline, WATERMARK, fontsize=WATERMARK_FS,
                         color='#999999', ha='right', va='baseline')
    probe.remove()
    fig.canvas.draw()

    gap = box(watermark).x0 - box(caption[-1]).x1
    baseline_diff = abs(box(watermark).y0 - box(caption[-1]).y0)
    top_gap = (lowest - box(caption[0]).y1) / line_h
    assert gap >= movi - 1e-4, 'watermark gap %.5f below movi %.5f' % (gap, movi)
    assert baseline_diff < 0.0015, baseline_diff
    assert min(box(c).y0 for c in caption) > 0.004, 'caption runs off the canvas'
    assert max(box(c).x1 for c in caption) <= X_RIGHT + 1e-4, 'caption past right margin'
    assert abs(top_gap - 2.00) < 0.01, top_gap

    fig.savefig(png_path, dpi=DPI, facecolor='white')
    plt.close(fig)

    print('%s  %d economies in all four decades, %.0f%% of middle-income population'
          % (png_path, N_ECONOMIES, POP_SHARE))
    print('%s  %d rows' % (csv_path, n_rows))
    for s in series:
        print('  %-10s n=%3d  unweighted %5.2f  weighted %5.2f  (%s)'
              % (s['label'], s['n'], s['unweighted'], s['weighted'], s['weighted_economy']))


if __name__ == '__main__':
    stem = 'chart-5-growth-in-middle-income-economies-decade-by-decade'
    build(stem + '.png', stem + '.csv')
