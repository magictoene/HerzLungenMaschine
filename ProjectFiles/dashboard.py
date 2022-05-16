from cmath import nan
from tempfile import SpooledTemporaryFile
import dash
from dash import Dash, html, dcc, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import utilities as ut
import numpy as np
import os
import re

app = Dash(__name__)


list_of_subjects = []
subj_numbers = []
number_of_subjects = 0
file_extension = ''

file_extension = 'csv'
file_paths = ut.get_Path(file_extension) # Get filepaths of every .csv file in input_data

for i in file_paths:
	list_of_subjects.append(ut.Subject(i)) # Create object of class Subject 
	number_of_subjects += 1

df = list_of_subjects[0].subject_data # Default value shown on dashboard (Subject 1)


for i in range(number_of_subjects):
    subj_numbers.append(list_of_subjects[i].subject_id)


data_names = ["SpO2 (%)", "Blood Flow (ml/s)","Temp (C)"]
algorithm_names = ['min','max']
blood_flow_functions = ['CMA','SMA','Show Limits']


fig0= go.Figure()
fig1= go.Figure()
fig2= go.Figure()
fig3= go.Figure()

fig0 = px.line(df, x="Time (s)", y = data_names[0]) #Sp02 (%)
fig1 = px.line(df, x="Time (s)", y = data_names[1]) #Blood Flow (ml/s)
fig2 = px.line(df, x="Time (s)", y = data_names[2]) #Temp (C)
fig3 = px.line(df, x="Time (s)", y = data_names[1]) #Blood Flow (ml/s)

app.layout = html.Div(children=[
    html.H1(children='Cardiopulmonary Bypass Dashboard'),

    html.Div(children='''
        Hier könnten Informationen zum Patienten stehen....
    '''),

    dcc.Checklist(
    id= 'checklist-algo',
    options=algorithm_names,
    inline=False
    ),

    html.Div([
        dcc.Dropdown(options = subj_numbers, placeholder='Select a subject', value='1', id='subject-dropdown'),
    html.Div(id='dd-output-container')
    ],
        style={"width": "15%"}
    ),

    dcc.Graph(
        id='dash-graph0',
        figure=fig0
    ),

    dcc.Graph(
        id='dash-graph1',
        figure=fig1
    ),
    dcc.Graph(
        id='dash-graph2',
        figure=fig2
    ),

    dcc.Checklist(
        id= 'checklist-bloodflow',
        options=blood_flow_functions,
        inline=False
    ),
    dcc.Graph(
        id='dash-graph3',
        figure=fig3
    )
])


### Callback Functions ###
## Graph Update Callback
@app.callback(
    # In- or Output('which html element','which element property')
    Output('dash-graph0', 'figure'),
    Output('dash-graph1', 'figure'),
    Output('dash-graph2', 'figure'),
    Input('subject-dropdown', 'value'),
    Input('checklist-algo','value')
)
def update_figure(value, algorithm_checkmarks):
    
    if value == None:
        value = subj_numbers[0]
    
    print("Current Subject: ",value)
    print("current checked checkmarks are: ", algorithm_checkmarks)

    ts = list_of_subjects[int(value)-1].subject_data
    #SpO2
    fig0 = px.line(ts, x="Time (s)", y = data_names[0])
    # Blood Flow
    fig1 = px.line(ts, x="Time (s)", y = data_names[1])
    # Blood Temperature
    fig2 = px.line(ts, x="Time (s)", y = data_names[2])
    
    ### Aufgabe 2: Min / Max ###

    grp = ts.agg(['max', 'min', 'idxmin', 'idxmax'])

    #print(max_values)
    #print(min_values)

    
    if algorithm_checkmarks is not None: #Checking if it is not None, otherwise it would iterate over NoneType Object = not possible

        if 'min' in algorithm_checkmarks:

            fig0.add_trace(go.Scatter(x=[grp.loc['idxmin', data_names[0]]], y=[grp.loc['min', data_names[0]]], mode ='markers', name='Mininum', marker_color='black'))
            fig1.add_trace(go.Scatter(x=[grp.loc['idxmin', data_names[1]]], y=[grp.loc['min', data_names[1]]], mode ='markers', name='Mininum', marker_color='black'))
            fig2.add_trace(go.Scatter(x=[grp.loc['idxmin', data_names[2]]], y=[grp.loc['min', data_names[2]]], mode ='markers', name='Mininum', marker_color='black'))

        
        if 'max' in algorithm_checkmarks:

            fig0.add_trace(go.Scatter(x=[grp.loc['idxmax', data_names[0]]], y=[grp.loc['max', data_names[0]]], mode ='markers', name='Maximum', marker_color='red'))
            fig1.add_trace(go.Scatter(x=[grp.loc['idxmax', data_names[1]]], y=[grp.loc['max', data_names[1]]], mode ='markers', name='Maximum', marker_color='red'))
            fig2.add_trace(go.Scatter(x=[grp.loc['idxmax', data_names[2]]], y=[grp.loc['max', data_names[2]]], mode ='markers', name='Maximum', marker_color='red'))

    
    return fig0, fig1, fig2 

## Blodflow Simple Moving Average Update
@app.callback(
    # In- or Output('which html element','which element property')
    Output('dash-graph3', 'figure'),
    Input('subject-dropdown', 'value'),
    Input('checklist-bloodflow','value')
)
def bloodflow_figure(value, bloodflow_checkmarks):

    if value == None:
        value = subj_numbers[0]

    ## Calculate Moving Average: Aufgabe 2
    print(bloodflow_checkmarks)

    bf = list_of_subjects[int(value)-1].subject_data
    fig3 = px.line(bf, x="Time (s)", y= data_names[1])


    return fig3

if __name__ == '__main__':
    app.run_server(debug=True)