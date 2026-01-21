import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from streamlit.components.v1 import html as st_html

# -----------------------------
# Global style
# -----------------------------
pio.templates.default = "plotly_white"

st.set_page_config(
    page_title="NYC Citi Bike Supply Insights",
    layout="wide"
)

# -----------------------------
# Load reduced sample (under 25MB)
# -----------------------------
@st.cache_data
def load_data():
    # Use your existing small sample (shown in your folder screenshot)
    # If your file is elsewhere, update this one line.
    return pd.read_csv("Data/Processed/sample_citibike_2022.csv")

df = load_data()

# -----------------------------
# Robust type handling (no KeyErrors)
# -----------------------------

# started_at (required for time series)
if "started_at" in df.columns:
    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
else:
    st.error("Column 'started_at' is missing from the dataset. The dashboard needs it.")
    st.stop()

# date (derive from started_at if missing)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
else:
    df["date"] = pd.to_datetime(df["started_at"].dt.date, errors="coerce")

# temperature column (TAVG)
if "TAVG" in df.columns:
    df["TAVG"] = pd.to_numeric(df["TAVG"], errors="coerce")
else:
    # Allow app to run even if TAVG missing, but temperature chart won’t work
    df["TAVG"] = np.nan

# coordinates (only if present)
for c in ["start_lat", "start_lng", "end_lat", "end_lng"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# trip duration (optional)
# If trip_minutes already exists, keep it numeric
if "trip_minutes" in df.columns:
    df["trip_minutes"] = pd.to_numeric(df["trip_minutes"], errors="coerce")
else:
    # compute only if ended_at exists
    if "ended_at" in df.columns:
        df["ended_at"] = pd.to_datetime(df["ended_at"], errors="coerce")
        df["trip_minutes"] = (df["ended_at"] - df["started_at"]).dt.total_seconds() / 60
    else:
        df["trip_minutes"] = np.nan  # available but empty

# -----------------------------
# Sidebar navigation (pages)
# -----------------------------
pages = [
    "Intro",
    "Trips vs Temperature",
    "Popular Stations",
    "Top 300 Routes Map",
    "Extra Insight",
    "Recommendations"
]
page = st.sidebar.selectbox("Select a page", pages)

# Optional filters (available across pages)
st.sidebar.markdown("### Filters")

if "member_casual" in df.columns:
    rider_options = sorted([x for x in df["member_casual"].dropna().unique()])
    member_filter = st.sidebar.multiselect("Rider type", options=rider_options, default=rider_options)
    df_f = df[df["member_casual"].isin(member_filter)].copy()
else:
    df_f = df.copy()
    st.sidebar.info("No 'member_casual' column found; rider-type filter disabled.")

# -----------------------------
# PAGE: Intro
# -----------------------------
if page == "Intro":
    st.title("NYC Citi Bike Supply Insights Dashboard")
    st.write(
        "Purpose: identify demand patterns and route concentrations to help the strategy team "
        "improve bike availability (supply) across NYC."
    )

    st.markdown(
        """
**What’s inside**
- **Trips vs Temperature:** how weather relates to daily usage.
- **Popular Stations:** where demand concentrates (pickup pressure).
- **Top 300 Routes Map:** the most frequent flows between station pairs (rebalancing targets).
- **Extra Insight:** an additional view to support supply decisions.
- **Recommendations:** actions for fleet allocation and station operations.
        """
    )

    # Quick KPIs (robust to missing columns)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trips (sample)", f"{len(df_f):,}")

    if "start_station_name" in df_f.columns:
        col2.metric("Unique start stations", f"{df_f['start_station_name'].nunique():,}")
    else:
        col2.metric("Unique start stations", "N/A")

    avg_minutes = df_f["trip_minutes"].dropna().mean()
    col3.metric("Avg trip minutes", f"{avg_minutes:.1f}" if np.isfinite(avg_minutes) else "N/A")

    avg_tavg = df_f["TAVG"].dropna().mean()
    col4.metric("Avg TAVG", f"{avg_tavg:.1f}" if np.isfinite(avg_tavg) else "N/A")

# -----------------------------
# PAGE: Trips vs Temperature
# -----------------------------
elif page == "Trips vs Temperature":
    st.header("Trips vs Average Temperature (TAVG)")

    if df_f["TAVG"].dropna().empty:
        st.warning("TAVG is missing/empty in this dataset, so the temperature comparison cannot be plotted.")
        st.stop()

    # daily aggregation
    if "ride_id" in df_f.columns:
        daily = (
            df_f.dropna(subset=["date"])
                .groupby("date", as_index=False)
                .agg(trips=("ride_id", "count"), avg_temp=("TAVG", "mean"))
                .dropna(subset=["avg_temp"])
        )
    else:
        daily = (
            df_f.dropna(subset=["date"])
                .groupby("date", as_index=False)
                .agg(trips=("started_at", "size"), avg_temp=("TAVG", "mean"))
                .dropna(subset=["avg_temp"])
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["trips"],
        name="Trips", mode="lines",
        line=dict(color="#1f77b4", width=2),
        yaxis="y1"
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["avg_temp"],
        name="Avg Temp (TAVG)", mode="lines",
        line=dict(color="#ff7f0e", width=2),
        yaxis="y2"
    ))

    fig.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Avg Temp (TAVG)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=520
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
**Interpretation**
- Trip volume generally increases as temperatures become more comfortable, indicating weather-driven demand.
- From a supply perspective, warmer periods typically require **higher bike availability** and **more frequent rebalancing**.
        """
    )

# -----------------------------
# PAGE: Popular Stations
# -----------------------------
elif page == "Popular Stations":
    st.header("Most Popular Start Stations")

    if "start_station_name" not in df_f.columns:
        st.warning("Column 'start_station_name' not found in this dataset.")
        st.stop()

    top_n = st.slider("Top N stations", 10, 50, 20)

    popular = (
        df_f["start_station_name"]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    popular.columns = ["start_station_name", "trip_count"]

    fig = px.bar(
        popular,
        x="trip_count",
        y="start_station_name",
        orientation="h",
        labels={"trip_count": "Trips", "start_station_name": "Station"},
        color_discrete_sequence=["#1f77b4"]
    )
    fig.update_layout(height=650, title_x=0.02)
    fig.update_yaxes(categoryorder="total ascending")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
**Interpretation**
- These stations are demand hotspots and are the most likely to experience **stockouts**.
- Operations can mitigate shortages by prioritizing these stations for **morning replenishment** and **midday rebalancing**.
        """
    )

# -----------------------------
# PAGE: Top 300 Routes Map
# -----------------------------
elif page == "Top 300 Routes Map":
    st.header("Kepler.gl Map: Top 300 Routes (by trip count)")

    map_path = "maps/kepler_top300.html"
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        st_html(map_html, height=750, scrolling=True)

        st.markdown(
            """
**Interpretation**
- The map highlights the strongest station-to-station flows.
- These corridors are the best candidates for targeted rebalancing routes and staged inventory.
- Concentrated arcs suggest predictable commuting patterns; supply can be pre-positioned accordingly.
            """
        )
    else:
        st.error("Map file not found: maps/kepler_top300.html")

# -----------------------------
# PAGE: Extra Insight (uses only 'date' so it always works)
# -----------------------------
elif page == "Extra Insight":
    st.header("Extra Insight: Trips by Day of Week")

    df_tmp = df_f.dropna(subset=["date"]).copy()
    df_tmp["day_of_week"] = df_tmp["date"].dt.day_name()

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    counts = (
        df_tmp["day_of_week"]
        .value_counts()
        .reindex(order)
        .reset_index()
    )
    counts.columns = ["day_of_week", "trip_count"]

    fig = px.bar(
        counts,
        x="day_of_week",
        y="trip_count",
        labels={"day_of_week": "Day", "trip_count": "Trips"},
        color_discrete_sequence=["#1f77b4"]
    )
    fig.update_layout(height=520)

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
**Interpretation**
- Weekday peaks often reflect commuter-driven demand.
- Weekend patterns reflect leisure usage.
- Supply planning should shift bikes toward business districts on weekdays and recreational areas on weekends.
        """
    )

# -----------------------------
# PAGE: Recommendations
# -----------------------------
elif page == "Recommendations":
    st.header("Recommendations for Citi Bike Supply Strategy")

    st.markdown(
        """
**Operational recommendations**
1. **Prioritize replenishment** at the highest-demand start stations (Popular Stations page).
2. Use the **Top 300 routes** to define rebalancing corridors—optimize truck routes around the most frequent flows.
3. Increase inventory buffers during **warmer periods**, when trips rise (Trips vs Temperature page).

**Measurement**
- Track station stockout rates for top stations.
- Monitor corridor-level imbalances (inflow vs outflow) for top routes.
- Evaluate changes with A/B tests on rebalancing frequency and buffer targets.
        """
    )
