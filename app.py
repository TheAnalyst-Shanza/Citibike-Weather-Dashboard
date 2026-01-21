import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from streamlit.components.v1 import html as st_html

# -----------------------------
# Global Plotly light theme
# -----------------------------
pio.templates.default = "plotly_white"

# -----------------------------
# Page config (must be first Streamlit command)
# -----------------------------
st.set_page_config(page_title="NYC Citi Bike & Weather Dashboard", layout="wide")

st.title("NYC Citi Bike & Weather Dashboard")
st.write(
    "This dashboard shows popular Citi Bike stations, daily trip volume vs average temperature (TAVG), "
    "and an interactive Kepler.gl map of the top 300 routes."
)

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    # Your CSV is in the project root based on your directory listing
    df = pd.read_csv("citibike_weather_2022.csv")
    return df

df = load_data()

# Ensure correct dtypes
df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["TAVG"] = pd.to_numeric(df["TAVG"], errors="coerce")

# -----------------------------
# Layout
# -----------------------------
tab1, tab2 = st.tabs(["Charts", "Map (Top 300 Routes)"])

with tab1:
    col1, col2 = st.columns([1, 1])

    # -----------------------------
    # Bar chart: Top stations
    # -----------------------------
    with col1:
        st.subheader("Most Popular Start Stations")

        station_col = "start_station_name"
        top_n = st.slider("Select top N stations", 5, 30, 15)

        popular = df[station_col].value_counts().head(top_n).reset_index()
        popular.columns = [station_col, "trip_count"]

        fig_bar = px.bar(
            popular,
            x="trip_count",
            y=station_col,
            orientation="h",
            labels={"trip_count": "Number of Trips", station_col: "Station"},
            color_discrete_sequence=["#1f77b4"],
        )
        fig_bar.update_layout(height=600, title_x=0.02)
        fig_bar.update_yaxes(categoryorder="total ascending")

        st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------
    # Dual-axis chart: Trips vs TAVG
    # -----------------------------
    with col2:
        st.subheader("Daily Trips vs Average Temperature (TAVG)")

        daily = (
            df.dropna(subset=["date"])
              .groupby("date", as_index=False)
              .agg(trips=("ride_id", "count"), avg_temp=("TAVG", "mean"))
              .dropna(subset=["avg_temp"])
        )

        fig_dual = go.Figure()
        fig_dual.add_trace(
            go.Scatter(
                x=daily["date"], y=daily["trips"],
                name="Trips",
                mode="lines",
                line=dict(color="#1f77b4", width=2),
                yaxis="y1",
            )
        )
        fig_dual.add_trace(
            go.Scatter(
                x=daily["date"], y=daily["avg_temp"],
                name="Avg Temp (TAVG)",
                mode="lines",
                line=dict(color="#ff7f0e", width=2),
                yaxis="y2",
            )
        )

        fig_dual.update_layout(
            xaxis=dict(title="Date"),
            yaxis=dict(title="Trips"),
            yaxis2=dict(title="Avg Temperature (TAVG)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=600,
        )

        st.plotly_chart(fig_dual, use_container_width=True)

with tab2:
    st.subheader("Kepler.gl Map: Top 300 Routes")

    map_path = "maps/kepler_top300.html"  # your exported top-300 map
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        st_html(map_html, height=750, scrolling=True)
    else:
        st.error(
            "Map file not found. Please export it first:\n"
            "maps/kepler_top300.html"
        )
        st.write("Expected path:", os.path.abspath(map_path))
