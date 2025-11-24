import pandas as pd
import pycountry


iea = pd.read_csv("rankings and ranges/data/iea_emissions.csv")
unfccc = pd.read_csv("rankings and ranges/data/unfccc_raw.csv")
filters = pd.read_csv("rankings and ranges/data/filters.csv")
unfccc_non_annex = pd.read_csv("rankings and ranges/data/unfccc_non_annex.csv")
filters_columns = ['Code', 'EU Member', 'GMP', 'APAC', 'OECD', 'AME', 'G20', 'G7']

iea = iea[['Country','Segment','Collection Year','Emissions']]
iea['Emissions'] = iea['Emissions'].str.replace(",", "").astype(float)
iea_coal = iea[iea['Segment'].str.contains('coal', case=False, na=False)]

#Sum values for each year
iea_result = iea_coal.groupby(['Country','Collection Year'])['Emissions'].sum().reset_index()
iea_result_pivot = iea_result.pivot(index="Country", columns="Collection Year", values="Emissions")
iea_result_pivot = iea_result_pivot.reset_index()

def get_country_code(country):
    try:
        return pycountry.countries.lookup(country).alpha_3
    except LookupError:
        if country == "Korea":
            return 'KOR'
        elif country == "Russia":
            return 'RUS'
        elif country == "Brunei":
            return 'BRN'
        else:
            return None


iea_result_pivot['Code'] = iea_result_pivot['Country'].apply(get_country_code)
print(iea_result_pivot)

unfccc = unfccc.drop(['Category'], axis=1)
unfccc['Ch4 Kt'] = unfccc['Ch4 Kt'].str.replace(",", "").astype(float)
unfccc = unfccc.drop_duplicates(subset=['Country', 'Year'])
unfccc.set_index('Year')
unfccc = unfccc[unfccc['Year'] != 'Base year']
unfccc['Year_backup'] = unfccc['Year']
unfccc['Year'] = unfccc['Year'].str.extract(r'\((.*?)\)')
unfccc['Year'] = unfccc['Year'].fillna(unfccc['Year_backup'])
unfccc = unfccc.drop(['Year_backup'], axis=1)

def get_first_valid(group, column, order="asc"):
    sorted_group = group.sort_values(by="Year", ascending=(order == "asc"))
    valid_values = sorted_group.dropna(subset=[column])
    if not valid_values.empty:
        return valid_values.iloc[0]
    return pd.Series({"Year": None, column: None, "Country": group["Country"].iloc[0]})

oldest_records = unfccc.groupby("Country").apply(lambda g: get_first_valid(g, "Ch4 Kt", "asc")).reset_index(drop=True)
most_recent_records = unfccc.groupby("Country").apply(lambda g: get_first_valid(g, "Ch4 Kt", "desc")).reset_index(drop=True)

unfccc_pivot = oldest_records.merge(
    most_recent_records, on="Country", suffixes=("_Oldest", "_Most_Recent")
)

unfccc.duplicated(subset=["Country", "Year"]).sum()

## 1: UNFCCC Last Reported Year Ranking (Annex I Countries)
unfccc_ranking = unfccc_pivot.merge(filters, how='left', on='Country')
unfccc_ranking.columns = unfccc_ranking.columns.str.strip()
unfccc_clean = unfccc_ranking
selected_columns = ["Country", "Year_Oldest", "Ch4 Kt_Oldest", "Year_Most_Recent", "Ch4 Kt_Most_Recent"] + filters_columns
unfccc_ranking = unfccc_ranking[selected_columns]


## 2: UNFCCC Last Reported Year Ranking (Non-Annex I Countries)
unfccc_non_annex.set_index("Country")
unfccc_non_annex = unfccc_non_annex.T
unfccc_non_annex.columns = unfccc_non_annex.iloc[0]  # Set the first row as the header
unfccc_non_annex = unfccc_non_annex.drop(unfccc_non_annex.index[0])

# Get oldest and most recent values and years for Non-Annex I countries
oldest_records = {}
most_recent_records = {}
oldest_years = {}
most_recent_years = {}

for country in unfccc_non_annex.columns:
    oldest_value = unfccc_non_annex[country].first_valid_index()
    most_recent_value = unfccc_non_annex[country].last_valid_index()
    
    if pd.notna(oldest_value) and pd.notna(most_recent_value):
        oldest_records[country] = unfccc_non_annex.loc[oldest_value, country]
        most_recent_records[country] = unfccc_non_annex.loc[most_recent_value, country]
        oldest_years[country] = oldest_value
        most_recent_years[country] = most_recent_value
    else:
        oldest_records[country] = None
        most_recent_records[country] = None
        oldest_years[country] = None
        most_recent_years[country] = None

unfccc_non_annex = pd.DataFrame({
    'Country': unfccc_non_annex.columns,
    'Ch4 Kt_Oldest': [oldest_records[country] for country in unfccc_non_annex.columns],
    'Year_Oldest': [oldest_years[country] for country in unfccc_non_annex.columns],
    'Ch4 Kt_Most_Recent': [most_recent_records[country] for country in unfccc_non_annex.columns],
    'Year_Most_Recent': [most_recent_years[country] for country in unfccc_non_annex.columns]
})

unfccc_ranking_na = unfccc_non_annex.merge(filters, how='left', on='Country')
unfccc_ranking_na = unfccc_ranking_na.drop(columns=['Unnamed: 0'])

unfccc_ranking_combined = pd.concat([unfccc_ranking, unfccc_ranking_na], ignore_index=True)
columns_to_convert = ['Ch4 Kt_Oldest', 'Ch4 Kt_Most_Recent']
unfccc_ranking_combined[columns_to_convert] = unfccc_ranking_combined[columns_to_convert].apply(pd.to_numeric, errors='coerce')
unfccc_ranking_final = unfccc_ranking_combined.sort_values(by='Ch4 Kt_Most_Recent', ascending=False)
unfccc_ranking_final.to_csv("rankings and ranges/output/unfccc_output.csv")


## 3: IEA 2023 Estimate Ranking
iea_ranking = iea_result_pivot.merge(filters, how='left', on='Country')
iea_ranking = iea_ranking.sort_values(by=2023, ignore_index=True, ascending=False) ## error here on the column??
iea_ranking= iea_ranking.drop(columns=['Unnamed: 0'])
iea_ranking.to_csv('rankings and ranges/output/iea_ranking.csv')

result_summary = unfccc_ranking_final.merge(iea_result_pivot, how='outer', on='Code')
result_summary['Country_x'] = result_summary['Country_x'].fillna(result_summary['Country_y'])
result_summary = result_summary.dropna(subset=['Code'])
result_summary = result_summary[['Country_x','Code', 'Ch4 Kt_Most_Recent', 'Year_Most_Recent' ,2022,2023]]
result_summary = result_summary.rename(columns={'Country_x': 'Country','Ch4 Kt_Most_Recent':'UNFCCC', 'Year_Most_Recent' : 'Year_UNFCCC', 2022 : 'IEA (2022)', 2023 : 'IEA (2023)'})

## 4: Add Science Studies
tropomi = pd.read_csv("rankings and ranges/data/tropomi_raw.csv")
tropomi = tropomi.dropna(subset=['Country Code'])
tropomi = tropomi[['Country Name','Country Code', 'Coal Tropomi2']]
tropomi = tropomi.rename(columns = {'Country Name':'Country', 'Country Code':'Code', 'Coal Tropomi2' : 'Shen et. al. (2018-2020)'})
result_summary = result_summary.merge(tropomi, how='outer', on='Code')
result_summary['Country_x'] = result_summary['Country_x'].fillna(result_summary['Country_y'])
result_summary = result_summary.rename(columns={'Country_x': 'Country'})
result_summary = result_summary.drop(columns='Country_y')
result_summary.to_csv('rankings and ranges/output/ranges.csv')