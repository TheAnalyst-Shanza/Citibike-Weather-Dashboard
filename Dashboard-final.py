import os
from pathlib import Path
from datetime import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit.components.v1 as components
from PIL import Image

# ----------------------------
# Base directory (this .py file)
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Citi Bike Strategy Dashboard", layout="wide")
st.title("Citi Bike Strategy Dashboard")
st.write("Interactive dashboard exploring station demand, weather impact, and trip patterns in NYC (2022).")

# ----------------------------
# Paths (aligned to notebook)
# ----------------------------
TRIPS_PATH = "Data/Processed/citibike_weather_2022.csv"
TOP20_PATH = "Data/Processed/top20_station.csv"
MAP_PATH = "Notebooks/MAPPS/kepler_top300.html"

# ----------------------------
# Helpers
# ----------------------------
def _read_csv(path: str, **kwargs) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"Missing required file: {path}")
        st.stop()
    return pd.read_csv(path, **kwargs)

def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Return a daily dataframe with columns: date, trips, avg_temp.

    Supports multiple upstream schemas (notebook variants / processed variants).
    """
    if "date" not in df.columns:
        st.error(f"Trips data is missing a 'date' column. Available columns: {list(df.columns)}")
        st.stop()

    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"])

    # Case 1: already daily, notebook style
    if {"trip_count", "avgTemp"}.issubset(d.columns):
        out = d.sort_values("date")[["date", "trip_count", "avgTemp"]].rename(
            columns={"trip_count": "trips", "avgTemp": "avg_temp"}
        )
        return out

    # Case 2: already daily, processed daily style
    if {"daily_trips", "temp_avg_c"}.issubset(d.columns):
        out = d.sort_values("date")[["date", "daily_trips", "temp_avg_c"]].rename(
            columns={"daily_trips": "trips", "temp_avg_c": "avg_temp"}
        )
        return out

    # Case 3: trip-level with ride_id + weather temp column
    trip_id_col = "ride_id" if "ride_id" in d.columns else None
    if trip_id_col is None:
        # fallback common identifiers
        for cand in ["trip_id", "id"]:
            if cand in d.columns:
                trip_id_col = cand
                break

    temp_col = None
    for cand in ["TAVG", "avg_temp", "avgTemp", "temp_avg_c", "temperature"]:
        if cand in d.columns:
            temp_col = cand
            break

    if trip_id_col is None:
        st.error(
            "Could not find a trip id column to count trips. "
            f"Expected 'ride_id' (or similar). Available columns: {list(d.columns)}"
        )
        st.stop()

    if temp_col is None:
        st.error(
            "Could not find a temperature column for the weather line. "
            f"Expected one of ['TAVG','avgTemp','temp_avg_c',...]. Available columns: {list(d.columns)}"
        )
        st.stop()

    # Aggregate to day
    d["day"] = d["date"].dt.floor("D")
    daily = (
        d.groupby("day", as_index=False)
        .agg(
            trips=(trip_id_col, "count"),
            avg_temp=(temp_col, "mean"),
        )
        .rename(columns={"day": "date"})
        .sort_values("date")
    )

    return daily

@st.cache_data
def load_data():
    df = _read_csv(TRIPS_PATH)
    top20 = _read_csv(TOP20_PATH, index_col=0)
    return df, top20

# ----------------------------
# Load data
# ----------------------------
df, top20 = load_data()

# ----------------------------
# Sidebar navigation
# ----------------------------
page = st.sidebar.selectbox(
    "Aspect Selector",
    [
        "Intro",
        "Most popular stations",
        "Weather component and bike usage",
        "Interactive map",
        "Recommendations",
    ],
)

# ----------------------------
# Intro
# ----------------------------
if page == "Intro":
    st.subheader("Purpose of the Dashboard")

    st.markdown(
        """
        This dashboard explores Citi Bike usage patterns in New York City to better understand
        bike shortages and uneven station availability.

        The analysis focuses on:
        - Station popularity and demand concentration
        - The relationship between weather and ridership
        - Spatial trip patterns across the city
        """
    )

    intro_img_path = BASE_DIR / "bike_pic.jpg"
    if intro_img_path.exists():
        st.image(str(intro_img_path), caption="Citi Bike usage across New York City", use_container_width=True)

# ----------------------------
# Bar chart page
# ----------------------------
elif page == "Most popular stations":
    st.subheader("Top 20 Most Popular Start Stations")

    st.markdown(
        """
        This bar chart shows the **20 most frequently used start stations**.
        These stations represent the highest-demand areas and are key targets for
        bike redistribution to reduce availability complaints.
        """
    )

    required_cols = {"start_station_name", "value"}
    if not required_cols.issubset(top20.columns):
        st.error(
            f"top20_station.csv is missing required columns. Expected {required_cols}, "
            f"but got: {set(top20.columns)}"
        )
        st.stop()

    fig_bar = px.bar(
        top20,
        x="start_station_name",
        y="value",
        title="Top 20 Most Popular Start Stations in NYC",
        labels={"start_station_name": "Start Station", "value": "Trips"},
    )
    fig_bar.update_layout(xaxis_tickangle=-45, height=600)
    st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------------
# Dual axis line chart page
# ----------------------------
elif page == "Weather component and bike usage":
    st.subheader("Trips vs Temperature Over Time")

    daily = build_daily(df)

    # Inform user if temperature has missing tail (common when weather coverage ends early)
    last_temp_date = daily.loc[daily["avg_temp"].notna(), "date"].max()
    if pd.notna(last_temp_date) and last_temp_date < daily["date"].max():
        st.warning(
            f"Temperature data is missing after {last_temp_date.date()}. "
            "The temperature line stops where weather data ends."
        )

    fig_line = make_subplots(specs=[[{"secondary_y": True}]])

    fig_line.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["trips"],
            name="Daily Trips",
            line=dict(color="#1f77b4", width=3),
        ),
        secondary_y=False,
    )

    fig_line.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["avg_temp"],
            name="Avg Temp (°C)",
            line=dict(color="#d62728", width=3),
        ),
        secondary_y=True,
    )

    fig_line.update_layout(
        title="Daily Citi Bike Trips vs Average Temperature (NYC, 2022)",
        xaxis_title="Date",
        plot_bgcolor="white",
        height=600,
    )

    fig_line.update_yaxes(title_text="Trips", secondary_y=False)
    fig_line.update_yaxes(title_text="Avg Temp (°C)", secondary_y=True)

    st.plotly_chart(fig_line, use_container_width=True)

# ----------------------------
# Kepler map
# ----------------------------
elif page == "Interactive map":
    st.subheader("Kepler.gl Map: Trip Patterns in NYC")

    # Prefer the notebook-aligned path, but allow a fallback if you move the file later.
    candidate_paths = [
        MAP_PATH,
        "maps/kepler_top300.html",
        str(BASE_DIR / "Notebooks" / "MAPPS" / "kepler_top300.html"),
        str(BASE_DIR / "maps" / "kepler_top300.html"),
    ]
    map_found = next((p for p in candidate_paths if os.path.exists(p)), None)

    if map_found is None:
        st.error(f"Map file not found. Tried: {candidate_paths}")
        st.stop()

    with open(map_found, "r", encoding="utf-8") as f:
        html_data = f.read()
    components.html(html_data, height=800, scrolling=True)

with st.expander("How to read this map", expanded=True):
    st.markdown(
        """
        **What this map shows**
        - The map visualizes **Citi Bike trip patterns in New York City** using an interactive Kepler.gl map.
        - Each line represents a **frequently traveled route** between a start and end location.
        - Thicker and brighter routes indicate **higher trip volumes**.

        **How the data was prepared**
        - Individual trips were **aggregated by origin–destination pairs** (start → end coordinates).
        - A **trip count** was calculated for each unique route.
        - To improve performance and readability, only the **top 300 most-used routes** are displayed.
        - All data was **filtered to NYC coordinates** to ensure geographic accuracy.

        **Why this matters**
        - Highlights major travel corridors and high-demand areas.
        - Helps identify where bike rebalancing and station capacity adjustments may be needed.
        - Provides spatial context to complement the time-series and station-level analyses in this dashboard.
        """
    )

# ----------------------------
# Recommendations
# ----------------------------
elif page == "Recommendations":
    st.subheader("Recommendations")

    rec_img_path = BASE_DIR / "business_pic.jpg"
    if rec_img_path.exists():
        st.image(
            str(rec_img_path),
            caption="Strategic recommendations for Citi Bike operations",
            use_container_width=True,
        )

    st.markdown(
        """
        Based on the analysis presented in this dashboard, several key recommendations emerge.

        ## Strategic Insights & Implications

        ### 1. Target High-Demand Stations
        Stations in central and lower Manhattan consistently record the highest trip volumes, indicating sustained commuter and tourist demand. These locations should be prioritized for proactive bike rebalancing, higher dock capacity, and faster maintenance response times. Ensuring bike availability in these areas can reduce user frustration, increase ride completion rates, and maximize system utilization.

        ### 2. Plan for Seasonal Demand
        Citi Bike usage shows a strong seasonal pattern, with demand peaking during warmer months and declining sharply in winter. This suggests that staffing, bike inventory, and maintenance schedules should be adjusted seasonally. During peak months, expanding capacity and rebalancing frequency can meet higher demand, while winter operations can focus on cost efficiency and preventative maintenance.

        ### 3. Address Spatial Imbalances
        Certain neighborhoods exhibit consistently lower usage, even during high-demand periods. This may indicate mismatches between station placement and user needs, limited awareness, or connectivity gaps. These areas present opportunities for targeted promotions, station relocation, or integration with other transit options to improve adoption and equity of access.

        ### 4. Use Geospatial Insights
        The Kepler.gl map highlights high-traffic travel corridors across the city, revealing how riders move between neighborhoods. These spatial patterns can inform infrastructure investments, such as protected bike lanes, station expansion, and street design improvements. They also provide evidence to support data-driven policy decisions related to urban mobility and sustainability.
        """
    )

