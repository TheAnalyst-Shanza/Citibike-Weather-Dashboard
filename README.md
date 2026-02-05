# Citibike-Weather-Dashboard
# Citi Bike & Weather Analysis (2022)

## Project Overview
This project analyzes Citi Bike usage patterns in 2022 and examines how daily weather—specifically **average temperature**—relates to bike trip volume. The goal is to understand seasonality, station popularity, and behavioral differences using clear, reproducible visual analytics.

This repository is structured so that data processing is done once and reused across notebooks, reducing unnecessary complexity and improving performance.

---

## Data Sources
- **Citi Bike Trip Data (2022)**  
  Monthly CSV files provided by Citi Bike (Jersey City system)
- **Weather Data (2022)**  
  Daily weather observations, including average temperature

> Note: Raw and large processed data files are excluded from version control per GitHub size limits and course guidance.

---

## Data Preparation
- Daily trip counts were aggregated from raw trip data in a prior assignment.
- Weather data was cleaned to retain **only date and mean temperature** (min/max temperatures were dropped as they were not required for the analysis).
- Missing dates in the weather data were handled to ensure **full daily coverage for all of 2022**.
- A single merged dataset (`citibike_weather_merged_2022.csv`) was created and reused in subsequent notebooks to avoid reloading all raw CSVs multiple times.

---

## Methods & Visualizations

### 1. Seasonality Analysis (Dual-Axis Line Chart)
- Daily trip counts and average temperature were plotted on a dual-axis line chart.
- Distinct colors were used for each series to ensure readability.
- This visualization highlights the strong seasonal relationship between temperature and ridership.

### 2. Station Popularity (Bar Chart)
- A bar chart displays the **top 20 most frequented starting stations**.
- Seaborn styling and palettes were used, with adjustments made where default palettes did not provide sufficient visual distinction.

### 3. Categorical Analysis (Box Plot)
- A categorical variable (e.g., rider type or station category) was analyzed using a box plot.
- The plot highlights differences in central tendency, spread, and outliers across categories, providing insight into usage behavior.

### 4. Faceted Analysis (FacetGrid)
- A Seaborn FacetGrid was used to break down distributions across categories (e.g., by month or rider type).
- This approach allows seasonal and behavioral differences to be examined without aggregating away important variation.

---

## Tools & Libraries
- Python
- pandas
- matplotlib
- seaborn
- JupyterLab
- Git & GitHub

---

## Repository Structure
Citibike-Weather-Dashboard/
│
├── Notebooks/
│ ├── Citibike-Weather-Analysis.ipynb
│ └── Seaborn_Station_Seasonality_Box_Facet.ipynb
│
├── Data/
│ ├── Raw/ # ignored in Git
│ └── Processed/ # ignored in Git
│
├── README.md
└── .gitignore

## Citibike Dashboard Link
