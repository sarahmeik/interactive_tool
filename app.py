import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib.colors as mplcolors
import pandas as pd
import numpy as np
import streamlit as st

original_efficiency_factor = 0.5

# create and insert sliders into sidebar
st.sidebar.image('https://mlombw7jtauz.i.optimole.com/cb:i-DS~f076/w:auto/h:auto/q:mauto/https://www.metabolic.nl/wp-content/uploads/2022/10/Metabolic_Logo_2022.png', caption=None, width=50, use_column_width=None, clamp=False, channels='RGB', output_format='auto')
factor = st.sidebar.slider("Efficiency Factor", 0.0, 1.0, 0.5)
st.sidebar.write(factor)

xls = pd.ExcelFile('data.xlsx')
input_data = pd.read_excel(xls, 'input_to_sector')
output_data = pd.read_excel(xls, 'sector_to_output')

# manipulate the output_data df to create two dfs that work with the mfa
output_data_grouped = output_data.groupby(['sector', 'output']).sum()
output_data_grouped = output_data_grouped.reset_index()

output_data_separate = output_data.dropna().reset_index(drop=True)
output_data_separate = output_data_separate.dropna(how='any')
output_data_separate = output_data_separate.drop('sector', axis=1)

# rename columns appropriately
input_data.columns = ['source','target','value']
output_data_grouped.columns = ['source','target','value']
output_data_separate.columns = ['source','target','value']

# create df of links
links = pd.concat([input_data, output_data_grouped, output_data_separate], axis=0)

# find all unique values in source and target columns
unique_source_target = list(pd.unique(links[['source','target']].values.ravel('k')))

# create a mapping dictionary
mapping_dict = {k: v for v, k in enumerate(unique_source_target)}

# map values to the links df
links['source'] = links['source'].map(mapping_dict)
links['target'] = links['target'].map(mapping_dict)
links['value'] = links['value'] * factor

# convert df to dictionary
links_dict = links.to_dict(orient='list')

# create MFA
fig_mfa = go.Figure(data=[go.Sankey(
    node = dict(
        pad = 15,
        thickness=20,
        line=dict(color='black', width=0.5),
        label = unique_source_target,
        color='green'
    ),
    link = dict(
        source= links_dict['source'],
        target = links_dict['target'],
        value = links_dict['value']
    )

)
])

# input emission data
gov_emissions_df = pd.DataFrame({
    'type': 'input',
    'source': input_data.loc[input_data['target'] == 'government', 'source'],   
    'emissions': input_data.loc[input_data['target'] == 'government', 'value'] * original_efficiency_factor,
})

# waste and output emission data
concat_df1 = pd.DataFrame({
    'source': output_data.loc[output_data['sector'] == 'government', 'output'],   
    'emissions': output_data.loc[output_data['sector'] == 'government', 'amount'] * original_efficiency_factor,
})

# change the 'type' label accordingly
concat_df1['type'] = np.where(concat_df1['source'] == 'cars', 'output', 'waste')
# concatenate the two dfs
gov_emissions_df = pd.concat([gov_emissions_df, concat_df1])
# add 'original' label to all original emissions before concatenating the modified ones
gov_emissions_df['emission_type'] = 'original'


# repeat the process for industry data
industry_emissions_df = pd.DataFrame({
    'type': 'input',
    'source': input_data.loc[input_data['target'] == 'industry', 'source'],   
    'emissions': input_data.loc[input_data['target'] == 'industry', 'value'] * original_efficiency_factor,
})

concat_df2 = pd.DataFrame({
    'source': output_data.loc[output_data['sector'] == 'industry', 'output'],   
    'emissions': output_data.loc[output_data['sector'] == 'industry', 'amount'] * original_efficiency_factor,
})

# change the 'type' label accordingly
concat_df2['type'] = np.where(concat_df2['source'] == 'cars', 'output', 'waste')
# concatenate the two dfs
industry_emissions_df = pd.concat([industry_emissions_df, concat_df2])
# add 'original' label to all original emissions before concatenating the modified ones
industry_emissions_df['emission_type'] = 'original'

# create new dataframe for the modified emissions
gov_modified_df = gov_emissions_df.assign(emissions=gov_emissions_df['emissions']* factor, emission_type='modified')
ind_modified_df = industry_emissions_df.assign(emissions=industry_emissions_df['emissions']* factor, emission_type='modified')

# concatenate the original and modified dataframes
gov_emissions_df = pd.concat([gov_emissions_df, gov_modified_df], ignore_index=True)
industry_emissions_df = pd.concat([industry_emissions_df, ind_modified_df], ignore_index=True)

# plot government emissions dataframe
fig_gov = px.histogram(gov_emissions_df, x="type", y="emissions",
             color='emission_type', barmode='group',
             histfunc='sum',
             height=400)

# plot industry emissions dataframe
fig_ind = px.histogram(industry_emissions_df, x="type", y="emissions",
             color='emission_type', barmode='group',
             histfunc='sum',
             height=400)

# create container for the MFA
with st.empty():
    st.write("MFA") # this isn't displaying for some reason??
    st.plotly_chart(fig_mfa, use_container_width=True)

# create columns for the bar graphs
col1, col2 = st.columns(2)

# insert government bar graph
with col1:
   st.write("Government Emissions") 
   st.plotly_chart(fig_gov, use_container_width=True)

# insert industry bar graph
with col2:
   st.write("Industry Emissions")
   st.plotly_chart(fig_ind, use_container_width=True)