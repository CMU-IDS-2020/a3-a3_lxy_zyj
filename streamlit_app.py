import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import altair as alt
from vega_datasets import data

st.title('Flight Delay')

def load_data():
	data = pd.read_csv('2018-5k.csv')
	return data

data = load_data()

st.write(data.head())
st.write(data.describe())

# for col in data:
data.loc[data['ARR_DELAY'] <= 15, 'STATUS'] = 'on time'
data.loc[data['ARR_DELAY'] >= 15, 'STATUS'] = 'slightly delayed'
data.loc[data['ARR_DELAY'] >= 60, 'STATUS'] = 'delayed'
data.loc[data['DIVERTED'] == 1, 'STATUS'] = 'diverted'
data.loc[data['CANCELLED'] == 1, 'STATUS'] = 'cancelled'

option = st.selectbox(
    'Flight Status by ?',
     ['MONTH', 'CARRIER', 'ORIGIN', 'DEST'])

if option == 'MONTH':
	x = 'month(FL_DATE):O'
	l = 12
elif option == 'CARRIER':
	x = 'OP_CARRIER:O'
	l = len(data['OP_CARRIER'].unique())
elif option == 'ORIGIN':
	x = 'ORIGIN:O'
	l = len(data['ORIGIN'].unique())
elif option == 'DEST':
	x = 'DEST:O'
	l = len(data['DEST'].unique())

if option == 'MONTH':

	status_by_option = alt.Chart(data).mark_bar().encode(
		x = x,
		y = 'count()',
		color = 'STATUS',
		tooltip = [x, 'count()'],
	).properties(width = 800, height = 400)

else:
	status_by_option = alt.Chart(data).mark_bar().encode(
		x = alt.X(x, axis = alt.Axis(labelOverlap = True), sort = '-y'),
		y = 'count()',
		color = 'STATUS',
		tooltip = [x, 'count()'],
	).properties(width = 800, height = 400)

status_by_option

'How long do flights delay?'

delay_time = data[['CARRIER_DELAY', 'WEATHER_DELAY', 'NAS_DELAY']]
delay_time = pd.melt(delay_time, var_name = 'Delay Type', value_name = 'Minutes')

delay = alt.Chart(delay_time).mark_boxplot().encode(
	x = 'Minutes',
	row = 'Delay Type',
	tooltip = ['Delay Type', 'Minutes'],
).properties(width = 630, height = 80)

delay

'How do the planned departure & arrival times affect the delay of flights?' 

brush = alt.selection(type='interval')

dep_arr = alt.Chart(data).mark_point().encode(
	x = alt.X('CRS_DEP_TIME', title = 'Departure Time', axis = alt.Axis(labelOverlap = True)),
	y = alt.Y('CRS_ARR_TIME', title = 'Arrival Time', axis = alt.Axis(labelOverlap = True), sort = '-y'),
	color = alt.condition(brush, 'STATUS', alt.value('lightgray')),
).add_selection(brush).properties(width = 600, height = 400)

bars = alt.Chart(data).mark_bar().encode(
    y = 'STATUS',
    color = 'STATUS',
    x = 'count(STATUS):Q'
).transform_filter(
    brush
)

dep_arr & bars
