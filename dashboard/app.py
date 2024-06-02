import pandas as pd
import streamlit as st
from pinotdb import connect
from datetime import datetime
import plotly.express as px
import time
import os


pinot_host=os.environ.get("PINOT_SERVER", "pinot-broker")
pinot_port=os.environ.get("PINOT_PORT", 8099)


st.set_page_config(layout="wide")

conn = connect(pinot_host, pinot_port, path='/query/sql', scheme='http')

st.header("Wikipedia Recent Changes")

now = datetime.now()
dt_string = now.strftime("%d %B %Y %H:%M:%S")
st.write(f"Last update: {dt_string}")

# Use session state to keep track of whether we need to auto refresh the page and the refresh frequency

if not "sleep_time" in st.session_state:
    st.session_state.sleep_time = 2

if not "auto_refresh" in st.session_state:
    st.session_state.auto_refresh = True

auto_refresh = st.checkbox('Auto Refresh?', st.session_state.auto_refresh)

if auto_refresh:
    number = st.number_input('Refresh rate in seconds', value=st.session_state.sleep_time)
    st.session_state.sleep_time = number

# Find changes that happened in the last 1 minute
# Find changes that happened between 1 and 2 minutes ago

query = """
select count(*) FILTER(WHERE  ts > ago('PT1M')) AS events1Min,
        count(*) FILTER(WHERE  ts <= ago('PT1M') AND ts > ago('PT2M')) AS events1Min2Min,
        distinctcount(user) FILTER(WHERE  ts > ago('PT1M')) AS users1Min,
        distinctcount(user) FILTER(WHERE  ts <= ago('PT1M') AND ts > ago('PT2M')) AS users1Min2Min,
        distinctcount(domain) FILTER(WHERE  ts > ago('PT1M')) AS domains1Min,
        distinctcount(domain) FILTER(WHERE  ts <= ago('PT1M') AND ts > ago('PT2M')) AS domains1Min2Min
from wikievents 
where ts > ago('PT2M')
limit 1
"""

curs = conn.cursor()

curs.execute(query)
df_summary = pd.DataFrame(curs, columns=[item[0] for item in curs.description])


metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    label="Changes",
    value=df_summary['events1Min'].values[0],
    delta=float(df_summary['events1Min'].values[0] - df_summary['events1Min2Min'].values[0])
)

metric2.metric(
    label="Users",
    value=df_summary['users1Min'].values[0],
    delta=float(df_summary['users1Min'].values[0] - df_summary['users1Min2Min'].values[0])
)

metric3.metric(
    label="Domains",
    value=df_summary['domains1Min'].values[0],
    delta=float(df_summary['domains1Min'].values[0] - df_summary['domains1Min2Min'].values[0])
)

# Find all the changes by minute in the last hour

query = """
select ToDateTime(DATETRUNC('minute', ts), 'yyyy-MM-dd hh:mm:ss') AS dateMin, count(*) AS changes, 
       distinctcount(user) AS users,
       distinctcount(domain) AS domains
from wikievents 
where ts > ago('PT10M')
group by dateMin
order by dateMin desc
LIMIT 30
"""

curs.execute(query)
df_ts = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df_ts_melt = pd.melt(df_ts, id_vars=['dateMin'], value_vars=['changes', 'users', 'domains'])

fig = px.line(df_ts_melt, x='dateMin', y="value", color='variable', color_discrete_sequence =['blue', 'red', 'green'])
fig['layout'].update(margin=dict(l=0,r=0,b=0,t=40), title="Changes/Users/Domains per minute")
fig.update_yaxes(range=[0, df_ts["changes"].max() * 1.1])
st.plotly_chart(fig, use_container_width=True)

# Refresh the page
if auto_refresh:
    time.sleep(number)
    st.rerun()