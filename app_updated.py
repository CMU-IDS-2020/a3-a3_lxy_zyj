import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data
import pydeck as pdk

st.beta_set_page_config(layout="wide")
alt.data_transformers.enable('data_server')

st.title("What made your flight delayed?")

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

# init STATUS col 
df.loc[df['ARR_DELAY'] <= 0, 'STATUS'] = 'on time'
df.loc[df['ARR_DELAY'] > 0, 'STATUS'] = 'slightly delayed'
df.loc[df['ARR_DELAY'] >= 30, 'STATUS'] = 'delayed'
df.loc[df['DIVERTED'] == 1, 'STATUS'] = 'diverted'
df.loc[df['CANCELLED'] == 1, 'STATUS'] = 'cancelled'

df.loc[df['ARR_DELAY'] <= 0, 'ON_TIME?'] = 'On Time'
df.loc[df['ARR_DELAY'] > 0, 'ON_TIME?'] = 'Delayed'
df.loc[df['DIVERTED'] == 1, 'ON_TIME?'] = 'Delayed'
df.loc[df['CANCELLED'] == 1, 'ON_TIME?'] = 'Delayed'



def show_data():
    st.write("This dataset contains....")
    if st.checkbox("show raw data"):
        st.write("Let's look at raw data in the Data Frame.")
        st.write(df)
show_data()


# Overview of delay & cancellation

def delay_per():
    st.subheader('How many flights are delayed, diverted or cancelled among the 5K flights?')
    delay_per = alt.Chart(df).mark_bar().encode(
        x = alt.X('count(ON_TIME?):Q', title = 'Number of Flights'),
        y = alt.Y('ON_TIME?:O', title = ''),
        color = alt.Color('ON_TIME?', legend = None),
    ).properties(width = 600, height = 160)

    text = delay_per.mark_text(
        align = 'left',
        baseline = 'middle',
        dx = 3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text = 'count(ON_TIME?):Q'
    )

    delay_per + text

delay_per()


# delayed count
def delayed_count():
    st.write("How long do flights delay?")
    delay_df = df.loc[:, ['ARR_DELAY','CARRIER_DELAY','WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']]
    delay_count = alt.Chart(df).mark_bar().transform_calculate(    
        delay="datum.ARR_DELAY < 400 ? datum.ARR_DELAY : 400"
    ).encode(
        x=alt.X('delay:Q'),
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


def delay_distribution(df):
    st.write('Flight delays are divided into categories: 1) arrival delay, 2) depature delay, 3) carrier delay, 4) weather delay, \
        5) national aviation system delay, 6) security delay and 7) late aircrate delay.')
    "Let's see how each of these delays distribute."

    brush = alt.selection_interval(encodings=['x'])
    delay_names = ['ARR_DELAY','DEP_DELAY','CARRIER_DELAY','WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']
    hist = (
        alt.Chart().mark_bar().encode(
            alt.X(
                alt.repeat("row"),
                type="quantitative",
                axis=alt.Axis(
                    format='d', titleAnchor='start'
                ),
            ),
            alt.Y('count():Q', title=None, scale=alt.Scale(type='log')),
            tooltip=['count():Q']
        )
    )
    st.write(alt.layer(
        hist.add_selection(brush).encode(color=alt.value('lightgrey')),
        hist.transform_filter(brush),
    ).properties(width=600, height=100).repeat(
        row=delay_names,
        data=df
    ).transform_calculate(
        ARR_DELAY='datum.ARR_DELAY <300 ? datum.ARR_DELAY : 300',
        DEP_DELAY='datum.DEP_DELAY <300 ? datum.DEP_DELAY : 300'

    ).configure_view(
        stroke='transparent'
    )
    )


    delay_time = df.loc[:, ['ARR_DELAY','CARRIER_DELAY','WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']]
    delay_time = pd.melt(delay_time, var_name = 'Delay Type', value_name = 'Minutes')

    delay = alt.Chart(delay_time).mark_boxplot().encode(
        x = 'Minutes',
        y = 'count()',
        row = 'Delay Type',
        tooltip = ['Delay Type', 'Minutes', 'count():Q'],
    ).properties(width = 600, height = 80)
    st.write(delay)

delay_distribution(df)

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

def show_delay_type_selection(key):
    delay_type_input = st.selectbox("Which type of delay you want to explore?",('Arrival Delay', 'Departure Delay', 'Carrier Delay',
       'Weather Delay', 'Nas Delay', 'Security Delay', 'Late Aircraft Delay'), key=key)
    if delay_type_input=='Arrival Delay':
        delay_type='ARR_DELAY'
    elif delay_type_input=='Departure Delay':
        delay_type='DEP_DELAY'
    elif delay_type_input=='Carrier Delay':
        delay_type='CARRIER_DELAY'
    elif delay_type_input=='Weather Delay':
        delay_type='WEATHER_DELAY'
    elif delay_type_input=='Nas Delay':
        delay_type='NAS_DELAY'
    elif delay_type_input=='Security Delay':
        delay_type='SECURITY_DELAY'
    elif delay_type_input=='Late Aircraft Delay':
        delay_type='LATE_AIRCRAFT_DELAY'
    else:
        delay_type='ARR_DELAY'
    return delay_type

def plot_map(df, collect_from='ORIGIN', connect_to='DEST'):
    if collect_from=='ORIGIN':
        st.subheader("Let's analyze flights that fly out from each origin. 🛫")
    else:
        st.subheader("Let's analyze flights that fly in to each destination. 🛬")

    airports = data.airports()
    states = alt.topo_feature(data.us_10m.url, feature="states")

    # Create mouseover selection
    select_city = alt.selection_single(
        on="mouseover", fields=[collect_from], empty="none"
    )
    min_value_delay = st.slider("Select minimun value of delay", -100, 1000, -100, key=collect_from)
    max_value_delay = st.slider("Select maximun value of delay", -100, 1000, 1000, key=collect_from)
    delay_type = show_delay_type_selection(collect_from)

    # Define which attributes to lookup from airports.csv
    lookup_data = alt.LookupData(
        airports, key="iata", fields=["state", "latitude", "longitude"]
    )

    background = alt.Chart(states).mark_geoshape(
        fill="lightgray",
        stroke="white"
    ).properties(
        width=650,
        height=400
    ).project("albersUsa")

    scale = alt.Scale(
        range=['green', 'orange', 'darkred'],
        domain=(0,60)
    )

    connections = alt.Chart(df).mark_rule(opacity=0.35).transform_filter(
        (alt.datum[f'{delay_type}']>= min_value_delay) &
        (alt.datum[f'{delay_type}']<= max_value_delay)
    ).encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        latitude2="lat2:Q",
        longitude2="lon2:Q",
        color=alt.Color("delay:Q", scale=scale),
        size=alt.Size("count:Q",scale=alt.Scale(range=[0, 40], domain=(0, 20),type='linear'), legend=None),
        tooltip=['ORIGIN:N', 'DEST:N', 'count:Q', 'delay:Q']
    ).transform_aggregate(
        count=f"count({delay_type})",
        delay=f"average({delay_type})",
        groupby=["ORIGIN","DEST"]
    ).transform_lookup(
        lookup=collect_from,
        from_=lookup_data
    ).transform_lookup(
        lookup=connect_to,
        from_=lookup_data,
        as_=["state", "lat2", "lon2"]
    ).transform_filter(
        select_city 
    )

    points = alt.Chart(df).mark_circle().transform_filter(
        (alt.datum[delay_type]>= min_value_delay) &
        (alt.datum[delay_type]<= max_value_delay)
    ).encode(
        latitude="latitude:Q",
        longitude="longitude:Q",
        size=alt.Size("routes:Q", scale=alt.Scale(range=[0, 1000]), legend=None),
        order=alt.Order("routes:Q", sort="descending"),
        color=alt.Color("average_delay:Q", scale=scale),
        tooltip=[f"{collect_from}:N", "average_delay:Q"]
    ).transform_aggregate(
        average_delay=f"average({delay_type})",
        routes=f"count({connect_to})",
        groupby=[collect_from]
    ).transform_lookup(
        lookup=collect_from,
        from_=lookup_data
    ).transform_filter(
        (alt.datum[collect_from] != 'SJU') & (alt.datum[collect_from] != 'GUM') &
        (alt.datum[collect_from] != 'AZA') & (alt.datum[collect_from] != 'PBG') &
        (alt.datum[collect_from] != 'USA') & (alt.datum[collect_from] != 'ECP') &
        (alt.datum[collect_from] != 'STT')
    ).add_selection(
        select_city
    )
    st.write("You can select each airport and see the distribution.")
    st.write("Thickness represents the throughput and color represents the lateness")

    st.write((background + connections + points).configure_view(stroke=None))

st.header("Is geographical position related to the flight delays?")
row1_1, row1_2 = st.beta_columns((1,1))
with row1_1:
    plot_map(df)

with row1_2:
    plot_map(df, 'DEST', 'ORIGIN')


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



st.header("What other factors also delay your flight?")

"We define the 'STATUS' of a flight such that the 'STATUS' of a flight delayed for less than 0 minutes is 'on time', more than 0 minutes is 'slightly delayed', \
more than 30 minutes is delayed. And some other flights are 'diverted' or 'cancelled'."

st.subheader('\n What affects the delay status of a flight other than geographical location?')

# STATUS by MONTH/CARRIER/ORIGIN ...

def status_by_option():
    option = st.selectbox(
        'Flight Status by ?',
         ['MONTH', 'DATE', 'CARRIER', 'ORIGIN', 'DEST'])

    if option == 'MONTH':
        x = 'month(FL_DATE):O'
        l = 12
    elif option == 'DATE':
        x = 'date(FL_DATE):O'
    elif option == 'CARRIER':
        x = 'OP_CARRIER:O'
        l = len(df['OP_CARRIER'].unique())
    elif option == 'ORIGIN':
        x = 'ORIGIN:O'
        l = len(df['ORIGIN'].unique())
    elif option == 'DEST':
        x = 'DEST:O'
        l = len(df['DEST'].unique())

    if option == 'MONTH' or option == 'DATE':

        status_by_option = alt.Chart(df).mark_bar().transform_filter(alt.datum['STATUS'] != 'on time').encode(
            x = alt.X(x, title = option),
            y = alt.Y('count()', title = 'Count Delayed Flights'),
            color = 'STATUS',
            tooltip = [alt.Tooltip(x, title = option), alt.Tooltip('count()', title = 'Count Delayed Flights')],
        ).properties(width = 800, height = 400).interactive()

    else:
        status_by_option = alt.Chart(df).mark_bar().transform_filter(alt.datum['STATUS'] != 'on time').encode(
            x = alt.X(x, axis = alt.Axis(labelOverlap = True), sort = '-y', title = option),
            y = alt.Y('count()', title = 'Count Delayed Flights'),
            color = 'STATUS',
            tooltip = [alt.Tooltip(x, title = option), alt.Tooltip('count()', title = 'Count Delayed Flights')],
        ).properties(width = 800, height = 400).interactive()

    status_by_option

status_by_option()

'It is noteworthy that different carriers have drastically different performance on flight delays.'
'Carrier WN flew almost twice the number of delayed flights than any other carrier!' 


st.subheader("Let's see how the departure & arrival time relate to flight delays.")

'\n Drag you mouse to select an area and see how the delay status distribute over that time interval!'
'\n You can also click the colored dots on the legend to see the distribution of one particular status.'

def status_by_dep_arr():
    selection = alt.selection_multi(fields = ['STATUS'])
    brush = alt.selection(type='interval')

    color_select_brush = alt.condition(selection | brush,
                          alt.Color('STATUS:N', legend = None),
                          alt.value('lightgrey'))

    color_select = alt.condition(selection,
                          alt.Color('STATUS:N', legend = None),
                          alt.value('lightgrey'))

    # color_brush = alt.condition(brush,
    #                       alt.Color('STATUS:N', legend = None),
    #                       alt.value('lightgray'))

    dep_arr = alt.Chart(df).mark_circle().encode(
    # dep_arr = alt.Chart(df).mark_circle().transform_filter(alt.datum['STATUS'] != 'on time').encode(
        x = alt.X('CRS_DEP_TIME:Q', title = 'Departure Time', axis = alt.Axis(labelOverlap = True)),
        y = alt.Y('CRS_ARR_TIME:Q', title = 'Arrival Time', axis = alt.Axis(labelOverlap = True), sort = '-y'),
        # color = alt.condition(brush, 'STATUS', alt.value('lightgray')),
        color = color_select_brush,
        size = alt.Size('average(ARR_DELAY):Q', title = 'Arrival Delay', scale = alt.Scale(domain = [1, 800]), legend = None),
        tooltip = [alt.Tooltip('CRS_DEP_TIME', title = 'Departure Time'), alt.Tooltip('CRS_ARR_TIME', title = 'Arrival Time'), \
        alt.Tooltip('average(ARR_DELAY):Q', title = 'Arrival Delay')],
    ).add_selection(brush).properties(width = 600, height = 400)

    bars = alt.Chart(df).mark_bar().encode(
    # bars = alt.Chart(df).mark_bar().transform_filter(alt.datum['STATUS'] != 'on time').encode(
        y = alt.Y('STATUS', title = ''),
        # color = 'STATUS',
        color = color_select,
        x = alt.X('count(STATUS):Q', title = 'Delayed Flights Count'),
    ).transform_filter(
        brush
    )

    bar_text = bars.mark_text(
        align = 'left',
        baseline = 'middle',
        dx = 3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text = 'count(STATUS):Q'
    )

    # count = alt.Chart(df).mark_bar().encode(
    count = alt.Chart(df).mark_bar().transform_filter(alt.datum['STATUS'] != 'on time').encode(
        x = alt.X('count(STATUS):Q', title = 'Total Delayed Flights Count'),
    ).transform_filter(
        brush
    )

    count_text = count.mark_text(
        align = 'left',
        baseline = 'middle',
        dx = 3 
    ).encode(
        text = 'count(STATUS):Q'
    )

    legend = alt.Chart(df).mark_point().encode(
    # legend = alt.Chart(df).mark_point().transform_filter(alt.datum['STATUS'] != 'on time').encode(
        y = alt.Y('STATUS:N', axis = alt.Axis(orient = 'right')),
        color = color_select
    ).add_selection(
        selection
    )

    (dep_arr & (count + count_text) & (bars + bar_text) ) | legend

status_by_dep_arr()



def weather_delay_by_month_date():

    st.subheader('Are there more weather delays in particular months or dates as the seasons change?')

    option = st.selectbox('Month or Date?', ['Month', 'Date'])
    if option == 'Month':
        x = 'month(FL_DATE):O'
    elif option == 'Date':
        x = 'date(FL_DATE):O'

    delays = pd.melt(df[['FL_DATE', 'CARRIER_DELAY', 'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']], id_vars = 'FL_DATE', var_name = 'delay_type', value_name = 'delay')

    all_delay = alt.Chart(delays).mark_area().encode(
        x = alt.X(x, title = option),
        y = alt.Y('sum(delay)', title = 'Delay'),
        color = 'delay_type',
    ).properties(width = 600, height = 400).interactive()

    all_delay

weather_delay_by_month_date()


st.subheader('Some vis that see trends:')


def late_aircraft_delay_by_distance():
    chart = alt.Chart(df).mark_point().encode(
        x = 'DISTANCE',
        y = 'LATE_AIRCRAFT_DELAY',
    ).properties(width = 600, height = 400)
    chart

late_aircraft_delay_by_distance()



def late_aircraft_delay_by_time():
    chart = alt.Chart(df).mark_point().encode(
        x = 'CRS_ELAPSED_TIME',
        y = 'LATE_AIRCRAFT_DELAY',
    ).properties(width = 600, height = 400)
    chart

late_aircraft_delay_by_time()





st.subheader('Others...')

def delay_type_by_option():
    delay_option = st.selectbox(
        'Which type of delay would you like to discover?', 
        ['ARR_DELAY', 'WEATHER_DELAY', 'NAS_DELAY', 'CARRIER_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY'])

    option = st.selectbox(
        'By which axis?',
        ['MONTH', 'DEPARTURE TIME', 'ARRIVAL TIME', 'DISTANCE', 'FLYING TIME'])

    if option == 'MONTH':
        x_axis = 'month(FL_DATE):O'
    elif option == 'DEPARTURE TIME':
        x_axis = 'CRS_DEP_TIME'
    elif option == 'ARRIVAL TIME':
        x_axis = 'CRS_ARR_TIME'
    elif option == 'DISTANCE':
        pass
    elif option == 'FLYING TIME':
        x_axis = 'CRS_ELAPSED_TIME'

    delay_option_chart = alt.Chart(df).mark_point().encode(
        x = alt.X(x_axis, title = option),
        y = alt.Y(delay_option, title = delay_option),
    ).properties(width = 600, height = 400)

    delay_option_chart

delay_type_by_option()