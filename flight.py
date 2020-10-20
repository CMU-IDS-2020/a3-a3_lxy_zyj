import streamlit as st
import pandas as pd
import altair as alt

st.title("Let's analyze some Data.")

@st.cache  # add caching so we load the data only once
def load_data(url):
    df = pd.read_csv(url)
    return df

"""
'FL_DATE', 'OP_CARRIER', 'OP_CARRIER_FL_NUM', 'ORIGIN', 'DEST',
       'CRS_DEP_TIME', 'DEP_TIME', 'DEP_DELAY', 'TAXI_OUT', 'WHEELS_OFF',
       'WHEELS_ON', 'TAXI_IN', 'CRS_ARR_TIME', 'ARR_TIME', 'ARR_DELAY',
       'CANCELLED', 'CANCELLATION_CODE', 'DIVERTED', 'CRS_ELAPSED_TIME',
       'ACTUAL_ELAPSED_TIME', 'AIR_TIME', 'DISTANCE', 'CARRIER_DELAY',
       'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY',
"""
df_month = load_data('./2018-02-01.csv')
# df_sfo = load_data('./2018-sfo.csv')
if st.checkbox("show raw data"):
    st.write("Let's look at raw data in the Data Frame.")
st.write(df_month)

# slider
# min_weight = st.slider("Minimun weight", 2500, 6500)
# st.write("Hmm 🤔, is there some correlation between body mass and flipper length? Let's make a scatterplot with [Altair](https://altair-viz.github.io/) to find.")

# selection
# picked = alt.selection_single(on='mouseover', empty = 'none')
# picked = alt.selection_multi(on='mouseover', empty='none')
# picked = alt.selection_interval(encodings=['x'])
# # binding selection
# input_dropdown = alt.binding_select(options=['Adelie', 'Chinstrap', 'Gentoo'], name="species of ")
# picked = alt.selection_single(encodings=['color'], bind=input_dropdown)

# st.write(chart.encode(
#     color=alt.condition(picked, "species:N", alt.value('lightgray'))
# ).add_selection(picked))

# binding selection to scale
# scales = alt.selection_interval(bind='scales')
# st.write(chart.add_selection(scales))

# filter data 
# brush = alt.selection_interval(encodings=['x'])
# st.write(chart.add_selection(brush) & chart.encode(
#     x=alt.X("bill_length_mm", scale=alt.Scale(zero=False)),
#     color=alt.condition(brush, "species:N", alt.value('lightgray'))
# ).transform_filter(
#     brush
# ))
# st.write(chart.add_selection(brush) & alt.Chart(df).mark_bar().encode(
#     alt.X("body_mass_g", bin=True),
#     alt.Y("count()"),
#     alt.Color("species")
# ).transform_filter(
#     brush
# ))

# NAS delay with origin
# nas_delay = alt.Chart(df_month).mark_bar().transform_filter(
#     alt.datum['NAS_DELAY']> 5
# ).encode(
#     x=alt.X("ORIGIN"),
#     y=alt.Y("average(NAS_DELAY)", scale=alt.Scale(zero=False))
# ).properties(
#     width=600, height=400
# ).interactive()

# st.write(nas_delay)

# delayed count
st.write("Delayed Count")
delay_count = alt.Chart(df_month).mark_line().encode(
    x=alt.X("ARR_DELAY"),
    y=alt.Y("count(ARR_DELAY)"),
    tooltip=['ARR_DELAY']
).properties(
    width=600, height=400
)
st.write(delay_count)

# delay with distance
st.write("Delay vs distance")
delay_dist = alt.Chart(df_month).mark_circle().encode(
    x=alt.X("ARR_DELAY"),
    y=alt.Y("DISTANCE"),
    tooltip=['ARR_DELAY', "DISTANCE"]
).properties(
    width=600, height=400
)
st.write(delay_dist)

# Is Carrier delay the main cause?
## Carrier delay with carriers
st.write("Delay vs carriers")
carrier_delay = alt.Chart(df_month).mark_point().transform_filter(
    alt.datum['CARRIER_DELAY']>0
).encode(
    x=alt.X("OP_CARRIER"),
    y=alt.Y("CARRIER_DELAY", scale=alt.Scale(zero=False))
).properties(
    width=600, height=400
)

picked = alt.selection_interval()
select = alt.selection_single(on='mouseover', fields=['OP_CARRIER'])
## carrier delay vs. arrival delay
carrier_vs_arr = alt.Chart(df_month).mark_point().transform_filter(
    alt.datum['CARRIER_DELAY']>=0
).encode(
    x=alt.X("ARR_DELAY"),
    y=alt.Y("CARRIER_DELAY"),
    color=alt.Color('OP_CARRIER'),
    tooltip=['ARR_DELAY', 'CARRIER_DELAY']
).properties(
    width=600, height=400
)
st.write(carrier_delay.add_selection(picked) & carrier_vs_arr.transform_filter(picked).encode(
    color=alt.condition(select, "OP_CARRIER:N", alt.value('lightgray'))
).add_selection(select))

# Is weather delay the main cause?



# # Is delay related to time?
# df_month_delay = df_month.loc[:, ['FL_DATE', 'ARR_DELAY', 'CARRIER_DELAY', 'WEATHER_DELAY']]
# delay_vs_time = alt.Chart(df_month_delay).mark_line().encode(
#     x=alt.X("date(FL_DATE)"),
#     y=alt.Y("average(ARR_DELAY)"),
#     tooltip=['ARR_DELAY']
# ).properties(
#     width=600, height=400
# )
# st.write(delay_vs_time)
