More than money can explain: Social Progress Index relative to income, by region (2025)
movingfrontiers.substack.com/more-than-money-can-explain

Each chart comes as a PNG, a CSV with the plotted data, and a .py that regenerates the PNG and CSV with no other files:
it embeds the data, the Moving Frontiers house style and the fonts. Needs only numpy, pandas, matplotlib and Pillow.

01 Asia-Pacific, 02 Arab States, 03 Eastern Europe and Central Asia, 04 Europe and North America,
05 Latin America and the Caribbean, 06 Sub-Saharan Africa.
spi-vs-income-all-countries.csv: all 165 countries with their region, GDP per capita, SPI, predicted SPI and gap.

Method: the predicted score comes from a regression of the 2025 SPI on log GDP per capita (2021 PPP) across all 165 ranked
countries with GDP data (R-squared 0.83). The gap is the actual score minus the predicted score.
Source: Social Progress Imperative, 2026 Global Social Progress Index.
Fonts: Liberation Sans and Carlito (Latin subsets), SIL Open Font License.
