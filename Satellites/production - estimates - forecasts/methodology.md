# IEA Forecast Document Methodology

In general, the data closely follows the forecasts from the IEA Coal 2024: Analysis and forecast to 2027. The document is not detailed enough, so in some cases, approximation or utilisation of other data sources, such as US EIA, was necessary. The main assumptions were the following:
- Where possible, IEA 2024 data was included as a baseline
- Where the document assessed production as 'flat, ' this baseline was inserted for the next three years
- Where the document stated imprecisely small changes, a random walk data was generated to simulate noisy changes in production (China, Poland, Bulgaria, Czechia)
- Where IEA provided data for 2024 and 2027, the annual rate of change was assumed to be constant.
- Where there was no data for 2024, EIA data for 2023 was used with appropriate changes.

Due to limited granularity, the EU coal production was particularly challenging to decipher. Therefore, the following approach was followed:
1. The baseline data for 2023 was entered manually from EIA or calculated (Bulgaria, Czechia)
2. Annual rates of change were randomised for Poland, Bulgaria and Czechia (according to the assertion that they will remain in low single digits 1-6%)
3. These were used to calculate 2027 production. Then, using the forecasted EU production, the German 2027 production could be estimated.
4. Using the 2024 estimate as a baseline, remaining annual rates of change were calculated, and values for 2025 and 2026 were inputted.

For African countries, no change of production was assumed, with the notable exceptions of Mozambique and Zimbabwe. In the former, IEA suggests a minor increase due to the planned expansion of the Benga coking coal mine. In the latter, a nondescript increase in production is supposed to be caused by the increase in steel production in the region.
