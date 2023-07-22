import streamlit as st
from datetime import datetime, timedelta
import pandas as pd


class Dataset(object):
    pass


class Evictions(Dataset):
    def __init__(self):
        self.schema = {
            "case_code": "object",
            "filed_date": "datetime64[ns]",
            "case_description": "object",
            "status": "category",
            "county": "category",
            "city": "object",
            "directional": "object",
            "zip": "object",
            "evicting_property_managers": "object",
            "evicting_landlords": "object",
            "evicting_lawyers": "object",
            "evicting_agents": "object",
            "first_appearance_date": "datetime64[ns]",
            "next_appearance_date": "datetime64[ns]",
            "last_appearance_date": "datetime64[ns]",
        }

        self.file_location = "https://storage.googleapis.com/depdx_data/evictions.json"


data_sets = {"evictions": Evictions}


def get_df(data_set) -> pd.DataFrame:
    data_set = data_sets[data_set]
    file_type = data_set().file_location.split(".")[-1]

    if file_type == "csv":
        df = pd.read_csv(data_set().file_location)
        df = df.astype(data_set().schema)

    elif file_type == "json":
        df = pd.read_json(data_set().file_location)
        df = df.astype(data_set().schema)

    else:
        raise Exception(f"file extension {file_type} not supported")

    return df


evictionsDF = get_df("evictions")

counties = evictionsDF["county"].unique().tolist()
min_date = datetime.date(min(evictionsDF['filed_date']))
max_date = datetime.date(max(evictionsDF['filed_date']))

st.set_page_config(
    page_title="Portland Metro Evictions",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

with st.sidebar:
    st.markdown("Select any or all of the Portland Metro counties and a date range for evictions filed in county courts")
    
    selected_counties = st.multiselect(
        "County", counties, ["Multnomah", "Washington", "Clackamas"]
    )

    start_date = st.date_input(
        "Filed Start Date", pd.Timestamp("today") - timedelta(days=30), help=f"latest data available is {min_date}"
    )

    end_date = st.date_input("Filed End Date", pd.Timestamp("today"), help=f"latest data available is {max_date}")

    st.caption("""
        We gather data from Multnomah, Washington, and Clackamas County Eviction Court Filings. These counts are a total number of evictions filed, not necessarily displacements. However, most filed evictions do result in a displacement through: 
          - An informal landlord-tenant agreement to move out (case-dismissed)
          - A court-official landlord-tenant agreement to move out (case-dismissed), OR
          - A court-ordered judgment of eviction (eviction on record)
    """)

    st.info("The Clackamas County data is incomplete, but we still want to track what we can")


date_range_days = end_date - start_date
prev_range_start_date = start_date - date_range_days

evictionsDF = evictionsDF[evictionsDF["county"].isin(selected_counties)]
prev_evictionsDF = evictionsDF[
    (evictionsDF["filed_date"].dt.date >= prev_range_start_date)
    & (evictionsDF["filed_date"].dt.date <= start_date)
]
total_prev_evictions = len(prev_evictionsDF.index)

evictionsDF = evictionsDF[
    (evictionsDF["filed_date"].dt.date >= start_date)
    & (evictionsDF["filed_date"].dt.date <= end_date)
]
total_evictions = len(evictionsDF.index)

evictions_delta = round(
    ((total_evictions - total_prev_evictions) / total_evictions) * 100
)

ll_evictors = evictionsDF.explode("evicting_landlords")
pm_evictors = evictionsDF.explode("evicting_property_managers")
lawyer_evictors = evictionsDF.explode("evicting_lawyers")

top_rows = 10

top_ll_evictorsDF = (
    ll_evictors.groupby(["evicting_landlords"])["case_code"]
    .count()
    .sort_values(ascending=False)
    .reset_index(name="count")
    .head(top_rows)
)
top_pm_evictorsDF = (
    pm_evictors.groupby(["evicting_property_managers"])["case_code"]
    .count()
    .sort_values(ascending=False)
    .reset_index(name="count")
    .head(top_rows)
)
top_lawyer_evictorsDF = (
    lawyer_evictors.groupby(["evicting_lawyers"])["case_code"]
    .count()
    .sort_values(ascending=False)
    .reset_index(name="count")
    .head(top_rows)
)

st.metric(
    label="Evictions Filed",
    value=format(total_evictions, ",d"),
    delta=f"{evictions_delta}%",
    delta_color="inverse",
    help='change is over the previous period of the same number of days within the selected date range'
)


col1, col2, col3 = st.columns(3)

with col1:
    st.dataframe(top_ll_evictorsDF)

with col2:
    st.dataframe(top_pm_evictorsDF)

with col3:
    st.dataframe(top_lawyer_evictorsDF)
