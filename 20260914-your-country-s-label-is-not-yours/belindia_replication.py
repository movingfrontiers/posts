"""
belindia_replication.py
=======================

Self-contained replication of "Your Country's Label Is Not Yours" (Moving
Frontiers, Post 6 in The Moving Escalator series, September 2026).

The script reproduces every number, chart series and table in the post and in
its two annexes: the typicality lines, the Belindia matrices for 1990, 2025 and
the 2026 nowcast, the country-level results for all 218 economies, the
robustness checks, the inequality decomposition and the alternative route of
translating the World Bank's GNI thresholds directly.

WHAT IT NEEDS
-------------
One external file: the World Bank's 1000 Binned Global Distribution. The script
downloads it on first run and caches it next to itself. Everything else
(country names, published income groups 1990-2026, 2025 Atlas GNI per capita,
survey welfare type, UN region and subregion) is embedded below.

    https://datacatalogfiles.worldbank.org/ddh-published/0064304/DR0094423/
    GlobalDist1000bins_1990_2026_20260324_2021_01_02_PROD.csv

Run:  python3 belindia_replication.py            (downloads if needed)
      python3 belindia_replication.py --bins X    (uses local CSV or zip X)

WHAT IT PRODUCES
----------------
    belindia_replication_output.xlsx   every result, one sheet per table
    country-results.csv                Annex 2 on its own, for convenience

METHOD IN BRIEF
---------------
1. For each income group, pool its people and draw the density of their daily
   welfare on a log grid ($0.10 to $2,000 a day, steps of 0.05 in logs). Each
   curve is normalised to unit area, so the four groups are compared on shape
   and not on size, and smoothed with a Gaussian kernel of bandwidth 0.2.
2. The most typical group at a given welfare level is the one whose curve is
   highest. Line k is the first grid cell at or beyond the peak of group k
   where the most typical group is k+1 or higher, interpolated within the cell
   on the difference between the two curves. For 2025 the lines are $3.80,
   $9.21 and $26.86 a day.
3. Each person is assigned to the segment they fall in. Shares below a line are
   read from the sorted bins with linear interpolation between bin means,
   multiplied by population and cross-tabulated by the economy's income group.
   The diagonal of that matrix is the population whose label fits.

CONVENTIONS
-----------
Income groups are always the World Bank's published lists (OGHIST); they are
never recomputed from GNI, so Argentina and Turkiye stay upper-middle income in
2025. The 2026 groups are the projection of the Great Income Inversion post, in
which China crosses the high-income threshold. All 218 classified economies are
counted, including the 46 without a household survey, whose distributions the
Bank imputes; those 46 never contribute to estimating the lines.

Author: Philip Schellekens, movingfrontiers.substack.com
Licence: CC BY 4.0 for the text and results; the underlying data are the World
Bank's, under its own terms.
"""

import argparse, io, os, sys, urllib.request, zipfile
import numpy as np
import pandas as pd

BIN_URL = ("https://datacatalogfiles.worldbank.org/ddh-published/0064304/DR0094423/"
           "GlobalDist1000bins_1990_2026_20260324_2021_01_02_PROD.csv")
BIN_CACHE = "GlobalDist1000bins_1990_2026_20260324_2021_01_02_PROD.csv"
OUT_XLSX = "belindia_replication_output.xlsx"
OUT_CSV = "country-results.csv"          # Annex 2, the one table worth a standalone file

# --------------------------------------------------------------------------
# Method parameters. BW is the only free choice and is varied in check_smoothing.
# --------------------------------------------------------------------------
GRP = ["L", "LM", "UM", "H"]                 # low, lower-middle, upper-middle, high
GRP_LONG = {"L": "Low income", "LM": "Lower-middle income",
            "UM": "Upper-middle income", "H": "High income"}
LO, HI, STEP = np.log(0.1), np.log(2000.0), 0.05   # log-welfare grid
BW = 0.2                                           # Gaussian bandwidth, log units
EPS = 1e-3                                         # a cell counts only above this density
THRESH = {2025: (1175.0, 4635.0, 14375.0)}         # Atlas GNI thresholds for the FY27 lists

GRID = np.arange(0, int(round((HI - LO) / STEP)) + 1) * STEP + LO
XG = np.exp(GRID)
MID = (GRID[:-1] + GRID[1:]) / 2

# --------------------------------------------------------------------------
# Embedded inputs, one row per economy:
#   code: (name, income groups 1990-2026, survey type, 2025 Atlas GNI per capita,
#          UN subregion, UN region)
# Income groups are a 37-character string, one character per year from 1990 to
# 2026: L low, M lower-middle, U upper-middle, H high, "." not classified that
# year. Survey type: c consumption, i income, n no survey (imputed bins).
# GNI is None where the Bank publishes no 2025 Atlas figure.
# --------------------------------------------------------------------------
INPUTS = {
    'ABW': ('Aruba', 'HUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'AFG': ('Afghanistan', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'n', None, 'Southern Asia', 'Asia'),
    'AGO': ('Angola', 'MMMMMLLLLLLLLLMMMMMMMUUUUUMMMMMMMMMMM', 'c', 2860, 'Middle Africa', 'Africa'),
    'ALB': ('Albania', 'MMMLLLMLMMMMMMMMMMMUUMUUUUUUUUUUUUUUU', 'c', 12060, 'Southern Europe', 'Europe'),
    'AND': ('Andorra', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 53230, 'Southern Europe', 'Europe'),
    'ARE': ('United Arab Emirates', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', None, 'Western Asia', 'Asia'),
    'ARG': ('Argentina', 'MUUUUUUUUUUUUUUUUUUUUUUUHUUHUUUUUUUUH', 'i', 14650, 'South America', 'Americas'),
    'ARM': ('Armenia', '.MMLLLLLLLLLMMMMMMMMMMMMMMMUUUUUUUUUU', 'c', 9020, 'Western Asia', 'Asia'),
    'ASM': ('American Samoa', 'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUHHHHH', 'n', None, 'Polynesia', 'Oceania'),
    'ATG': ('Antigua and Barbuda', 'UUUUUUUUUUUUHUUHHHHUUUHHHHHHHHHHHHHHH', 'n', 23790, 'Caribbean', 'Americas'),
    'AUS': ('Australia', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 64120, 'Australia and New Zealand', 'Oceania'),
    'AUT': ('Austria', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 60360, 'Western Europe', 'Europe'),
    'AZE': ('Azerbaijan', '.MMMLLLLLLLLLMMMMMMUUUUUUUUUUUUUUUUUU', 'c', 7360, 'Western Asia', 'Asia'),
    'BDI': ('Burundi', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 240, 'Eastern Africa', 'Africa'),
    'BEL': ('Belgium', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 59500, 'Western Europe', 'Europe'),
    'BEN': ('Benin', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMM', 'c', 1600, 'Western Africa', 'Africa'),
    'BFA': ('Burkina Faso', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 980, 'Western Africa', 'Africa'),
    'BGD': ('Bangladesh', 'LLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMM', 'c', 2840, 'Southern Asia', 'Asia'),
    'BGR': ('Bulgaria', 'MMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUHHHH', 'i', 17780, 'Eastern Europe', 'Europe'),
    'BHR': ('Bahrain', 'UUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 28790, 'Western Asia', 'Asia'),
    'BHS': ('Bahamas, The', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'BIH': ('Bosnia and Herzegovina', '..MLLLLLMMMMMMMMMMUUUUUUUUUUUUUUUUUUU', 'c', 9940, 'Southern Europe', 'Europe'),
    'BLR': ('Belarus', '.UUUMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUU', 'c', 9160, 'Eastern Europe', 'Europe'),
    'BLZ': ('Belize', 'MMMMMMMMMMMMUUUUUUMMMMUUUUUUUUMUUUUUU', 'c', 7530, 'Central America', 'Americas'),
    'BMU': ('Bermuda', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'BOL': ('Bolivia', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'i', 4420, 'South America', 'Americas'),
    'BRA': ('Brazil', 'UUUUUUUUUUUUMMMMUUUUUUUUUUUUUUUUUUUUU', 'i', 10550, 'South America', 'Americas'),
    'BRB': ('Barbados', 'UUUUUUUUUUHUHUUUHHHHHHHHHHHHHHHHHHHHH', 'c', 27080, 'Caribbean', 'Americas'),
    'BRN': ('Brunei Darussalam', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 34790, 'South-eastern Asia', 'Asia'),
    'BTN': ('Bhutan', 'LLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMMM', 'c', 4310, 'Southern Asia', 'Asia'),
    'BWA': ('Botswana', 'MUUMMMMUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'c', 7390, 'Southern Africa', 'Africa'),
    'CAF': ('Central African Republic', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 560, 'Middle Africa', 'Africa'),
    'CAN': ('Canada', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 56420, 'Northern America', 'Americas'),
    'CHE': ('Switzerland', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 110330, 'Western Europe', 'Europe'),
    'CHI': ('Channel Islands', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Northern Europe', 'Europe'),
    'CHL': ('Chile', 'MMMUUUUUUUUUUUUUUUUUUUHHHHHHHHHHHHHHH', 'i', 16960, 'South America', 'Americas'),
    'CHN': ('China', 'LLLLLLLMLMMMMMMMMMMMUUUUUUUUUUUUUUUUH', 'c', 14230, 'Eastern Asia', 'Asia'),
    'CIV': ("Côte d'Ivoire", 'MMMLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMM', 'c', 2780, 'Western Africa', 'Africa'),
    'CMR': ('Cameroon', 'MMMMLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMMMM', 'c', 1860, 'Middle Africa', 'Africa'),
    'COD': ('Congo, Dem. Rep.', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 720, 'Middle Africa', 'Africa'),
    'COG': ('Congo, Rep.', 'MMMMLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMMMM', 'c', 2280, 'Middle Africa', 'Africa'),
    'COL': ('Colombia', 'MMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUU', 'i', 7900, 'South America', 'Americas'),
    'COM': ('Comoros', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMM', 'c', 1950, 'Eastern Africa', 'Africa'),
    'CPV': ('Cabo Verde', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMUUU', 'c', 5590, 'Western Africa', 'Africa'),
    'CRI': ('Costa Rica', 'MMMMMMMMMMUUUUUUUUUUUUUUUUUUUUUUUUHHH', 'i', 17930, 'Central America', 'Americas'),
    'CUB': ('Cuba', 'MMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUU', 'n', None, 'Caribbean', 'Americas'),
    'CUW': ('Curaçao', '....................HHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'CYM': ('Cayman Islands', '...HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'CYP': ('Cyprus', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 36110, 'Western Asia', 'Asia'),
    'CZE': ('Czechia', '..MMUUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHH', 'i', 32960, 'Eastern Europe', 'Europe'),
    'DEU': ('Germany', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 60200, 'Western Europe', 'Europe'),
    'DJI': ('Djibouti', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 3960, 'Eastern Africa', 'Africa'),
    'DMA': ('Dominica', 'MMMMMMMMMUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'n', 10690, 'Caribbean', 'Americas'),
    'DNK': ('Denmark', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 77190, 'Northern Europe', 'Europe'),
    'DOM': ('Dominican Republic', 'MMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUU', 'i', 10620, 'Caribbean', 'Americas'),
    'DZA': ('Algeria', 'MMMMMMMMMMMMMMMMMMUUUUUUUUUUUMMMMUUUU', 'c', 5850, 'Northern Africa', 'Africa'),
    'ECU': ('Ecuador', 'MMMMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUU', 'i', 6890, 'South America', 'Americas'),
    'EGY': ('Egypt, Arab Rep.', 'LLLLLMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 3260, 'Northern Africa', 'Africa'),
    'ERI': ('Eritrea', '..LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'n', None, 'Eastern Africa', 'Africa'),
    'ESP': ('Spain', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 37120, 'Southern Europe', 'Europe'),
    'EST': ('Estonia', '.UUUMMMUUUUUUUUUHHHHHHHHHHHHHHHHHHHHH', 'i', 32310, 'Northern Europe', 'Europe'),
    'ETH': ('Ethiopia', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL.LL', 'c', 1110, 'Eastern Africa', 'Africa'),
    'FIN': ('Finland', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 55250, 'Northern Europe', 'Europe'),
    'FJI': ('Fiji', 'MMMMMMMMMMMMMMMMMUUUMMUUUUUUUUUUUUUUU', 'c', 6230, 'Melanesia', 'Oceania'),
    'FRA': ('France', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 48630, 'Western Europe', 'Europe'),
    'FRO': ('Faeroe Islands', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Northern Europe', 'Europe'),
    'FSM': ('Micronesia, Fed. Sts.', '.MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMUU', 'c', 4760, 'Micronesia', 'Oceania'),
    'GAB': ('Gabon', 'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'c', 8090, 'Middle Africa', 'Africa'),
    'GBR': ('United Kingdom', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 54550, 'Northern Europe', 'Europe'),
    'GEO': ('Georgia', '.MMLLLMMMLLLLMMMMMMMMMMMMUMMUUUUUUUUU', 'c', 8990, 'Western Asia', 'Asia'),
    'GHA': ('Ghana', 'LLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMM', 'c', 2630, 'Western Africa', 'Africa'),
    'GIB': ('Gibraltar', 'UUUU...............HH....HHHHHHHHHHHH', 'n', None, 'Southern Europe', 'Europe'),
    'GIN': ('Guinea', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMM', 'c', 1730, 'Western Africa', 'Africa'),
    'GMB': ('Gambia, The', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 930, 'Western Africa', 'Africa'),
    'GNB': ('Guinea-Bissau', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 1090, 'Western Africa', 'Africa'),
    'GNQ': ('Equatorial Guinea', 'LLLLLLLMMMMLLLUUUHHHHHHHHUUUUUUUUUUUU', 'c', 5890, 'Middle Africa', 'Africa'),
    'GRC': ('Greece', 'UUUUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 25360, 'Southern Europe', 'Europe'),
    'GRD': ('Grenada', 'MMMMMMMUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'c', 11660, 'Caribbean', 'Americas'),
    'GRL': ('Greenland', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Northern America', 'Americas'),
    'GTM': ('Guatemala', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMUUUUUUUUUU', 'i', 6360, 'Central America', 'Americas'),
    'GUM': ('Guam', 'UUUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Micronesia', 'Oceania'),
    'GUY': ('Guyana', 'LLLLLLLMMMMMMMMMMMMMMMMMMUUUUUUUHHHHH', 'i', 28470, 'South America', 'Americas'),
    'HKG': ('Hong Kong SAR, China', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 62500, 'Eastern Asia', 'Asia'),
    'HND': ('Honduras', 'LLLLLLLLLMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'i', 3270, 'Central America', 'Americas'),
    'HRV': ('Croatia', '..MMMUUUUUUUUUUUUUHHHHHHHHUHHHHHHHHHH', 'i', 25360, 'Southern Europe', 'Europe'),
    'HTI': ('Haiti', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMM', 'c', 2010, 'Caribbean', 'Americas'),
    'HUN': ('Hungary', 'UUUUUUUUUUUUUUUUUHHHHHUUHHHHHHHHHHHHH', 'i', 23850, 'Eastern Europe', 'Europe'),
    'IDN': ('Indonesia', 'LLLMMMMMLLLLLMMMMMMMMMMMMMMMMUMMUUUUU', 'c', 5120, 'South-eastern Asia', 'Asia'),
    'IMN': ('Isle of Man', 'UUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Northern Europe', 'Europe'),
    'IND': ('India', 'LLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMM', 'c', 2760, 'Southern Asia', 'Asia'),
    'IRL': ('Ireland', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 87360, 'Northern Europe', 'Europe'),
    'IRN': ('Iran, Islamic Rep.', 'MMMMMMMMMMMMMMMMMMMUUUUUUUUUUUMMMUUUU', 'c', 4650, 'Southern Asia', 'Asia'),
    'IRQ': ('Iraq', 'UMMMMMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUU', 'c', 5690, 'Western Asia', 'Asia'),
    'ISL': ('Iceland', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 89220, 'Northern Europe', 'Europe'),
    'ISR': ('Israel', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 56180, 'Western Asia', 'Asia'),
    'ITA': ('Italy', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 42080, 'Southern Europe', 'Europe'),
    'JAM': ('Jamaica', 'MMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUU', 'c', 7790, 'Caribbean', 'Americas'),
    'JOR': ('Jordan', 'MMMMMMMMMMMMMMMMMMMMUUUUUUMUUUUUMMMUU', 'c', 5260, 'Western Asia', 'Asia'),
    'JPN': ('Japan', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 38340, 'Eastern Asia', 'Asia'),
    'KAZ': ('Kazakhstan', '.MMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUUU', 'c', 13740, 'Central Asia', 'Asia'),
    'KEN': ('Kenya', 'LLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMM', 'c', 2200, 'Eastern Africa', 'Africa'),
    'KGZ': ('Kyrgyz Republic', '.MMMLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMM', 'c', 2800, 'Central Asia', 'Asia'),
    'KHM': ('Cambodia', 'LLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMM', 'n', 2750, 'South-eastern Asia', 'Asia'),
    'KIR': ('Kiribati', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 3930, 'Micronesia', 'Oceania'),
    'KNA': ('St. Kitts and Nevis', 'UUUUUUUUUUUUUUUUUUUUUHHHHHHHHHHHHHHHH', 'n', 24530, 'Caribbean', 'Americas'),
    'KOR': ('Korea, Rep.', 'UUUUUHHHUUUHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 37880, 'Eastern Asia', 'Asia'),
    'KWT': ('Kuwait', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Western Asia', 'Asia'),
    'LAO': ('Lao PDR', 'LLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMM', 'c', 2150, 'South-eastern Asia', 'Asia'),
    'LBN': ('Lebanon', 'MMMMMMMUUUUUUUUUUUUUUUUUUUUUUUUMMMMMM', 'c', None, 'Western Asia', 'Asia'),
    'LBR': ('Liberia', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 830, 'Western Africa', 'Africa'),
    'LBY': ('Libya', 'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'n', 7250, 'Northern Africa', 'Africa'),
    'LCA': ('St. Lucia', 'MMUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'c', 13410, 'Caribbean', 'Americas'),
    'LIE': ('Liechtenstein', '....HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Western Europe', 'Europe'),
    'LKA': ('Sri Lanka', 'LLLLLLLMMMMMMMMMMMMMMMMMMMMMUMMMMMMUU', 'c', 4670, 'Southern Asia', 'Asia'),
    'LSO': ('Lesotho', 'LLLLLMLLLLLLLLLMMMMMMMMMMMMMMMMMMMMMM', 'c', 1280, 'Southern Africa', 'Africa'),
    'LTU': ('Lithuania', '.UMMMMMMMMMUUUUUUUUUUUHHHHHHHHHHHHHHH', 'i', 30500, 'Northern Europe', 'Europe'),
    'LUX': ('Luxembourg', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 95720, 'Western Europe', 'Europe'),
    'LVA': ('Latvia', '.UMMMMMMMMMUUUUUUUUHUUHHHHHHHHHHHHHHH', 'i', 24980, 'Northern Europe', 'Europe'),
    'MAC': ('Macao SAR, China', 'UUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Eastern Asia', 'Asia'),
    'MAF': ('St. Martin (French part)', '....................HHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'MAR': ('Morocco', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 4360, 'Northern Africa', 'Africa'),
    'MCO': ('Monaco', '....HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Western Europe', 'Europe'),
    'MDA': ('Moldova', '.MMMMMLLLLLLLLLMMMMMMMMMMMMMMMUUUUUUU', 'c', 8050, 'Eastern Europe', 'Europe'),
    'MDG': ('Madagascar', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 560, 'Eastern Africa', 'Africa'),
    'MDV': ('Maldives', 'LLLMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUU', 'c', 12950, 'Southern Asia', 'Asia'),
    'MEX': ('Mexico', 'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'i', 13730, 'Central America', 'Americas'),
    'MHL': ('Marshall Islands', '.MMMMMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUU', 'c', 9710, 'Micronesia', 'Oceania'),
    'MKD': ('North Macedonia', '..MMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUU', 'i', 9490, 'Southern Europe', 'Europe'),
    'MLI': ('Mali', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 1120, 'Western Africa', 'Africa'),
    'MLT': ('Malta', 'UUUUUUUUHUHUHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 41440, 'Southern Europe', 'Europe'),
    'MMR': ('Myanmar', 'LLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMM', 'c', 1320, 'South-eastern Asia', 'Asia'),
    'MNE': ('Montenegro', '................UUUUUUUUUUUUUUUUUUUUH', 'i', 14150, 'Southern Europe', 'Europe'),
    'MNG': ('Mongolia', 'MMMLLLLLLLLLLLLLLMMMMMMMUMMMMMMMMUUUU', 'c', 6210, 'Eastern Asia', 'Asia'),
    'MNP': ('Northern Mariana Islands', '..MMMHHHHHHHUUUUUHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Micronesia', 'Oceania'),
    'MOZ': ('Mozambique', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 570, 'Eastern Africa', 'Africa'),
    'MRT': ('Mauritania', 'LLLLLLLLLLLLLLLLLLLLMLMMMMMMMMMMMMMMM', 'c', 2210, 'Western Africa', 'Africa'),
    'MUS': ('Mauritius', 'MMUUUUUUUUUUUUUUUUUUUUUUUUUUUHUUUUUUH', 'c', 14040, 'Eastern Africa', 'Africa'),
    'MWI': ('Malawi', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 600, 'Eastern Africa', 'Africa'),
    'MYS': ('Malaysia', 'MMUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU', 'i', 12380, 'South-eastern Asia', 'Asia'),
    'NAM': ('Namibia', 'MMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUMMM', 'c', 4340, 'Southern Africa', 'Africa'),
    'NCL': ('New Caledonia', 'UUUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Melanesia', 'Oceania'),
    'NER': ('Niger', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 750, 'Western Africa', 'Africa'),
    'NGA': ('Nigeria', 'LLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMM', 'c', 1360, 'Western Africa', 'Africa'),
    'NIC': ('Nicaragua', 'MLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMMMMM', 'i', 2850, 'Central America', 'Americas'),
    'NLD': ('Netherlands', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 68530, 'Western Europe', 'Europe'),
    'NOR': ('Norway', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 97310, 'Northern Europe', 'Europe'),
    'NPL': ('Nepal', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMM', 'c', 1570, 'Southern Asia', 'Asia'),
    'NRU': ('Nauru', '.........................HUUUHHHHHHHH', 'c', 20690, 'Micronesia', 'Oceania'),
    'NZL': ('New Zealand', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 46630, 'Australia and New Zealand', 'Oceania'),
    'OMN': ('Oman', 'UUUUUUUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Western Asia', 'Asia'),
    'PAK': ('Pakistan', 'LLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMM', 'c', 1500, 'Southern Asia', 'Asia'),
    'PAN': ('Panama', 'MMMMMMMMUUUUUUUUUUUUUUUUUUUHHHUHHHHHH', 'i', 19140, 'Central America', 'Americas'),
    'PER': ('Peru', 'MMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUU', 'i', 8430, 'South America', 'Americas'),
    'PHL': ('Philippines', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMUU', 'c', 4850, 'South-eastern Asia', 'Asia'),
    'PLW': ('Palau', '......UUUUUUUUUUUUUUUUUUUUHHHHHUUHHHH', 'n', 19890, 'Micronesia', 'Oceania'),
    'PNG': ('Papua New Guinea', 'MMMMMMMMMMMLLLLLLLMMMMMMMMMMMMMMMMMMM', 'c', 2890, 'Melanesia', 'Oceania'),
    'POL': ('Poland', 'MMMMMMUUUUUUUUUUUUUHHHHHHHHHHHHHHHHHH', 'i', 25520, 'Eastern Europe', 'Europe'),
    'PRI': ('Puerto Rico (U.S.)', 'UUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 27320, 'Caribbean', 'Americas'),
    'PRK': ('Korea, Dem. Rep.', 'MMMMMMMMLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'n', None, 'Eastern Asia', 'Asia'),
    'PRT': ('Portugal', 'UUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 29930, 'Southern Europe', 'Europe'),
    'PRY': ('Paraguay', 'MMMMMMMMMMMMMMMMMMMMMMMMUUUUUUUUUUUUU', 'i', 6750, 'South America', 'Americas'),
    'PSE': ('West Bank and Gaza', '....MMMMMMMMMMMMMMMMMMMMMMMMMMMMUMMMM', 'c', 3250, 'Western Asia', 'Asia'),
    'PYF': ('French Polynesia', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Polynesia', 'Oceania'),
    'QAT': ('Qatar', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 74330, 'Western Asia', 'Asia'),
    'ROU': ('Romania', 'MMMMMMMMMMMMMMMUUUUUUUUUUUUUUHUHHHHHH', 'i', 20190, 'Eastern Europe', 'Europe'),
    'RUS': ('Russian Federation', '.UMMMMMMMMMMMMUUUUUUUUHHHUUUUUUUUHHHH', 'i', 15960, 'Eastern Europe', 'Europe'),
    'RWA': ('Rwanda', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLM', 'c', 1150, 'Eastern Africa', 'Africa'),
    'SAU': ('Saudi Arabia', 'UUUUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHHHH', 'n', 36070, 'Western Asia', 'Asia'),
    'SDN': ('Sudan', 'LLLLLLLLLLLLLLLLLMMMMMMMMMMMMLLLLLLLL', 'c', 900, 'Northern Africa', 'Africa'),
    'SEN': ('Senegal', 'MMMMLLLLLLLLLLLLLLLMMMMMMLLLMMMMMMMMM', 'c', 1780, 'Western Africa', 'Africa'),
    'SGP': ('Singapore', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', 81760, 'South-eastern Asia', 'Asia'),
    'SLB': ('Solomon Islands', 'LLMMMMMMLLLLLLLLLLMLMMMMMMMMMMMMMMMMM', 'c', 2020, 'Melanesia', 'Oceania'),
    'SLE': ('Sierra Leone', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 830, 'Western Africa', 'Africa'),
    'SLV': ('El Salvador', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMUUUUU', 'i', 5410, 'Central America', 'Americas'),
    'SMR': ('San Marino', '.HHH......HHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Southern Europe', 'Europe'),
    'SOM': ('Somalia, Fed. Rep.', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'n', 640, 'Eastern Africa', 'Africa'),
    'SRB': ('Serbia', '................UUUUUUUUUUUUUUUUUUUUH', 'i', 13480, 'Southern Europe', 'Europe'),
    'SSD': ('South Sudan', '.....................MLMLLLLLLLLLLLLL', 'c', None, 'Eastern Africa', 'Africa'),
    'STP': ('São Tomé and Príncipe', 'LLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMMMM', 'c', 3800, 'Middle Africa', 'Africa'),
    'SUR': ('Suriname', 'UUUMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUU', 'c', 6140, 'South America', 'Americas'),
    'SVK': ('Slovak Republic', '..MMMMUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHH', 'i', 26410, 'Eastern Europe', 'Europe'),
    'SVN': ('Slovenia', '..UUUUUHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 35520, 'Southern Europe', 'Europe'),
    'SWE': ('Sweden', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 63010, 'Northern Europe', 'Europe'),
    'SWZ': ('Eswatini', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 3730, 'Southern Africa', 'Africa'),
    'SXM': ('Sint Maarten (Dutch part)', '....................HHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'SYC': ('Seychelles', 'UUUUUUUUUUUUUUUUUUUUUUUUHHHHHHHHHHHHH', 'i', 19200, 'Eastern Africa', 'Africa'),
    'SYR': ('Syrian Arab Republic', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLL', 'c', None, 'Western Asia', 'Asia'),
    'TCA': ('Turks and Caicos Islands', '...................HHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'TCD': ('Chad', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 970, 'Middle Africa', 'Africa'),
    'TGO': ('Togo', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLMM', 'c', 1350, 'Western Africa', 'Africa'),
    'THA': ('Thailand', 'MMMMMMMMMMMMMMMMMMMMUUUUUUUUUUUUUUUUU', 'c', 7690, 'South-eastern Asia', 'Asia'),
    'TJK': ('Tajikistan', '.MLLLLLLLLLLLLLLLLLLLLLLMMMLLLMMMMMMM', 'c', 2080, 'Central Asia', 'Asia'),
    'TKM': ('Turkmenistan', '.MMMMMMLLLMMMMMMMMMMMUUUUUUUUUUUUUUUU', 'c', 6340, 'Central Asia', 'Asia'),
    'TLS': ('Timor-Leste', '...........LLLLLLMMMMMMMMMMMMMMMMMMMM', 'c', 1510, 'South-eastern Asia', 'Asia'),
    'TON': ('Tonga', 'MMMMMMMMMMMMMMMMMMMMMMUUUMUUUUUUUUUUU', 'c', 6840, 'Polynesia', 'Oceania'),
    'TTO': ('Trinidad and Tobago', 'UUUUUUUUUUUUUUUUHHHHHHHHHHHHHHHHHHHHH', 'i', 18550, 'Caribbean', 'Americas'),
    'TUN': ('Tunisia', 'MMMMMMMMMMMMMMMMMMMMUUUUUMMMMMMMMMMMM', 'c', 4300, 'Northern Africa', 'Africa'),
    'TUR': ('Türkiye', 'MMMMMMMUUMUMMMUUUUUUUUUUUUUUUUUUUUUUH', 'i', 16300, 'Western Asia', 'Asia'),
    'TUV': ('Tuvalu', '...................MMUUUUUUUUUUUUUUUU', 'c', 9780, 'Polynesia', 'Oceania'),
    'TWN': ('Taiwan, China', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', None, 'Eastern Asia', 'Asia'),
    'TZA': ('Tanzania', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMM', 'c', 1270, 'Eastern Africa', 'Africa'),
    'UGA': ('Uganda', 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', 'c', 1120, 'Eastern Africa', 'Africa'),
    'UKR': ('Ukraine', '.MMMMMMMMLLLMMMMMMMMMMMMMMMMMMMMMUUUU', 'c', 5510, 'Eastern Europe', 'Europe'),
    'URY': ('Uruguay', 'UUUUUUUUUUUUUUUUUUUUUUHHHHHHHHHHHHHHH', 'i', 24020, 'South America', 'Americas'),
    'USA': ('United States', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'i', 88810, 'Northern America', 'Americas'),
    'UZB': ('Uzbekistan', '.MMMMMMMMLLLLLLLLLLMMMMMMMMMMMMMMMMMM', 'i', 3670, 'Central Asia', 'Asia'),
    'VCT': ('St. Vincent and the Grenadines', 'MMMMMMMMMMMMMUUUUUUUUUUUUUUUUUUUUUUUU', 'n', 12000, 'Caribbean', 'Americas'),
    'VEN': ('Venezuela, RB', 'UUUUMMMUUUUUUUUUUUUUUUUUHUUUUU.....MM', 'i', 3860, 'South America', 'Americas'),
    'VGB': ('British Virgin Islands', '.........................HHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'VIR': ('Virgin Islands (U.S.)', 'HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH', 'n', None, 'Caribbean', 'Americas'),
    'VNM': ('Viet Nam', 'LLLLLLLLLLLLLLLLLLLMMMMMMMMMMMMMMMMUU', 'c', 4970, 'South-eastern Asia', 'Asia'),
    'VUT': ('Vanuatu', 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM', 'c', 4410, 'Melanesia', 'Oceania'),
    'WSM': ('Samoa', 'MMMMMMMMMMMMMMMMMMMMMMMMMMUUUUMMMMUUU', 'c', 5640, 'Polynesia', 'Oceania'),
    'XKX': ('Kosovo', '..................MMMMMMMMMMUUUUUUUUU', 'i', 7760, 'Southern Europe', 'Europe'),
    'YEM': ('Yemen, Rep.', 'MLLLLLLLLLLLLLLLLLLMMMMMMMMLLLLLLLLLL', 'c', None, 'Western Asia', 'Asia'),
    'ZAF': ('South Africa', 'UUUUUUUUMUUMMMUUUUUUUUUUUUUUUUUUUUUUU', 'c', 6270, 'Southern Africa', 'Africa'),
    'ZMB': ('Zambia', 'LLLLLLLLLLLLLLLLLLLLMMMMMMMMMMMLMMMMM', 'c', 1200, 'Eastern Africa', 'Africa'),
    'ZWE': ('Zimbabwe', 'MLLLLLLLLLLLLLLLLLLLLLLLLLLLMMMMMMMMM', 'c', 2660, 'Eastern Africa', 'Africa'),}

CLS_CHAR = {"L": "L", "M": "LM", "U": "UM", "H": "H"}
YEARS = list(range(1990, 2027))


def groups_in(year):
    """Published income group of every economy in a given year, as a Series."""
    j = YEARS.index(year)
    return pd.Series({c: CLS_CHAR.get(v[1][j]) for c, v in INPUTS.items()}).dropna()


META = pd.DataFrame(
    {c: dict(name=v[0], survey=v[2], gni=v[3], subregion=v[4], region=v[5])
     for c, v in INPUTS.items()}).T


# ==========================================================================
# 1. Data
# ==========================================================================
def fetch_bins(path=None):
    """Return the 1000-bin file as a DataFrame, downloading it once if needed."""
    if path and path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            name = [n for n in z.namelist() if n.endswith(".csv")][0]
            with z.open(name) as f:
                return _read_bins(f)
    src = path or BIN_CACHE
    if not os.path.exists(src):
        print(f"downloading {BIN_URL}\n  (about 1 GB uncompressed, this takes a few minutes)")
        with urllib.request.urlopen(BIN_URL) as r, open(BIN_CACHE, "wb") as f:
            while True:
                chunk = r.read(1 << 22)
                if not chunk:
                    break
                f.write(chunk)
        src = BIN_CACHE
    return _read_bins(src)


def _read_bins(src):
    parts = pd.read_csv(src, usecols=["year", "code", "quantile", "welf", "pop"],
                        dtype={"code": "category"}, chunksize=2_000_000)
    df = pd.concat(parts, ignore_index=True)
    df["code"] = df["code"].astype(str)
    return df.sort_values(["year", "code", "quantile"])


def year_panel(df, year, group_year=None):
    """Welfare matrix (economies x 1000 bins), income groups and population."""
    g = groups_in(group_year or year)
    d = df[df.year == year]
    W = d.pivot(index="code", columns="quantile", values="welf")
    codes = [c for c in W.index if c in g.index]
    pop = d.groupby("code")["pop"].sum().loc[codes].to_numpy(float)
    return codes, W.loc[codes].to_numpy(float), g.loc[codes].to_numpy(), pop


# ==========================================================================
# 2. The typicality method
# ==========================================================================
def shares_below_grid(W):
    """Share of each economy's people at or below every grid edge."""
    return np.column_stack([(W <= x).sum(1) for x in XG]) / 1000.0


def kernel(bw=BW, kind="gauss"):
    if kind == "gauss":
        r = int(np.ceil(5 * bw / STEP)); k = np.arange(-r, r + 1)
        w = np.exp(-0.5 * (k * STEP / bw) ** 2)
    else:                                            # Epanechnikov, same variance
        r = int(np.ceil(bw * np.sqrt(5) / STEP)); k = np.arange(-r, r + 1)
        w = np.clip(1 - (k * STEP / (bw * np.sqrt(5))) ** 2, 0, None)
    return w / w.sum()


def group_curves(F, cls, pop, bw=BW, kind="gauss"):
    """Smoothed density of daily welfare for each income group, unit area each."""
    ker = kernel(bw, kind); out = {}
    for c in GRP:
        m = cls == c
        if m.sum() == 0 or pop[m].sum() == 0:
            out[c] = np.zeros(len(MID)); continue
        raw = (np.diff(F[m], axis=1) * pop[m][:, None]).sum(0) / pop[m].sum() / STEP
        out[c] = np.convolve(raw, ker, "same")
    return out


def typicality_lines(curves):
    """The three welfare levels at which the most typical income group changes."""
    D = np.column_stack([curves[c] for c in GRP])
    top = np.where(D.max(1) > EPS, D.argmax(1), -1)
    peaks = D.argmax(0)
    lines = []
    for k in range(1, 4):
        idx = np.where((top >= k) & (np.arange(len(top)) >= peaks[k - 1]))[0]
        if len(idx) == 0:
            lines.append(np.nan); continue
        j = idx[0]
        if j == 0:
            lines.append(float(np.exp(MID[0]))); continue
        a = top[j - 1] if top[j - 1] >= 0 else k - 1
        b = top[j]
        d0, d1 = D[j - 1, a] - D[j - 1, b], D[j, a] - D[j, b]
        t = 0.5 if d0 == d1 else min(max(d0 / (d0 - d1), 0.0), 1.0)
        lines.append(float(np.exp(MID[j - 1] + t * STEP)))
    return lines


def shares_below(W, lines):
    """Share of each economy's people below each line, interpolated between bins."""
    out = np.zeros((len(W), len(lines)))
    for i, w in enumerate(W):
        for j, x in enumerate(lines):
            m = int((w <= x).sum())
            out[i, j] = (0.0005 * x / w[0] if m == 0 else 1.0 if m == 1000 else
                         (m - 0.5 + (x - w[m - 1]) / (w[m] - w[m - 1])) / 1000)
    return out


def standard_shares(W, lines):
    """Share of each economy's people living at each of the four standards."""
    b = shares_below(W, lines)
    return np.column_stack([b[:, 0], b[:, 1] - b[:, 0], b[:, 2] - b[:, 1], 1 - b[:, 2]])


def belindia_matrix(W, cls, pop, lines):
    """Millions of people by income group (rows) and standard lived at (columns)."""
    sh = standard_shares(W, lines)
    M = pd.DataFrame(sh * pop[:, None], columns=GRP).groupby(cls).sum().reindex(GRP).fillna(0)
    M.index.name = "group"
    return M, sh


def fit_summary(M):
    v = M.to_numpy(); tot = v.sum()
    fits = np.trace(v); richer = np.triu(v, 1).sum()
    return dict(total=tot, fits=fits, poorer=tot - fits - richer, richer=richer,
                fits_share=fits / tot, poorer_share=(tot - fits - richer) / tot,
                richer_share=richer / tot)


def lines_for(W, cls, pop, bw=BW, kind="gauss", mask=None):
    """Estimate the lines, optionally from a subset of economies."""
    F = shares_below_grid(W if mask is None else W[mask])
    c = cls if mask is None else cls[mask]
    p = pop if mask is None else pop[mask]
    return typicality_lines(group_curves(F, c, p, bw, kind))


# ==========================================================================
# 3. Analyses, one function per result in the post
# ==========================================================================
def main_year(df, year, group_year=None, lines=None):
    """Lines, matrix and per-economy shares for one year."""
    codes, W, cls, pop = year_panel(df, year, group_year)
    if lines is None:
        lines = lines_for(W, cls, pop)
    M, sh = belindia_matrix(W, cls, pop, lines)
    ctry = pd.DataFrame(sh, index=codes, columns=[f"at_{c}" for c in GRP])
    ctry.insert(0, "pop", pop); ctry.insert(0, "group", cls)
    ctry["median"] = np.median(W, 1); ctry["mean"] = W.mean(1)
    ctry["gamma"] = ctry["median"] / ctry["mean"]
    ctry["below_own_mean"] = [(w < w.mean()).mean() for w in W]
    return dict(lines=lines, matrix=M, summary=fit_summary(M), country=ctry,
                codes=codes, W=W, cls=cls, pop=pop)


def history(df, lines_2025):
    """Label fit every year from 1990 to 2026 under three yardsticks."""
    rows, panels, F_all, c_all, p_all = [], {}, [], [], []
    for y in YEARS:
        codes, W, cls, pop = year_panel(df, y)
        F = shares_below_grid(W)
        ly = typicality_lines(group_curves(F, cls, pop))
        F_all.append(F); c_all.append(cls); p_all.append(pop)
        panels[y] = (codes, W, cls, pop)
        row = dict(year=y, status="nowcast" if y == 2026 else "actual", pop=pop.sum(),
                   line_L_LM=ly[0], line_LM_UM=ly[1], line_UM_H=ly[2])
        for c in GRP:
            row[f"pop_{c}"] = pop[cls == c].sum()
        for tag, z in (("year", ly), ("fixed", lines_2025)):
            s = fit_summary(belindia_matrix(W, cls, pop, z)[0])
            row.update({f"{tag}_{k}": v for k, v in s.items() if k != "total"})
        rows.append(row)
    pooled = typicality_lines(group_curves(np.vstack(F_all), np.concatenate(c_all),
                                           np.concatenate(p_all)))
    for i, y in enumerate(YEARS):
        codes, W, cls, pop = panels[y]
        s = fit_summary(belindia_matrix(W, cls, pop, pooled)[0])
        rows[i].update({f"pooled_{k}": v for k, v in s.items() if k != "total"})
    return pd.DataFrame(rows), pooled, panels


def check_smoothing(W, cls, pop):
    """Annex 1a. Bandwidth and kernel shape."""
    rows = []
    for bw in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
        z = lines_for(W, cls, pop, bw=bw)
        s = fit_summary(belindia_matrix(W, cls, pop, z)[0])
        rows.append(dict(smoothing=f"Gaussian, bandwidth {bw:.2f}", **_lz(z), **_ls(s)))
    z = lines_for(W, cls, pop, kind="epa")
    s = fit_summary(belindia_matrix(W, cls, pop, z)[0])
    rows.append(dict(smoothing="Epanechnikov, same variance as 0.20", **_lz(z), **_ls(s)))
    return pd.DataFrame(rows)


def check_giants(codes, W, cls, pop):
    """Annex 1b. India, China and the imputed economies out of the estimation."""
    codes = np.array(codes); rows = []
    survey = np.array([META.loc[c, "survey"] != "n" for c in codes])
    for label, mask in (("none (baseline)", None),
                        ("India excluded from the lower-middle curve", ~np.isin(codes, ["IND"])),
                        ("China excluded from the upper-middle curve", ~np.isin(codes, ["CHN"])),
                        ("India and China excluded", ~np.isin(codes, ["IND", "CHN"])),
                        ("curves from survey economies only", survey)):
        z = lines_for(W, cls, pop, mask=mask)
        s = fit_summary(belindia_matrix(W, cls, pop, z)[0])
        rows.append(dict(excluded=label, **_lz(z), **_ls(s)))
    return pd.DataFrame(rows)


def check_missing_rich(W, cls, pop):
    """Annex 1c. Scaling up the top decile of every economy."""
    q = np.arange(1, 1001); base = np.average(W.mean(1), weights=pop); rows = []
    for f in (1.0, 1.25, 1.5, 2.0, 3.0):
        Wx = W * np.where(q > 900, 1 + (f - 1) * (q - 900) / 100, 1.0)
        z = lines_for(Wx, cls, pop)
        M, _ = belindia_matrix(Wx, cls, pop, z); s = fit_summary(M)
        rows.append(dict(correction="none (baseline)" if f == 1 else f"top decile up to x{f:g}",
                         mean_uplift=np.average(Wx.mean(1), weights=pop) / base - 1,
                         **_lz(z), **_ls(s), richer_millions=s["richer"]))
    return pd.DataFrame(rows)


def check_yardsticks(hist, pooled):
    """Annex 1d. Fixed, yearly and pooled lines in selected years."""
    h = hist.set_index("year")
    rows = [dict(year=y, fixed_2025_lines=h.loc[y, "fixed_fits_share"],
                 lines_each_year=h.loc[y, "year_fits_share"],
                 pooled_lines=h.loc[y, "pooled_fits_share"],
                 year_line_L_LM=h.loc[y, "line_L_LM"], year_line_LM_UM=h.loc[y, "line_LM_UM"],
                 year_line_UM_H=h.loc[y, "line_UM_H"]) for y in (1990, 2010, 2025, 2026)]
    out = pd.DataFrame(rows)
    out.attrs["pooled_lines"] = pooled
    return out


def check_income_consumption(codes, W, cls, pop):
    """Annex 1e. Compressing income surveys towards a consumption-like shape."""
    survey = np.array([META.loc[c, "survey"] for c in codes])
    inc = survey == "i"; med = np.median(W, 1)[:, None]; rows = []
    for b in (1.0, 0.9, 0.8, 0.7):
        Wx = W.copy(); Wx[inc] = (med * (W / med) ** b)[inc]
        z = lines_for(Wx, cls, pop)
        s = fit_summary(belindia_matrix(Wx, cls, pop, z)[0])
        um = {}
        for t in ("c", "i"):
            m = survey == t
            Mt, _ = belindia_matrix(Wx[m], cls[m], pop[m], z)
            um[t] = Mt.loc["UM", "UM"] / Mt.loc["UM"].sum()
        rows.append(dict(compression="none (baseline)" if b == 1 else f"elasticity {b:.1f}",
                         **_lz(z), **_ls(s),
                         UM_fit_consumption_surveys=um["c"], UM_fit_income_surveys=um["i"]))
    out = pd.DataFrame(rows)
    # the two lines that can be estimated from a single survey type
    for t, name in (("c", "consumption"), ("i", "income")):
        m = survey == t
        out.attrs[f"lines_{name}_only"] = lines_for(W, cls, pop, mask=m)
    return out


def decomposition(panels):
    """Mean log deviation split into three levels, every year."""
    rows = []
    for y, (codes, W, cls, pop) in panels.items():
        Wc = np.clip(W, 0.28, None)
        mu_c = Wc.mean(1); mu = np.average(mu_c, weights=pop)
        within = np.average((np.log(mu_c)[:, None] - np.log(Wc)).mean(1), weights=pop)
        mu_g = {g: np.average(mu_c[cls == g], weights=pop[cls == g]) for g in GRP
                if (cls == g).sum()}
        share_g = {g: pop[cls == g].sum() / pop.sum() for g in mu_g}
        between_groups = sum(share_g[g] * np.log(mu / mu_g[g]) for g in mu_g)
        between_within = sum(share_g[g] * np.average(np.log(mu_g[g] / mu_c[cls == g]),
                                                     weights=pop[cls == g]) for g in mu_g)
        rows.append(dict(year=y, mld_total=between_groups + between_within + within,
                         between_income_groups=between_groups,
                         between_countries_within_groups=between_within,
                         within_countries=within, mean_welfare=mu))
    return pd.DataFrame(rows)


def counterfactual_densities(codes, W, cls, pop):
    """Annex 1. The world distribution with each kind of inequality removed."""
    mu_c = W.mean(1); mu = np.average(mu_c, weights=pop)
    ker = kernel()
    def dens(Wx):
        F = shares_below_grid(Wx)
        raw = (np.diff(F, axis=1) * pop[:, None]).sum(0) / pop.sum() / STEP
        return np.convolve(raw, ker, "same")
    def below(Wx):
        w = Wx.ravel(); p = np.repeat(pop / 1000, 1000)
        return p[w < mu].sum() / p.sum()
    Wsc = W * (mu / mu_c)[:, None]
    hb, _ = np.histogram(np.log(mu_c), bins=GRID, weights=pop)
    between = np.convolve(hb / hb.sum() / STEP, ker, "same")
    out = pd.DataFrame({"welfare": np.exp(MID), "actual": dens(W),
                        "between_countries_only": between, "within_countries_only": dens(Wsc)})
    out.attrs["world_mean"] = mu
    out.attrs["below_mean"] = dict(actual=below(W),
                                   between_only=pop[mu_c < mu].sum() / pop.sum(),
                                   within_only=below(Wsc))
    return out


def off_diagonal_sources(W, cls, pop, lines):
    """Annex 1. How much of the off-diagonal is skewness and how much is position."""
    mu_c = W.mean(1)
    mu_g = np.array([np.average(mu_c[cls == g], weights=pop[cls == g]) for g in cls])
    rows = []
    for label, Wx in (("actual", W),
                      ("within-country inequality removed", np.repeat(mu_c[:, None], 1000, 1)),
                      ("position removed", W * (mu_g / mu_c)[:, None]),
                      ("both removed", np.repeat(mu_g[:, None], 1000, 1))):
        s = fit_summary(belindia_matrix(Wx, cls, pop, lines)[0])
        rows.append(dict(counterfactual=label, **_ls(s)))
    out = pd.DataFrame(rows)
    band = np.digitize(mu_c, lines); own = np.array([GRP.index(c) for c in cls])
    out.attrs["mean_outside_band"] = dict(economies=int((band != own).sum()),
                                          population=float(pop[band != own].sum()))
    out.attrs["group_means"] = {g: float(np.average(mu_c[cls == g], weights=pop[cls == g]))
                                for g in GRP}
    return out


def threshold_translation(codes, W, cls, pop):
    """Annex 1. Converting the Bank's GNI thresholds into daily welfare instead."""
    gni = np.array([META.loc[c, "gni"] if META.loc[c, "gni"] is not None else np.nan
                    for c in codes], float)
    survey = np.array([META.loc[c, "survey"] != "n" for c in codes])
    mean_w, med_w = W.mean(1), np.median(W, 1)
    ok = survey & ~np.isnan(gni)
    rho_mean, rho_med = mean_w * 365 / gni, med_w * 365 / gni
    scatter = pd.DataFrame(dict(code=np.array(codes)[ok], group=cls[ok], pop=pop[ok],
                                gni_2025=gni[ok], rho_mean=rho_mean[ok], rho_median=rho_med[ok]))
    T = np.array(THRESH[2025]); rows = []
    for basis, rho in (("mean", rho_mean), ("median", rho_med)):
        for k in (1.25, 1.5, 2.0, 3.0, 4.0):
            r, n = [], []
            for t in T:
                m = ok & (gni > t / k) & (gni < t * k)
                r.append(np.median(rho[m])); n.append(int(m.sum()))
            z = list(T * np.array(r) / 365)
            s = fit_summary(belindia_matrix(W, cls, pop, z)[0])
            rows.append(dict(basis=f"{basis} welfare", window=f"x{k:g}",
                             n_line1=n[0], n_line2=n[1], n_line3=n[2],
                             rho1=r[0], rho2=r[1], rho3=r[2], **_lz(z), **_ls(s)))
    return pd.DataFrame(rows), scatter


def _lz(z):
    return dict(line_L_LM=z[0], line_LM_UM=z[1], line_UM_H=z[2])


def _ls(s):
    return dict(label_fits=s["fits_share"], poorer=s["poorer_share"], richer=s["richer_share"])


# ==========================================================================
# 4. Output
# ==========================================================================
SHEETS = []          # (sheet name, title, note, DataFrame, index?)


def add(name, title, note, df, index=False):
    SHEETS.append((name, title, note, df, index))


def country_table(res25, res90, res26):
    """Annex 2. Every economy, its group, survey type and the four shares."""
    c = res25["country"].copy()
    c.insert(0, "economy", [META.loc[i, "name"] for i in c.index])
    c.insert(1, "region", [META.loc[i, "region"] for i in c.index])
    c.insert(2, "subregion", [META.loc[i, "subregion"] for i in c.index])
    c.insert(4, "survey", [META.loc[i, "survey"] for i in c.index])
    c["gni_2025"] = [META.loc[i, "gni"] for i in c.index]
    for tag, r in (("1990", res90), ("2026", res26)):
        s = r["country"].reindex(c.index)
        c[f"group_{tag}"] = s["group"]
        for g in GRP:
            c[f"at_{g}_{tag}"] = s[f"at_{g}"]
    c.index.name = "code"
    return c.sort_values(["region", "subregion", "economy"])


def write_outputs():
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook(); wb.remove(wb.active)
    bold = Font(bold=True)
    for name, title, note, df, index in SHEETS:
        ws = wb.create_sheet(name[:31])
        ws["A1"] = title; ws["A1"].font = Font(bold=True, size=12); ws["A2"] = note
        cols = ([df.index.name or "index"] if index else []) + [str(c) for c in df.columns]
        for j, h in enumerate(cols, 1):
            ws.cell(4, j, h).font = bold
        for i, (ix, row) in enumerate(df.iterrows(), 5):
            vals = ([ix] if index else []) + list(row.values)
            for j, v in enumerate(vals, 1):
                if isinstance(v, (np.floating, np.integer)):
                    v = v.item()
                if isinstance(v, float) and np.isnan(v):
                    v = None
                ws.cell(i, j, v)
        ws.freeze_panes = "A5"
        ws.column_dimensions["A"].width = 30
        if name == "Country results":
            df.to_csv(OUT_CSV, index=index)
    wb.save(OUT_XLSX)
    print(f"wrote {OUT_XLSX} ({len(SHEETS)} sheets) and {OUT_CSV}")


# ==========================================================================
# 5. Run
# ==========================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[3])
    ap.add_argument("--bins", help="local 1000-bin CSV or zip; downloaded if omitted")
    args = ap.parse_args()

    df = fetch_bins(args.bins)
    print(f"bins loaded: {df.year.nunique()} years, {df.code.nunique()} economies")

    # --- headline year
    r25 = main_year(df, 2025)
    z = r25["lines"]
    print(f"2025 typicality lines: ${z[0]:.2f}, ${z[1]:.2f}, ${z[2]:.2f}; "
          f"label fits {100 * r25['summary']['fits_share']:.1f}% of "
          f"{r25['summary']['total'] / 1000:.2f}bn people")

    r90 = main_year(df, 1990)
    r26 = main_year(df, 2026)
    r26f = main_year(df, 2026, lines=z)          # 2026 against the 2025 yardstick
    r90f = main_year(df, 1990, lines=z)

    add("Read me", "Belindia replication: results behind Your Country's Label Is Not Yours",
        "One sheet per table in the post. Every sheet is also written as a csv. "
        "Method and conventions are documented in the script header.",
        pd.DataFrame({"item": ["typicality lines 2025", "label fits 2025", "population 2025",
                               "poorer than label", "richer than label"],
                      "value": [f"${z[0]:.2f} / ${z[1]:.2f} / ${z[2]:.2f}",
                                f"{100 * r25['summary']['fits_share']:.1f}%",
                                f"{r25['summary']['total'] / 1000:.2f}bn",
                                f"{100 * r25['summary']['poorer_share']:.1f}%",
                                f"{100 * r25['summary']['richer_share']:.1f}%"]}))

    for tag, r, note in (("2025", r25, "own lines"), ("1990", r90, "own lines"),
                         ("1990 at 2025 lines", r90f, "2025 lines held fixed"),
                         ("2026 nowcast", r26, "own lines"),
                         ("2026 at 2025 lines", r26f, "2025 lines held fixed")):
        M = r["matrix"].copy(); M.columns = [f"at_{c}_standard" for c in GRP]
        add(f"Matrix {tag}", f"Belindia matrix, {tag}",
            f"Millions of people; rows are the economy's income group, columns the standard "
            f"its people live at. Lines: " +
            ", ".join(f"${x:.2f}" for x in r["lines"]) + f" ({note}).", M, index=True)

    # --- shares by group, for the two bar charts in the post
    def group_shares(r):
        M = r["matrix"]; rows = []
        for i, g in enumerate(GRP):
            v = M.loc[g]; t = v.sum()
            rows.append(dict(group=GRP_LONG[g], population=t, poorer=v.iloc[:i].sum() / t,
                             fits=v.iloc[i] / t, richer=v.iloc[i + 1:].sum() / t))
        s = r["summary"]
        rows.append(dict(group="World", population=s["total"], poorer=s["poorer_share"],
                         fits=s["fits_share"], richer=s["richer_share"]))
        return pd.DataFrame(rows)

    add("Shares 2025", "Share of each income group living at its own standard, 2025",
        "Poorer, fits and richer are shares of the group's population.", group_shares(r25))
    add("Shares 2026", "Share of each income group living at its own standard, 2026 nowcast",
        "Measured against the 2025 lines.", group_shares(r26f))

    # --- history
    hist, pooled, panels = history(df, z)
    add("History 1990-2026", "Label fit by year, 1990 to 2026",
        "fixed_* uses the 2025 lines; year_* re-estimates the lines each year; "
        "pooled_* uses lines estimated from all years at once: " +
        ", ".join(f"${x:.2f}" for x in pooled) + ".", hist)

    # --- skewness
    g = r25["country"][["group", "pop", "median", "mean", "gamma", "below_own_mean"]].copy()
    g.insert(0, "economy", [META.loc[i, "name"] for i in g.index])
    g["survey"] = [META.loc[i, "survey"] for i in g.index]
    g.index.name = "code"
    add("Skewness by economy", "Median over mean daily welfare (gamma), 2025",
        "gamma below one means the distribution is skewed to the right. "
        "below_own_mean is the share of an economy's people living below its own mean.",
        g.sort_values("gamma"), index=True)

    world = counterfactual_densities(r25["codes"], r25["W"], r25["cls"], r25["pop"])
    add("World distribution 2025", "Density of daily welfare across the world, 2025",
        f"World mean ${world.attrs['world_mean']:.2f} a day; "
        f"{100 * world.attrs['below_mean']['actual']:.0f}% of people live below it. "
        "The two counterfactual columns remove one kind of inequality at a time.", world)

    curves = pd.DataFrame({"welfare": np.exp(MID)} |
                          {GRP_LONG[c]: v for c, v in
                           group_curves(shares_below_grid(r25["W"]), r25["cls"],
                                        r25["pop"]).items()})
    add("Group curves 2025", "Welfare density of each income group's people, 2025",
        "Each curve integrates to one, so the groups are compared on shape, not size. "
        "The lines are where the highest curve changes hands.", curves)

    # --- robustness
    add("Check smoothing", "Annex 1a. Bandwidth and kernel shape",
        "Lines and shares re-derived under each smoothing choice, 2025.",
        check_smoothing(r25["W"], r25["cls"], r25["pop"]))
    add("Check giants", "Annex 1b. Large economies out of the curve estimation",
        "Excluded economies are still counted in the matrix, 2025.",
        check_giants(r25["codes"], r25["W"], r25["cls"], r25["pop"]))
    add("Check missing rich", "Annex 1c. Scaling up the top decile",
        "Welfare multiplied by a factor rising linearly from one at the 90th percentile "
        "to the stated value at the 100th, then the lines re-estimated.",
        check_missing_rich(r25["W"], r25["cls"], r25["pop"]))
    yard = check_yardsticks(hist, pooled)
    add("Check yardsticks", "Annex 1d. Fixed, yearly and pooled lines",
        "Pooled lines: " + ", ".join(f"${x:.2f}" for x in pooled) + ".", yard)
    ic = check_income_consumption(r25["codes"], r25["W"], r25["cls"], r25["pop"])
    add("Check survey type", "Annex 1e. Income versus consumption surveys",
        "Income distributions compressed towards their median to mimic a consumption "
        "survey. Lines from consumption economies only: " +
        ", ".join(f"${x:.2f}" for x in ic.attrs["lines_consumption_only"]) +
        "; from income economies only: " +
        ", ".join(f"${x:.2f}" for x in ic.attrs["lines_income_only"]) + ".", ic)

    # --- decomposition and sources
    dec = decomposition(panels)
    add("Inequality decomposition", "Mean log deviation split into three levels",
        "between_income_groups is what the classification captures by construction; "
        "the other two terms are what it cannot see.", dec)
    src = off_diagonal_sources(r25["W"], r25["cls"], r25["pop"], z)
    add("Off-diagonal sources", "Where the off-diagonal comes from",
        f"{src.attrs['mean_outside_band']['economies']} economies holding "
        f"{src.attrs['mean_outside_band']['population'] / 1000:.2f}bn people have a mean "
        f"outside their own group's band. Group means: " +
        ", ".join(f"{k} ${v:.2f}" for k, v in src.attrs["group_means"].items()) + ".", src)

    # --- threshold translation
    tt, scatter = threshold_translation(r25["codes"], r25["W"], r25["cls"], r25["pop"])
    add("Threshold translation", "Annex 1. Converting the GNI thresholds instead",
        "rho is an economy's 2025 mean or median welfare times 365 over its 2025 Atlas GNI "
        "per capita, taken as the median across economies within a factor of the window "
        "of each threshold. Thresholds: $1,175, $4,635, $14,375.", tt)
    add("Rho by economy", "Survey welfare as a share of GNI per capita, 2025",
        "Only the 166 economies with both a survey and a 2025 Atlas GNI figure.", scatter)

    # --- country tables
    add("Country results", "Annex 2. Every economy, by UN region and subregion",
        "at_L to at_H are the shares of the economy's population living at each standard "
        "in 2025; the 1990 and 2026 columns repeat the exercise for those years.",
        country_table(r25, r90, r26), index=True)

    write_outputs()


if __name__ == "__main__":
    main()
