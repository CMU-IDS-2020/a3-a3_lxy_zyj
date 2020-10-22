import streamlit as st
import pandas as pd
import altair as alt

# st.beta_set_page_config(layout="wide")

st.title("Why is Your Flight Delayed?")
st.text("Interactive Data Science Assignment 3, by Yeju Zhou & Xuanyi Li")

st.write("Explore how flights delay in the United States and possible reasons that lead to the delays. ")

@st.cache  # add caching so we load the data only once
def load_data(url):
    df = pd.read_csv(url)
    return df

df = load_data('./2018-5k.csv')
df = df.drop('Unnamed: 27', 1)
df = df.drop('Unnamed: 0', 1)
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



def show_data(df):
    st.header('Flight Dataset')

    st.write("In this project, we randomly select 5K rows from the flight dataset in 2018. ")
    st.write("This dataset contains....")
    if st.checkbox("Show Raw Data"):
        st.write("Let's look at raw data in the Data Frame.")
        st.write(df)
    if st.checkbox("Show Column Information"):
        st.write("Let's look at columns in the Data Frame.")
        st.markdown("**FL_DATE**: date of flight (yyyy-mm-dd)")
        st.markdown("**OP_CARRIER**: carrier name")
        st.markdown("**OP_CARRIER_FL_NUM**: flight number")
        st.markdown("**ORIGIN**: origin IATA airport code")
        st.markdown("**DEST**: destination IATA airport code")
        st.markdown("**CRS_DEP_TIME**: scheduled departure time (hhmm)")
        st.markdown("**DEP_TIME**: actual departure time (hhmm)")
        st.markdown("**DEP_DELAY**: departure delay (minutes)")
        st.markdown("**TAXI_OUT**: taxi out time (minutes)")
        st.markdown("**WHEELS_OFF**: wheels off time (hhmm)")
        st.markdown("**WHEELS_ON**: wheels on time (hhmm)")
        st.markdown("**TAXI_IN**: taxi in time (minutes)")
        st.markdown("**CRS_ARR_TIME**: scheduled arrival time (hhmm)")
        st.markdown("**ARR_TIME**: actual arrival time (hhmm)")
        st.markdown("**ARR_DELAY**: arrival delay (minutes)")
        st.markdown("**CANCELLED**: cancelled Flight Indicator (1=Yes)")
        st.markdown("**CANCELLATION_CODE**: specifies the reason for cancellation")
        st.markdown("**DIVERTED**: diverted flight indicator (1=Yes)")
        st.markdown("**CRS_ELAPSED_TIME**: estimated elapsed time (minutes)")
        st.markdown("**ACTUAL_ELAPSED_TIME**: actual elapsed time (minutes)")
        st.markdown("**AIR_TIME**: flight time (minutes)")
        st.markdown("**DISTANCE**: distance between airports (miles)")
        st.markdown("**CARRIER_DELAY**: carrier delay (minutes). Carrier delay is within the control of the air carrier.")
        st.markdown("**WEATHER_DELAY**: weather delay (minutes). This is caused by extreme or hazardous weather conditions that are forecasted or manifest themselves on point of departure, enroute, or on point of arrival.")
        st.markdown("**NAS_DELAY**: national airspace system (NAS) Delay (minutes). It may include may include: non-extreme weather conditions, airport operations, heavy traffic volume, air traffic control, etc. ")
        st.markdown("**SECURITY_DELAY**: security delay (minutes). This is caused by security reason.")
        st.markdown("**LATE_AIRCRAFT_DELAY**: late aircraft delay (minutes). This is due to the late arrival of the same aircraft at a previous airport.")
    
show_data(df)


# Overview of delay & cancellation
st.header('Overview of Delay & Cancalation')

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


def delay_distribution(df):
    st.subheader('Delay time distribution')

    """
    Flight delays are divided into categories:
    - Arrival Delay
    - Depature Delay
        
    The causes of arrival delay or departure delay are divided into categories: 
    - Carrier Delay
    - Weather Delay
    - National Aviation System Delay
    - Security Delay 
    - Late Aircraft Delay
    """

    "**Let's see how each of these delays distribute. Is there any relationship among different delay types?**"
    "You can select a range of delay on one graph to see distribution of delay for other types."

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
    ))


delay_distribution(df)


st.header("What factors delay your flight?")

"We define the 'STATUS' of a flight such that the 'STATUS' of a flight delayed for less than 0 minutes is 'on time', more than 0 minutes is 'slightly delayed', \
more than 30 minutes is delayed. And some other flights are 'diverted' or 'cancelled'."

st.subheader('\n What affects the delay status of a flight?')

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



# delay vs position
def get_delay_type(delay_type_input):
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

def show_delay_type_selection(key):
    delay_type_input = st.selectbox("Which type of delay you want to explore?",('Arrival Delay', 'Departure Delay', 'Carrier Delay',
       'Weather Delay', 'Nas Delay', 'Security Delay', 'Late Aircraft Delay'), key=key)
    return get_delay_type(delay_type_input)

def plot_map(df, collect_from='ORIGIN', connect_to='DEST'):
    st.write("")
    if collect_from=='ORIGIN':
        "**Let's analyze flights that fly out from each origin.** 🛫"
    else:
        "**Let's analyze flights that fly in to each destination.** 🛬"

    # airports = data.airports()
    # states = alt.topo_feature(data.us_10m.url, feature="states")
    airports = pd.read_csv('airport.csv')
    states = alt.topo_feature('https://vega.github.io/vega-datasets/data/us-10m.json', feature='states')


    # Create mouseover selection
    select_city = alt.selection_single(
        on="mouseover", fields=[collect_from], empty="none"
    )
    row1_1, row1_2, _, row1_3 = st.beta_columns((5,5,1,5))
    with row1_1:
        min_value_delay = st.slider("Select minimun value of delay", -100, 1000, -100, key=collect_from)
    with row1_2:
        max_value_delay = st.slider("Select maximun value of delay", -100, 1000, 1000, key=collect_from)
    with row1_3:
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
    st.write("You can select each airport and see the distribution of delays from/to this airport.")
    st.write("Thickness represents the throughput. Color represents the lateness.")

    st.write((background + connections + points).configure_view(stroke=None))

st.header("Is geographical position related to the flight delays?")
# row1_1, row1_2 = st.beta_columns((1,1))
# with row1_1:
plot_map(df)

# with row1_2:
plot_map(df, 'DEST', 'ORIGIN')


# delay composition
## Carrier delay with carriers
def carrier_delay():
    st.header("Is there any carrier that is more likely to delay?")

    """
    Carrier Delay represent the delay caused by the air carrier. 
    Possible occurence are: aircraft cleaning, aircraft damage, baggage, etc.

    """

    carrier_delay = alt.Chart(df).mark_bar().transform_filter(
        alt.datum['CARRIER_DELAY']>0
    ).encode(
        x=alt.X("OP_CARRIER", sort='-y', title = 'Carrier'),
        y=alt.Y("average(CARRIER_DELAY)", scale=alt.Scale(zero=False), title = 'Average Carrier Delay'),
        tooltip=[alt.Tooltip("OP_CARRIER", title = 'Carrier'), alt.Tooltip("average(CARRIER_DELAY)", title = 'Average Carrier Delay')]
    ).properties(
        width=600, height=250
    )
    st.write(carrier_delay)

    picked = alt.selection_interval()

    carrier_delay_dist = alt.Chart(df).mark_point().transform_filter(
        alt.datum['CARRIER_DELAY']>0
    ).transform_calculate(    
        CARRIER_DELAY="datum.CARRIER_DELAY < 350 ? datum.CARRIER_DELAY : 350", 
    ).encode(
        x=alt.X("OP_CARRIER"),
        y=alt.Y("CARRIER_DELAY", scale=alt.Scale(zero=False)),
        order=alt.Order(
            'average(CARRIER_DELAY)',
            sort='descending'),
        tooltip=['OP_CARRIER', 'CARRIER_DELAY', 'ARR_DELAY']
    ).properties(
        width=600, height=100
    ).add_selection(picked) 

    
    # st.write()

    # st.write(carrier_delay_dist.add_selection(picked) & carrier_delay.transform_filter(picked))
    # binding selection
    # input_dropdown = alt.binding_select(options=carrier_names, name="Carrier ")
    # dd_select = alt.selection_single(encodings=['color'], bind=input_dropdown)

    ## carrier delay vs. arrival delay
    "**Is there any relationship between Carrier Delay and other type delays?**"
    select = alt.selection_single(on='mouseover', fields=['OP_CARRIER'])

    delay_type_input = st.selectbox("Show correlation between Carrier Delay and ",('Arrival Delay', 'Departure Delay',
       'Weather Delay', 'Nas Delay', 'Security Delay', 'Late Aircraft Delay'))
    delay_type = get_delay_type(delay_type_input)

    carrier_vs_arr = alt.Chart(df).mark_point().transform_filter(
        alt.datum['CARRIER_DELAY']>=0
    ).transform_calculate(    
        SELECTED_DELAY=f"datum.{delay_type} < 350 ? datum.{delay_type} : 350",  
        CARRIER_DELAY="datum.CARRIER_DELAY < 350 ? datum.CARRIER_DELAY : 350", 
    ).encode(
        x='SELECTED_DELAY:Q',
        y=alt.Y("CARRIER_DELAY"),
        color=alt.Color('OP_CARRIER'),
        tooltip=[delay_type, 'CARRIER_DELAY','OP_CARRIER']
    ).properties(
        width=600, height=300
    )
    """
    You can select the interval in the graph below to explore the carrier delays in a specific range.
    """
    st.write(carrier_delay_dist & carrier_vs_arr.transform_filter(picked).encode(
        color=alt.condition(select, "OP_CARRIER:N", alt.value('lightgray'))
    ).add_selection(select))

carrier_delay()


st.header("Now let's see how the departure & arrival time relate to flight delays.")

'\n Drag you mouse to select an area and see how the delay status distribute over that time interval! You can also click the colored dots on the legend to see the distribution of one particular status.'

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

'If you investigate carefully, you will find that there are much more delayed flights in the upper-right corner, where flights departure late or arrive late.'


def delay_by_month_date():

    st.header('Are there more delays in particular months or dates as the seasons change?')

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

    st.write(all_delay)

    if option == 'Month':
    	st.write("It makes sense that there are more extreme weathers during July-August (heavy rains) and Nov. (heavy snows)!")
delay_by_month_date()



st.subheader('Will the flying distance also affect the flight delays?')
'It appears that the shorter the distance, the larger the late aircraft delay! Maybe this is caused by the fact that more flights are flying shorter distances, and the more flights, the more congestion.'

def late_aircraft_delay_by_distance():
    chart = alt.Chart(df).mark_point().encode(
        x = alt.X('DISTANCE', title = 'Flying Distance'),
        y = alt.Y('LATE_AIRCRAFT_DELAY', title = 'Late Aircraft Delay'),
    ).properties(width = 600, height = 400)
    chart

late_aircraft_delay_by_distance()

