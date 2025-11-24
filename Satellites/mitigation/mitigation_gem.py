import pandas as pd
import numpy as np
import pycountry

GEM = pd.read_excel('data/GEM.xlsx', sheet_name=1)

GEM = GEM[['Country','GEM Mine ID','Coal Grade','GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)']]

GEM = GEM[GEM['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'] != '-']
GEM['Total Emissions by Country'] = GEM.groupby('Country')['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].transform('sum')

GEM['Share of Country Emissions (%)'] = GEM.apply(
    lambda row: (row['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'] / row['Total Emissions by Country']) * 100 
    if row['Total Emissions by Country'] != 0 else 0, 
    axis=1
)

GEM = GEM.sort_values(by=['Country', 'GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'], ascending=[True, False])
GEM['Rank within Country'] = GEM.groupby('Country')['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].rank(method='first', ascending=False).astype(int)
GEM['Global rank'] = GEM['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].rank(method='min', ascending=False)

GEM_gassy = GEM[GEM['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)']>0]
num_mines_per_country = GEM_gassy['Country'].value_counts().reset_index()
num_mines_per_country.columns = ['Country', 'Number of Mines']
num_mines_per_country["Top 10%"] = np.rint(num_mines_per_country['Number of Mines']*0.1)
num_mines_per_country["Top 10"] = 10

top_10_percent_emissions = GEM.merge(num_mines_per_country, on='Country', how='left').groupby('Country').apply(
    lambda x: x.loc[x['Rank within Country'] <= x['Top 10%'], 'GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].sum()
).reset_index(name="Top 10% Emissions")

top_10_emissions = GEM.merge(num_mines_per_country, on='Country', how='left').groupby('Country').apply(
   lambda x: x.loc[x['Rank within Country'] <= x["Top 10"], 'GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].sum()
).reset_index(name="Top 10 Emissions")

#Country data
GEM_analysis = GEM.groupby('Country')['GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)'].sum()
analysis = num_mines_per_country.merge(top_10_percent_emissions, on='Country', how='left')
analysis = analysis.merge(top_10_emissions, on='Country', how='left')
analysis = analysis.merge(GEM_analysis, on='Country', how = 'left')
analysis['Top 10% Mitigation Share'] = (analysis["Top 10% Emissions"] / analysis["GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)"]) * 100
analysis['Top 10 Mitigation Share'] = (analysis["Top 10 Emissions"] / analysis["GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)"]) * 100
mitigation_1 = analysis[['Country', 'Number of Mines', 'Top 10%', 'Top 10% Mitigation Share', 'Top 10 Mitigation Share', 'GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)']]

mitigation_1.to_csv('mitigation.csv')

#Slider

##get country codes
def get_country_code(country):
    try:
        return pycountry.countries.lookup(country).alpha_3
    except LookupError:
        if country == "Republic of Korea":
            return 'KOR'
        elif country == "Russia":
            return 'RUS'
        else:
            return None  

analysis = analysis.rename(columns={'GEM Coal Mine Methane Emissions Estimate (M tonnes/yr)':'GEM Estimate Total (M tonnes/yr)'})
country_sum = analysis[['Country',"GEM Estimate Total (M tonnes/yr)"]]
country_sum['Code'] = country_sum['Country'].apply(get_country_code)

slider_dataset = GEM
slider_dataset['Code'] = slider_dataset['Country'].apply(get_country_code)


slider_dataset.to_csv('output for google/slider.csv')
country_sum.to_csv('output for google/country_sum.csv')