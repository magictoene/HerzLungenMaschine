from cmath import nan
from tempfile import SpooledTemporaryFile
from tkinter import OFF
from turtle import width
from unicodedata import name
import dash
from dash import Dash, html, dcc, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pyparsing import And
from scipy.__config__ import show
import utilities as ut
import numpy as np
import os
import re

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#FAEBD7',
    'text': '#000000'
}

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

app.layout = html.Div(style={'backgroundColor': colors['background']},children=[
    html.H1(children='Cardiopulmonary Bypass Dashboard'),

    html.Div(children=''' Hier könnten Informationen zum Patienten stehen...''', style={
        'textAlign': 'center',
        'color': colors['text']
     }),

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

   html.Div([
       html.Div([
            dcc.Graph(
                 id='dash-graph0',
                 figure=fig0
            ),
       ], className='six columns'),

       html.Div([
            dcc.Graph(
                 id='dash-graph1',
                 figure=fig1
            ),
       ], className='six columns'),

    ], className='row'),

    html.Div([
            dcc.Graph(
                 id='dash-graph2',
                 figure=fig2,
                 style={"margin-top": "50px"}
            ),
       ], className='row'),
        

    dcc.Checklist(
        id= 'checklist-bloodflow',
        options=blood_flow_functions,
        inline=False
    ),

    dcc.Textarea(
        id='text-area1',
        #readOnly=True,
        disabled=True, #disabled --> User cannot interact with textarea
        style={"width": "100%", 'height': "auto"}
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

    fig_list = []
    
    #SpO2
    fig0 = px.line(ts, x="Time (s)", y = data_names[0])
    fig_list.append(fig0)
    # Blood Flow
    fig1 = px.line(ts, x="Time (s)", y = data_names[1])
    fig_list.append(fig1)
    # Blood Temperature
    fig2 = px.line(ts, x="Time (s)", y = data_names[2])
    fig_list.append(fig2)
    
    
    ### Aufgabe 2: Min / Max ###

    grp = ts.agg(['max', 'min', 'idxmin', 'idxmax'])


    if algorithm_checkmarks is not None: #Checking if it is not None, otherwise it would iterate over NoneType Object = not possible

        if 'min' in algorithm_checkmarks:

            for i in range(0,3):
                
                fig_list[i].add_trace(go.Scatter(x=[grp.loc['idxmin', data_names[i]]], y=[grp.loc['min', data_names[i]]], mode ='markers', name='Mininum', marker_color='black'))

        
        if 'max' in algorithm_checkmarks:

            for i in range(0,3):
                fig_list[i].add_trace(go.Scatter(x=[grp.loc['idxmax', data_names[i]]], y=[grp.loc['max', data_names[i]]], mode ='markers', name='Maximum', marker_color='red'))

    
    return fig0, fig1, fig2 

## Bloodflow Simple Moving Average Update
@app.callback(
    # In- or Output('which html element','which element property')
    Output('dash-graph3', 'figure'),
    Output('text-area1', 'value'), #Output textarea added for 
    Input('subject-dropdown', 'value'),
    Input('checklist-bloodflow','value')
)
def bloodflow_figure(value, bloodflow_checkmarks):

    if value == None: # if subject-dropdown is empty, then show subject 1 per default
        value = subj_numbers[0]

    ## Calculating frequently used values:
    bf = list_of_subjects[int(value)-1].subject_data
    fig3 = px.line(bf, x="Time (s)", y= data_names[1])  

    #Mean value 
    avg = bf.mean() #calculate average values for all columns of subject data
    x = [0, 480] #set boundaries for x values (required later to depict mean value)
    y = avg[data_names[1]] #mean value of Blood Flow (ml/s)

    # Calculating upper and lower limit
    y_oben = y*1.15 # 115% of blood flow mean value
    y_unten = y*0.85 # 85% of blood flow mean value

    #call utilities function to calculate Cumulative Moving Average
    bf["Blood Flow (ml/s) - SMA"] = ut.calculate_SMA(bf[data_names[1]],4) 
    bf_SMA =  bf["Blood Flow (ml/s) - SMA"]


    ## Aufgabe 2 bzw. 3
    def show_limits(fig):

        fig.add_trace(go.Scatter(x = x, y = [y_oben, y_oben], mode = 'lines', name = 'Upper Limit', line_color='red')) #adding trace of upper limit to fig3
        fig.add_trace(go.Scatter(x = x, y = [y_unten, y_unten], mode = 'lines', name = 'Lower Limit', line_color='red')) #adding trace of lower limit to fig3

        return fig

    ## Update fig3 via checkboxes
    if bloodflow_checkmarks is not None: #eliminating iteration over NoneType Object

        if 'CMA' in bloodflow_checkmarks and 'SMA' not in bloodflow_checkmarks: #only if CMA is checked
            
            bf["Blood Flow (ml/s) - CMA"] = ut.calculate_CMA(bf[data_names[1]],2)
            fig_CMA = px.line(bf, x="Time (s)", y="Blood Flow (ml/s) - CMA") #update fig3 to show Cumulative moving Average

            if 'Show Limits' in bloodflow_checkmarks: #Check if Limits is checked
                fig3 = show_limits(fig_CMA) #call show_limits to add traces to current figure
            
            fig3 = fig_CMA #save edited figure with or without traces to fig3


        if 'SMA' in bloodflow_checkmarks and 'CMA' not in bloodflow_checkmarks: #only if SMA is checked

            fig_SMA = px.line(bf, x="Time (s)", y=bf_SMA) #save plot of edited figure

            if 'Show Limits' in bloodflow_checkmarks:
                fig3 = show_limits(fig_SMA) #call show_limits to add traces to current figure
            
            fig3 = fig_SMA #save edited figure with or without traces to fig3


        if bloodflow_checkmarks == ['Show Limits']: #check if Show Limits is the only checked box

            fig3 = show_limits(fig3) #save figure with added limit traces
        
    #adding trace of mean value to fig3
    fig3.add_trace(go.Scatter(x = x, y = [y, y], mode = 'lines', name = 'Mittelwert', line_color='green')) 


    ## Aufgabe 3.3
    alert_count = [] # 
    alert_sum = 0 #int, holds count of invalid values

    for i in bf_SMA:
        if i > y_oben or i < y_unten: # is simple moving average value '>' or '<' than the limit
            alert_count.append(bf.index[bf_SMA==i].tolist()) # append list of invalid values to list
            alert_sum += 1 #for each invalid value, alert_sum is going up by 1

    print('Alert count: ' + str(alert_count))
    print(str(alert_sum))

    # Defining alert message shown in textarea
    alert_msg = 'Warning! Blood Flow exceeded/fell below the allowed Limit for a total of ' + str(alert_sum) + ' seconds!'

    ## Two returns values instead of only one value for exercise 3.3
    return fig3, alert_msg


if __name__ == '__main__':
    app.run_server(debug=True)


## Aufgabe 3.4
# Simple Moving Average: n=4; wurde so ausgelegt, dass bei Bestimmung der Alerts nicht darauf geachtet werden muss, ob Werte bis zu 3 Sekunden hintereinander ungültig sind.
# Ist der Durchschnittswert des 4 Sekunden Intervalls nämlich nicht höher/niedriger als das erlaubte Limit von 15%, muss auch kein Alarm ausgelöst werden.