panel-data-set.csv
==================
Cross-country panel used to benchmark Sri Lanka's foreign direct investment.

  4,379 rows   151 economies   1996-2024   one row per country-year
  Unit of observation: country-year. Country identifier: ISO3 alpha-3 code.


-------------------------------------------------------------------------------
1. WHAT THIS FILE IS
-------------------------------------------------------------------------------
panel-data-set.csv supports two estimation exercises:

  (a) A pooled OLS benchmark. Net FDI inflows as a share of GDP are regressed on
      a set of determinants plus year fixed effects, with an indicator for Sri
      Lanka whose coefficient measures the conditional shortfall. A leave-one-out
      variant re-estimates the model excluding Sri Lanka entirely and then
      applies the coefficients to Sri Lanka's own characteristics, so the country
      never influences its own benchmark.

  (b) A stochastic frontier model. The same determinants define a frontier -- the
      maximum inflow observed for economies with given fundamentals -- and each
      country's distance below it is measured as technical efficiency.

panel-data-set.csv is delivered as a single flat table rather than as separate
estimation samples. Three flag columns (section 5) mark which rows enter which
exercise.


-------------------------------------------------------------------------------
2. CONSTRUCTION PIPELINE
-------------------------------------------------------------------------------
Step 1 - Core macro panel
  Pulled from the World Bank World Development Indicators via the API using the
  wbgapi Python client, for all economies and all available years. Series codes
  are listed in section 6.

Step 2 - Governance
  Merged from the Worldwide Governance Indicators. Note for replication: WGI was
  retired from the classic World Bank API endpoint during 2025-26 and can no
  longer be retrieved through wbgapi. It must be downloaded from the DataBank
  interface instead. WGI begins in 1996 and is published biennially until 2002,
  which is why 1997, 1999 and 2001 are missing for every country.

Step 3 - Surrounding market potential
  Constructed, not downloaded. For each country i and year t:

      SMP(i,t) = sum over j != i of  GDP(j,t) / distw(i,j)

  where distw is the population-weighted bilateral distance from CEPII GeoDist
  and the host country is excluded from its own sum. Entered in logs. The CEPII
  file is distributed as .xls and was converted via LibreOffice before merging.
  A robustness variant using the CES-weighted distance (distwces) was also built
  but is not included here.

Step 4 - Conflict
  Merged from two UCDP files, neither of which arrives as a country-year panel:

    - UCDP/PRIO Armed Conflict Dataset (conflict-year level) supplies the
      intensity level: 1 = minor (25-999 battle deaths), 2 = war (1,000+).
    - UCDP Battle-Related Deaths, conflict-year file, supplies annual death
      counts (best, low and high estimates).

  Both use Gleditsch-Ward country codes rather than ISO3, and conflicts spanning
  borders appear with comma-separated country lists. Construction therefore
  required: exploding multi-country conflicts into one row per country; mapping
  GW codes to ISO3 (e.g. GW 780 = LKA); aggregating across concurrent conflicts
  within a country-year; and filling non-conflict years with zeros. Absence of a
  row in UCDP means no conflict that year, not missing data -- treating it as
  missing is the standard way to get this merge wrong.

Step 5 - Sample restrictions
  Applied before panel-data-set.csv was written, so no further filtering of the
  file is needed:

    - Offshore financial centres dropped: NLD, LUX, IRL, CHE, SGP, HKG, MUS,
      CYP, MLT, PAN and the Caribbean centres. Investment routed through
      special-purpose entities inflates their ratios and biases estimated
      determinants.
    - Economies averaging under one million people dropped. In a micro-state a
      single transaction moves the FDI ratio by several percentage points.
    - Years restricted to 1996-2024. The start is set by WGI availability; the
      end by data currency (WGI for 2025 publishes in late 2026, and 2025 FDI
      data covers only about half the sample).

Step 6 - Winsorisation
  The dependent variable is trimmed at the 1st and 99th percentiles. Net FDI can
  be large and negative, and the raw series runs from -82.9 to +161.8 percent of
  GDP. After winsorising, the range is -5.09 to +30.03. Both the raw and trimmed
  series are included so the effect can be inspected.


-------------------------------------------------------------------------------
3. VARIABLE DEFINITIONS
-------------------------------------------------------------------------------
Columns of panel-data-set.csv, in file order.

Identifiers
  iso3              ISO3 country code
  year              calendar year
  lka_dummy         1 for Sri Lanka, 0 otherwise

Dependent variable
  fdi_gdp           net FDI inflows, percent of GDP, as published
  fdi_gdp_w         the same, winsorised at the 1st/99th percentiles
                    -- this is the variable actually estimated on

Determinants (the seven regressors, all entering every specification)
  ln_gdp            log of GDP in current US dollars            [market size]
  ln_gdppc          log of GDP per capita, PPP, constant prices [income level]
  gdp_growth        real GDP growth, percent                    [growth prospects]
  trade_open        trade as percent of GDP                     [export platform]
  inflation         consumer price inflation, percent           [macro stability]
  ln_smp_usd        log surrounding market potential            [market access]
  GE_EST            government effectiveness, WGI point estimate,
                    approximately -2.5 to +2.5                  [institutions]

  A note on ln_smp_usd, since it is constructed rather than sourced: it measures
  access to nearby markets and works against Sri Lanka in the benchmark. India is
  large and close, so Sri Lanka scores well, the model expects more from it, and
  the measured shortfall widens accordingly.

  A note on GE_EST: only one of the six WGI dimensions is used. The six correlate
  at roughly 0.8-0.9 with one another and including them jointly produces severe
  multicollinearity. The first principal component of all six was tested as an
  alternative and changes nothing material.

Conflict
  war               1 if UCDP/PRIO records war-intensity conflict (1,000+
                    battle-related deaths) on the country's territory, else 0
  conflict          1 if any armed conflict was active that year, else 0
  max_intensity     0 = none, 1 = minor (25-999 deaths), 2 = war (1,000+)
  bd_best           battle-related deaths, UCDP best estimate, summed across
                    concurrent conflicts
  ln_bd             log(1 + bd_best). The log(1+x) form keeps the many
                    zero-conflict country-years defined; a plain log would drop
                    most of the panel.
  peace_years       years since the last active armed conflict, capped at 30.
                    Countries with no conflict anywhere in the UCDP window take
                    the cap.

Scale
  pop               total population
  gdp_usd           GDP in current US dollars


-------------------------------------------------------------------------------
4. MISSING DATA
-------------------------------------------------------------------------------
Missing values are left blank in panel-data-set.csv rather than imputed.
Counts by column:

  GE_EST        475    biennial before 2002; some small economies never covered
  trade_open    440    gaps vary by country; missing for Sri Lanka 2010-2014
  inflation     425
  fdi_gdp       203    also propagates to fdi_gdp_w
  ln_smp_usd    203
  ln_gdppc      192
  ln_gdp         91    also gdp_usd
  gdp_growth     90

Conflict variables are complete by construction, since absence of a UCDP record
is coded as zero rather than as missing.

Worth knowing for Sri Lanka specifically: of the 29 years from 1996, eight drop
out of the estimation sample. 1997, 1999 and 2001 lack governance data because
WGI was biennial; 2010-2014 lack trade openness. The 1997 exclusion matters for
interpretation, because 1997 was Sri Lanka's peak FDI year at 2.85 percent of
GDP. Its absence pulls the estimation-sample mean down to 1.14 percent from
1.20 percent on all available 1996-2024 years.


-------------------------------------------------------------------------------
5. SAMPLE FLAGS
-------------------------------------------------------------------------------
Filter panel-data-set.csv on these to reproduce each estimation exactly.

  in_ols_sample = 1
      3,097 observations, 130 countries, 21 Sri Lanka years.
      Rows with complete data on the dependent variable and all seven
      determinants. Used for the descriptive statistics, the main regression,
      the sub-period splits and the year-by-year leave-one-out table.

  in_sfa_sample = 1
      2,882 observations, 125 countries.
      The OLS sample, further requiring strictly positive FDI (the frontier
      model is estimated on log FDI/GDP, so non-positive values cannot enter)
      and at least eight years of data per country. Used for the frontier table.

  in_peacetime_sfa = 1
      1,685 observations, 124 countries.
      The SFA sample restricted to 2010-2024, so that war years do not
      contaminate estimates meant to reflect normal-time investment climate.
      Used for the peer efficiency comparison.

The samples nest: in_peacetime_sfa is a subset of in_sfa_sample, which is a
subset of in_ols_sample.


-------------------------------------------------------------------------------
6. SOURCES
-------------------------------------------------------------------------------
Everything merged into panel-data-set.csv, and everything consulted along the
way.

World Bank, World Development Indicators
  https://databank.worldbank.org/source/world-development-indicators
  Retrieved via the wbgapi Python client (https://pypi.org/project/wbgapi/).
  Series used:
    BX.KLT.DINV.WD.GD.ZS   FDI net inflows, percent of GDP  [dependent variable]
    BX.KLT.DINV.CD.WD      FDI net inflows, current US$
    NY.GDP.MKTP.CD         GDP, current US$
    NY.GDP.MKTP.PP.CD      GDP, PPP
    NY.GDP.PCAP.PP.KD      GDP per capita, PPP, constant
    NY.GDP.MKTP.KD.ZG      real GDP growth
    SP.POP.TOTL            population
    NE.TRD.GNFS.ZS         trade, percent of GDP
    FP.CPI.TOTL.ZG         inflation, consumer prices
    DT.DOD.DECT.GN.ZS      external debt stocks, percent of GNI
    BN.CAB.XOKA.GD.ZS      current account balance, percent of GDP

World Bank, Worldwide Governance Indicators
  https://www.worldbank.org/en/publication/worldwide-governance-indicators
  Downloaded from DataBank; no longer available through the classic API.
  Series: GE.EST (used), plus CC.EST, PV.EST, RQ.EST, RL.EST, VA.EST
  (retained for the principal-component robustness check).

CEPII, GeoDist
  http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=6
  Files dist_cepii (pair-level: dist, distcap, distw, distwces) and geo_cepii
  (country-level, including internal distance dii). distw used in the baseline.
  Documented in Mayer and Zignago (2011), CEPII Working Paper 2011-25.

Uppsala Conflict Data Program
  https://ucdp.uu.se/downloads/
  UCDP/PRIO Armed Conflict Dataset version 26.1
  UCDP Battle-Related Deaths Dataset version 26.1, conflict-year file
  Variables: intensity_level, type_of_conflict, gwno_loc, bd_best, bd_low,
  bd_high, gwno_battle

Consulted and merged during construction but not used in the specifications
reported here:
  Penn World Table 10.1, variable hc (human capital index)
    https://www.rug.nl/ggdc/productivity/pwt/
  Chinn-Ito index of capital account openness, 2023 release (coverage ends 2023)
    https://web.pdx.edu/~ito/Chinn-Ito_website.htm
  Bailey, Strezhnev and Voeten UN voting ideal points, June 2024 release
    https://dataverse.harvard.edu/dataverse/Voeten
    Sessions convert to calendar years as year = session + 1945; ends 2023.
  World Uncertainty Index, global monthly series collapsed to annual means
    https://worlduncertaintyindex.com/

Consulted as cross-checks on the dependent variable:
  UNCTADstat, US.FdiFlowsStock (inward FDI flows and stocks)
    https://unctadstat.unctad.org/
  IMF Balance of Payments, series BFDL_BP6_USD (direct investment, net
  incurrence of liabilities, BPM6)
    https://data.imf.org/

Considered and rejected:
  UNCTAD IIA Navigator (bilateral investment treaty counts). No bulk export is
  available; counts would have to be assembled country by country, and the
  treaty-FDI relationship is weakly identified in the literature.
  OECD FDI Regulatory Restrictiveness Index. Conceptually well suited but covers
  only OECD members and about twenty partners, and does not include Sri Lanka.
