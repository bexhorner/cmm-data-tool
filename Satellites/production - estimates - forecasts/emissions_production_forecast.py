import pandas as pd
import pycountry
import requests


## Make API Call on EIA Data. Production data in Thousand Metric Tonnes
def clean_eia_api(url):
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data["response"]["data"])
    output = df[['period', 'countryRegionId', 'countryRegionName', 'value']]
    output = output.rename(columns={
        "period": "Year",
        "countryRegionId": "Code",
        "countryRegionName": "Country",
        "value": "Production"
    })
    
    output["Data_Type"] = "EIA Production Report"
    output['Production'] = pd.to_numeric(output['Production'], errors='coerce')
    df_cleaned = output.groupby('Country').filter(lambda x: (x['Production'] > 0).any())
    output = df_cleaned
    return output

url1 = "https://api.eia.gov/v2/international/data/?api_key=d4KldYENRqkz03BmNuPj8b7X2a5xelGCWAnxfc1U&frequency=annual&data[0]=value&facets[activityId][]=1&facets[productId][]=7&facets[unit][]=MT&facets[countryRegionTypeId][]=c&start=2000&sort[0][column]=countryRegionId&sort[0][direction]=asc&offset=0&length=5000"
url2 = "https://api.eia.gov/v2/international/data/?api_key=d4KldYENRqkz03BmNuPj8b7X2a5xelGCWAnxfc1U&frequency=annual&data[0]=value&facets[activityId][]=1&facets[productId][]=7&facets[unit][]=MT&facets[countryRegionTypeId][]=c&start=1990&end=2000&sort[0][column]=countryRegionId&sort[0][direction]=asc&offset=0&length=5000"

production_1991 = clean_eia_api(url2)
production_2001 = clean_eia_api(url1)
frames = [production_1991, production_2001]
production = pd.concat(frames)
production = production.sort_values(by=['Code', 'Year'])

#Load secondary datasets
unfccc_a = pd.read_csv("data/unfccc_raw.csv")
unfccc_na = pd.read_csv("data/unfccc_non_annex.csv")
forecast = pd.read_csv("data/forecast.csv")
forecast["Data_Type"] = "IEA Forecast"

##clean
unfccc_a_clean = unfccc_a.drop_duplicates()
unfccc_a_clean = unfccc_a_clean.copy()
unfccc_a_clean.loc[:, 'Ch4 Kt'] = unfccc_a_clean['Ch4 Kt'].replace({',': ''}, regex=True).astype(float)
unfccc_a_clean.loc[pd.notna(unfccc_a_clean['Ch4 Kt']), 'Ch4 Kt'] = unfccc_a_clean.loc[pd.notna(unfccc_a_clean['Ch4 Kt']), 'Ch4 Kt'].astype(float)
unfccc_a_grouped = unfccc_a_clean.groupby(['Year', 'Country'], as_index=False)['Ch4 Kt'].sum()

##convert to long and append
unfccc_na_long = pd.melt(unfccc_na, id_vars=['Country'], var_name='Year', value_name='Ch4 Kt')
frames = [unfccc_na_long, unfccc_a_grouped]
unfccc = pd.concat(frames)
unfccc = unfccc[unfccc['Year'] != 'Base year']
unfccc['Year_backup'] = unfccc['Year']
unfccc['Year'] = unfccc['Year'].str.extract(r'\((.*?)\)')
unfccc['Year'] = unfccc['Year'].fillna(unfccc['Year_backup'])
unfccc = unfccc.drop(['Year_backup'], axis=1)

##append production and forecast
frames = [production, forecast]
production = pd.concat(frames)
production.reset_index(drop=True)

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


unfccc['Code'] = unfccc['Country'].apply(get_country_code)

def get_country_name(code):
    country = pycountry.countries.get(alpha_3=code)
    return country.name if country else "Unknown"

production['Country'] = production['Code'].apply(get_country_name)

#Merge Production and Emissions
production.loc[pd.notna(production['Year']), 'Year'] = production.loc[pd.notna(production['Year']), 'Year'].astype(int)
unfccc.loc[pd.notna(unfccc['Year']), 'Year'] = unfccc.loc[pd.notna(unfccc['Year']), 'Year'].astype(int)
merge = production.merge(unfccc, on=['Year','Code'], how='left')
merge = merge[(merge['Production'] != 0) & (merge['Production'].notna())]
merge = merge.drop(columns=['Country_y'])
merge = merge.rename(columns={"Country_x":"Country"})

merge_filtered = merge.dropna(subset=['Production', 'Ch4 Kt'])
merge_filtered = merge_filtered.copy()
merge_filtered['Production'] = pd.to_numeric(merge_filtered['Production'], errors='coerce')
merge_filtered['Intensity'] = merge_filtered['Ch4 Kt'] / merge_filtered['Production']
result_merge = merge_filtered[['Code', 'Year', 'Intensity']]


calculation = merge.merge(result_merge, on=['Year', 'Code'], how='left')
calculation['Intensity'] = pd.to_numeric(calculation['Intensity'], errors='coerce')
calculation['Production'] = pd.to_numeric(calculation['Production'], errors='coerce')

def calculate_estimate(df):
    # Loop through the rows
    for idx, row in df[df['Ch4 Kt'].isna() & df['Production'].notna()].iterrows():
        country_code = row['Code']
        year = row['Year']
        production = row['Production']

        # Filter data for the same country and find the most recent valid intensity
        recent_intensity = df[(df['Code'] == country_code) &
                               (df['Year'] < year) &
                               (df['Intensity'].notna())]['Intensity'].max()
        
        # If a valid intensity exists, calculate the estimate
        if pd.notna(recent_intensity):
            df.at[idx, 'Estimate'] = production * recent_intensity
        else:
            df.at[idx, 'Estimate'] = None  # Keep NaN if no valid intensity is found
    
    return df

calculation = calculate_estimate(calculation)
calculation = calculation.sort_values(by=['Code', 'Year'])

calculation.to_csv('final_output.csv')
