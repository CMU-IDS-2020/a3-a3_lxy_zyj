import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data
import pydeck as pdk


alt.data_transformers.enable('data_server')

st.title("Let's analyze some Data.")

@st.cache  # add caching so we load the data only once
def load_data(url):
    df = pd.read_csv(url)
    df.fillna(0)
    return df

"""
'FL_DATE', 'OP_CARRIER', 'OP_CARRIER_FL_NUM', 'ORIGIN', 'DEST',
       'CRS_DEP_TIME', 'DEP_TIME', 'DEP_DELAY', 'TAXI_OUT', 'WHEELS_OFF',
       'WHEELS_ON', 'TAXI_IN', 'CRS_ARR_TIME', 'ARR_TIME', 'ARR_DELAY',
       'CANCELLED', 'CANCELLATION_CODE', 'DIVERTED', 'CRS_ELAPSED_TIME',
       'ACTUAL_ELAPSED_TIME', 'AIR_TIME', 'DISTANCE', 'CARRIER_DELAY',
       'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY',
"""
df = load_data('./2018-5k.csv')
df = df.fillna(0)
carrier_names = df.OP_CARRIER.unique().tolist()
airport_names = df.ORIGIN.unique().tolist()

def show_data():
    st.write("This dataset contains....")
    if st.checkbox("show raw data"):
        st.write("Let's look at raw data in the Data Frame.")
        st.write(df)
show_data()


# Overview of delay & cancellation

# delayed count
def delayed_count():
    st.write("Delayed Count")
    delay_df = df.loc[:, ['ARR_DELAY','CARRIER_DELAY','WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']]
    delay_count = alt.Chart(df).mark_bar().encode(
        x=alt.X("ARR_DELAY"),
        y=alt.Y("count(ARR_DELAY)"),
        tooltip=['ARR_DELAY', 'count(ARR_DELAY)']
    ).properties(
        width=600, height=400
    )
    st.write(delay_count)

    delay_percent = alt.Chart(delay_df).mark_bar().encode(
        x = alt.X("ARR_DELAY"),
        y = alt.Y("sum(CARRIER_DELAY)")
    ).properties(
        width=600, height=400
    )
    st.write(delay_percent)

delayed_count()

# delay vs position
def plot_airport(df):
    airports = data.airports()
    # st.write(airports)
    states = alt.topo_feature(data.us_10m.url, feature='states')
    ori_df = df.merge(airports, left_on = "ORIGIN", right_on = "iata", how = "inner")
    dest_df = df.merge(airports, left_on = "DEST", right_on = "iata", how = "inner")
    
    # US states background
    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).properties(
        width=500,
        height=300
    ).project('albersUsa')

    # airport positions on background
    points_dep = alt.Chart(ori_df).mark_circle().transform_filter(
        alt.datum['DEP_DELAY']>0,
    ).encode(
        longitude='longitude',
        latitude='latitude',
        tooltip=['ORIGIN', 'DEP_DELAY'],
        size=alt.Size('average(DEP_DELAY)'),
        
    )
    st.write(background+points_dep)


    points_arr = alt.Chart(dest_df).mark_circle().transform_filter(
        alt.datum['ARR_DELAY']>0,
    ).encode(
        longitude='longitude',
        latitude='latitude',
        tooltip=['DEST', 'ARR_DELAY'],
        size=alt.Size('average(ARR_DELAY)'),
    )
    st.write(background+points_arr)

plot_airport(df)



# Is delay related to distance?
def delay_vs_distance():
    st.write("Delay vs distance")
    delay_dist = alt.Chart(df).mark_circle().encode(
        x=alt.X("ARR_DELAY"),
        y=alt.Y("DISTANCE"),
        tooltip=['ARR_DELAY', "DISTANCE"]
    ).properties(
        width=600, height=400
    ).interactive()
    st.write(delay_dist)
delay_vs_distance()

# Is delay related to departure time?
def delay_vs_departure_time():
    st.write("Delay vs departure time")
    delay_dist = alt.Chart(df).mark_circle().encode(
        x=alt.X("CRS_DEP_TIME"),
        y=alt.Y("ARR_DELAY"),
        tooltip=['ARR_DELAY', "CRS_DEP_TIME"]
    ).properties(
        width=600, height=400
    )
    st.write(delay_dist)
delay_vs_departure_time()

# delay composition
# NAS delay
def nas_delay():
    Top20airports = df[df['DEST'].isin([
        'ORD', 'ATL', 'DFW', 'DEN', 'EWR', 'LAX', 'IAH', 'PHX', 
        'DTW', 'SFO','LAS', 'DEN', 'ORD','JFK' ,'CLT', 'LGA', 
        'MCO', 'MSP', 'BOS','PHL'])]
    nas_delay = alt.Chart(Top20airports).mark_point().transform_filter(
        alt.datum['NAS_DELAY']>0
    ).encode(
        x=alt.X("ORIGIN"),
        y=alt.Y("NAS_DELAY", scale=alt.Scale(zero=False))
    ).properties(
        width=600, height=400
    )
    st.write(nas_delay)
nas_delay()

# Is delay related to date&time?
def delay_vs_datetime():
    df_month_delay = df.loc[:, ['FL_DATE', 'ARR_DELAY', 'CARRIER_DELAY', 'WEATHER_DELAY']]
    delay_vs_time = alt.Chart(df_month_delay).mark_line().encode(
        x=alt.X("date(FL_DATE)"),
        y=alt.Y("average(ARR_DELAY)"),
        tooltip=['ARR_DELAY']
    ).properties(
        width=600, height=400
    )
    st.write(delay_vs_time)
delay_vs_datetime()


## Carrier delay with carriers
def carrier_delay():
    st.write("Delay vs carriers")

    carrier_delay = alt.Chart(df).mark_point().transform_filter(
        alt.datum['CARRIER_DELAY']>0
    ).encode(
        x=alt.X("OP_CARRIER"),
        y=alt.Y("CARRIER_DELAY", scale=alt.Scale(zero=False))
    ).properties(
        width=600, height=400
    )

    picked = alt.selection_interval()
    select = alt.selection_single(on='mouseover', fields=['OP_CARRIER'])
    # binding selection
    # input_dropdown = alt.binding_select(options=carrier_names, name="Carrier ")
    # dd_select = alt.selection_single(encodings=['color'], bind=input_dropdown)

    ## carrier delay vs. arrival delay
    carrier_vs_arr = alt.Chart(df).mark_point().transform_filter(
        alt.datum['CARRIER_DELAY']>=0
    ).transform_calculate(    
        ARR_DELAY="datum.ARR_DELAY < 180 ? datum.ARR_DELAY : 180",  # clamp delays > 3 hours    
        CARRIER_DELAY="datum.CARRIER_DELAY < 180 ? datum.CARRIER_DELAY : 180",  # clamp delays > 3 hours    
    ).encode(
        x=alt.X("ARR_DELAY"),
        y=alt.Y("CARRIER_DELAY"),
        color=alt.Color('OP_CARRIER'),
        tooltip=['ARR_DELAY', 'CARRIER_DELAY','OP_CARRIER']
    ).properties(
        width=600, height=400
    )

    st.write(carrier_delay.add_selection(picked) & carrier_vs_arr.transform_filter(picked).encode(
        color=alt.condition(select, "OP_CARRIER:N", alt.value('lightgray'))
    ).add_selection(select))
carrier_delay()

# weather delay
def weather_delay():
    weather_delay = alt.Chart(df).mark_point().transform_filter(
        alt.datum['WEATHER_DELAY']>0
    ).transform_calculate(    
        WEATHER_DELAY="datum.WEATHER_DELAY < 180 ? datum.WEATHER_DELAY : 180",  # clamp delays > 3 hours    
    ).encode(
        x=alt.X("ARR_DELAY"),
        y=alt.Y("WEATHER_DELAY", scale=alt.Scale(zero=False)),
        color=alt.Color('ORIGIN'),
        tooltip=['ARR_DELAY', 'WEATHER_DELAY','ORIGIN']
    ).properties(
        width=600, height=400
    )
    st.write(weather_delay)
weather_delay()