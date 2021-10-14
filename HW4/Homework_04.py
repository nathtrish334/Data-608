import pandas as pd
import numpy as np
import dash
from dash import dcc,html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.graph_objects import Layout

'''
Records in the dataset:
API v2.1 (latest version) has no maximum value for the '$limit' query parameter
Hence to get the number of records in the dataset, you can set the limit value to a large value. I used the following to get the total number of rows.
(Note: This takes a while to run)

dataset = pd.read_json('https://data.cityofnewyork.us/resource/uvpi-gqnh.json?' + '&$limit=700000').replace(' ', '%20')
dataset.shape # This returns (683788, 45) implying the dataset has a total of 683788 rows
'''

'''
Retrieve data set of NYC trees through API call using Socrata query.
There are 5 levels of steward (including empty), 4 levels of health, 133 levels of spc_common (including empty string) and 5 boroughs. A single query could yield up to 5 * 4 * 133 * 5 = 13,300 results from this query.
'''

soql_url = ('https://data.cityofnewyork.us/resource/uvpi-gqnh.json?' +\
                '$select=spc_common,borocode,health,steward,count(tree_id)' +\
                        '&$group=spc_common,borocode,health,steward' +\
                                '&$limit=14000').replace(' ', '%20')

df = pd.read_json(soql_url)
# Remove rows that do not have complete data.
df = df.dropna(axis=0, how='any')
# Preview
df.head(5)

'''
Output for Question 1
=====================
Proportions will be shown in bar graphs grouped by boroughs for each health status.
'''

# Data for question 1:
totals_df = df.groupby(['borocode', 'spc_common'])['count_tree_id'].sum()
totals_df_by_borocode_species_health = df.groupby(['borocode', 'spc_common', 'health'])['count_tree_id'].sum()
totals_df = totals_df.reset_index(drop=False)
totals_df_by_borocode_species_health = totals_df_by_borocode_species_health.reset_index(drop=False)
totals_df.columns = ['borocode', 'spc_common', 'total_for_species_in_borough']
totals_df_by_borocode_species_health.columns = ['borocode', 'spc_common', 'health', 'total']
tree_species_proportions_df = pd.merge(totals_df_by_borocode_species_health, totals_df, on=['borocode', 'spc_common'])
tree_species_proportions_df['ratio'] = tree_species_proportions_df['total'] / tree_species_proportions_df['total_for_species_in_borough']
tree_species_proportions_df['spc_common'] = tree_species_proportions_df['spc_common'].apply(lambda x: x.title())

print(tree_species_proportions_df.head(5))

species = np.sort(tree_species_proportions_df.spc_common.unique()) # To be used for species dropdown:

'''
Output for Question 2
=====================
A scatter plot will represent the overall health status of the selected species for boroughs. 
Overall Health index is the numeric value of each health level (Poor=1, Fair=2, Good=3) 
obtained by calculating a weighted average for the selected species for each borough.
'''
# Data for question 2:
totals_df_by_steward = df.groupby(['borocode', 'spc_common', 'steward'])['count_tree_id'].sum()
totals_df_by_steward = totals_df_by_steward.reset_index(drop=False)
totals_df_by_steward.columns = ['borocode', 'spc_common', 'steward', 'steward_total']
df['borocode'] = pd.to_numeric(df['borocode'])
stewards_df = pd.merge(df, totals_df_by_steward, on=['borocode', 'spc_common', 'steward'])
di = {'Poor':1, 'Fair':2, 'Good':3}
stewards_df['health_level'] = stewards_df['health'].map(di)
stewards_df['health_index'] = (stewards_df['count_tree_id'] / stewards_df['steward_total']) * stewards_df['health_level']

overall_health_index_df = stewards_df.groupby(['borocode', 'spc_common', 'steward'])['health_index'].sum()
overall_health_index_df = overall_health_index_df.reset_index(drop=False)
overall_health_index_df.columns = ['borocode', 'spc_common', 'steward', 'overall_health_index']
di2 = {'3or4':3, '4orMore':4, 'None':1, '1or2':2}
overall_health_index_df['steward_level'] = overall_health_index_df['steward'].map(di2)
di3 = { 1:'Manhattan', 2:'Bronx', 3:'Brooklyn', 4:'Queens', 5:'Staten Island'}
overall_health_index_df['borough'] = overall_health_index_df['borocode'].map(di3)
overall_health_index_df['spc_common'] = overall_health_index_df['spc_common'].apply(lambda x: x.title())

#Preview
print(overall_health_index_df.head(5))

####################
# Dash Application #
####################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    html.H1(
        children='Question 1',
        style={
            'textAlign': 'center'
        }
    ),

    html.Div(children='Proportion of trees in Good, Fair and Poor conditions', style={
        'textAlign': 'center'
    }),
    html.H4('Choose a Tree Species'),
    
    dcc.Dropdown(
        id='species', 
        options=[{'label': i, 'value': i} for i in species],
        value="American Beech",
        style={'height': 'auto', 'width': '300px'}
    ),

    html.Div([
        dcc.Graph(id='graph_q1')]),

    html.H1(
        children='Question 2',
        style={
            'textAlign': 'center'
        }
    ),
    html.Div(children='Correlation between Stewards and Health of Trees', style={
        'textAlign': 'center'
    }),
    html.Div([
        dcc.Graph(id='graph_q2')]),

    ], style={'columnCount': 1,'backgroundColor':'#3da118'})

# Callback for Proportion Graph - Question 1
@app.callback(
    Output('graph_q1', 'figure'),
    [Input('species', 'value')])
def update_figure(selected_species):

    filtered_df = tree_species_proportions_df[tree_species_proportions_df.spc_common == selected_species]
    #borocode: 1 (Manhattan), 2 (Bronx), 3 (Brooklyn), 4 (Queens), 5 (Staten Island)
    manhattan = filtered_df[filtered_df.borocode == 1]
    bronx = filtered_df[filtered_df.borocode == 2]
    brooklyn = filtered_df[filtered_df.borocode == 3]
    queens = filtered_df[filtered_df.borocode == 4]
    staten_island = filtered_df[filtered_df.borocode == 5]
    
    traces = []

    traces.append(go.Bar(
    x=queens['health'],
    y=queens['ratio'],
    name='Queens',
    opacity=0.9
    ))

    traces.append(go.Bar(
    x=manhattan['health'],
    y=manhattan['ratio'],
    name='Manhattan',
    opacity=0.9
    ))

    traces.append(go.Bar(
    x=bronx['health'],
    y=bronx['ratio'],
    name='Bronx',
    opacity=0.9
    ))

    traces.append(go.Bar(
    x=brooklyn['health'],
    y=brooklyn['ratio'],
    name='Brooklyn',
    opacity=0.9
    ))

    traces.append(go.Bar(
    x=staten_island['health'],
    y=staten_island['ratio'],
    name='Staten Island',
    opacity=0.9
    ))
    
    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'title': 'Health of Tree Species'},
            yaxis={'title': 'Proportion of Trees in Borough'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend=dict(x=-.1, y=1.2),
            paper_bgcolor='rgb(231, 240, 187)',
            plot_bgcolor='rgb(247, 215, 195)'
        )
    }


# Callback for Steward-Health Graph - Question 2
@app.callback(
    Output('graph_q2', 'figure'),
    [Input('species', 'value')])
def update_figure2(selected_species):
    #print('here: ' + selected_species)
    filtered_df = overall_health_index_df[overall_health_index_df.spc_common == selected_species]
    traces2 = []
        
    for i in filtered_df.borough.unique():
        df_by_borough = filtered_df[filtered_df['borough'] == i]
        traces2.append(go.Scatter(
            x=df_by_borough['steward_level'],
            y=df_by_borough['overall_health_index'],
            mode='markers',
            opacity=0.7,
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=i
        ))
    
    return {
        'data': traces2,
        'layout': go.Layout(
            yaxis={'title': 'Overall Health Index'},
            xaxis=dict(tickvals = [1,2,3,4], ticktext = ['None', '1or2', '3or4', '4orMore'], title='Steward'),
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend=dict(x=-.1, y=1.2),
            paper_bgcolor='rgb(231, 240, 187)',
            plot_bgcolor='rgb(247, 215, 195)'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
