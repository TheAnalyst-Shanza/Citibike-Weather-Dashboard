import numpy as np
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Citi Bike Strategy Dashboard", layout="wide")
st.title("Citi Bike Strategy Dashboard")
st.write("Interactive dashboard exploring station demand, weather impact, and trip patterns in NYC (2022).")

# ----------------------------
# Paths (repo-relative, Cloud-safe)
# ----------------------------
TRIPS_PATH = "Data/Processed/citibike_weather_daily_2022.csv"
TOP20_PATH = "Data/Processed/top20_station.csv"
MAP_PATH = "Notebooks/maps/kepler_top300.html"

# ----------------------------
# Load data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(TRIPS_PATH)
    top20 = pd.read_csv(TOP20_PATH, index_col=0)
    return df, top20

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

    # Intro image
    intro_img_path = os.path.join(BASE_DIR, "bike_pic.jpg")
    if os.path.exists(intro_img_path):
        st.image(intro_img_path, caption="Citi Bike usage across New York City", width=900)

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

    # Load top20 safely
    if not os.path.exists(TOP20_PATH):
        st.error(f"Top 20 file not found at: {TOP20_PATH}")
        st.stop()

    top20 = pd.read_csv(TOP20_PATH, index_col=0)

    # Validate expected columns
    required_cols = {"start_station_name", "value"}
    if not required_cols.issubset(top20.columns):
        st.error(
            f"top20_station.csv is missing required columns. "
            f"Expected {required_cols}, but got: {set(top20.columns)}"
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

    df_daily = df.sort_values("date")

    fig_line = make_subplots(specs=[[{"secondary_y": True}]])

    fig_line.add_trace(
        go.Scatter(
            x=df_daily["date"],
            y=df_daily["trip_count"],
            name="Daily Trips",
            line=dict(color="#1f77b4", width=3)
        ),
        secondary_y=False
    )

    fig_line.add_trace(
        go.Scatter(
            x=df_daily["date"],
            y=df_daily["avgTemp"],
            name="Avg Temp (°C)",
            line=dict(color="#d62728", width=3)
        ),
        secondary_y=True
    )

    fig_line.update_layout(
        title="Daily Citi Bike Trips vs Average Temperature (NYC, 2022)",
        xaxis_title="Date",
        plot_bgcolor="white",
        height=600
    )

    fig_line.update_yaxes(title_text="Trips", secondary_y=False)
    fig_line.update_yaxes(title_text="Avg Temp (°C)", secondary_y=True)

    st.plotly_chart(fig_line, use_container_width=True)

# ----------------------------
# Kepler map
# ----------------------------
elif page == "Interactive map":
    st.subheader("Kepler.gl Map: Trip Patterns in NYC")

    # If your kepler map is inside Notebooks/maps:
    MAP_PATH = os.path.join(BASE_DIR, "Notebooks", "maps", "kepler_top300.html")

    try:
        with open(MAP_PATH, "r", encoding="utf-8") as f:
            html_data = f.read()
        components.html(html_data, height=800, scrolling=True)
    except FileNotFoundError:
        st.error(f"Map file not found at: {MAP_PATH}")

# ----------------------------
# Recommendations
# ----------------------------
elif page == "Recommendations":
    st.subheader("Recommendations")

    # Recommendation image
    rec_img_path = os.path.join(BASE_DIR, "business_pic.jpg")
    if os.path.exists(rec_img_path):
        st.image(rec_img_path, caption="Strategic recommendations for Citi Bike operations", width=900)

    st.markdown(
        """
        Based on the analysis presented in this dashboard, several key recommendations emerge:

        1. **Target High-Demand Stations**  
           Stations in central and lower Manhattan consistently experience heavy usage and should be
           prioritized for bike rebalancing.

        2. **Plan for Seasonal Demand**  
           Bike usage peaks during warmer months and drops significantly in winter, suggesting that
           operational planning should account for seasonal variability.

        3. **Address Spatial Imbalances**  
           Some neighborhoods show persistent underutilization, presenting opportunities for
           redistribution or targeted promotions.

        4. **Use Geospatial Insights**  
           The Kepler.gl map reveals high-traffic corridors that can inform infrastructure and
           policy decisions.
        """
    )
