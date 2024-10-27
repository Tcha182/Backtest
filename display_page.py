import streamlit as st
import pandas as pd
from numerize import numerize
import gcs_utils
import os

# Specify your GCS bucket name
GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")

# Load data from GCS
@st.cache_data
def load_results():
    results_data = gcs_utils.download_from_gcs(GS_BUCKET_NAME, "data/simulation_results.csv")
    summary_data = gcs_utils.download_from_gcs(GS_BUCKET_NAME, "data/summary_table.csv")
    
    results_df = pd.read_csv(results_data)
    summary_table = pd.read_csv(summary_data)
    
    return results_df, summary_table

# Helper function to get or download a plot image
def get_or_download_plot(blob_path):
    """Checks if the image is in session state; if not, downloads and stores it."""
    if blob_path not in st.session_state:
        st.session_state[blob_path] = gcs_utils.download_from_gcs(GS_BUCKET_NAME, blob_path)
    return st.session_state[blob_path]

# Load results data
results_df, summary_table = load_results()

# Interactive slider for duration
selected_duration = st.slider(
    "Select Duration (Years)", 
    min_value=int(results_df['Duration (Years)'].min()), 
    max_value=int(results_df['Duration (Years)'].max())
)

# Filter data for the selected duration
selected_data = summary_table[summary_table['Duration (Years)'] == selected_duration]

# Get mean invested amount
mean_invested_amount = selected_data['Mean_Invested_Amount'].mean()
mean_invested_display = numerize.numerize(mean_invested_amount, 1)

# Display Mean Invested Amount prominently
st.metric(label="Invested Amount", value=f"€{mean_invested_display}")

# Define a function to format values and calculate deltas with correct delta color and direction
def display_metric(label, value, invested_amount):
    formatted_value = f"€{numerize.numerize(value, 1)}"
    delta_value = value - invested_amount
    delta = f"€{numerize.numerize(abs(delta_value), 1)}"
    delta_color = "normal"
    st.metric(label=label, value=formatted_value, delta=f"-{delta}" if delta_value < 0 else delta, delta_color=delta_color)

# Column layout for S&P 500 metrics
st.subheader("S&P 500 Strategy")
col1, col2 = st.columns(2)

with col1:
    sp500_min_value = selected_data[selected_data['Strategy'] == 'S&P 500']['Min_End_Value'].values[0]
    display_metric("Min End Value", sp500_min_value, mean_invested_amount)

with col2:
    sp500_median_value = selected_data[selected_data['Strategy'] == 'S&P 500']['Median_End_Value'].values[0]
    display_metric("Median End Value", sp500_median_value, mean_invested_amount)

# Column layout for Leveraged S&P 500 metrics
st.subheader("Leveraged S&P 500 Strategy")
col3, col4 = st.columns(2)

with col3:
    leveraged_min_value = selected_data[selected_data['Strategy'] == 'Leveraged S&P 500']['Min_End_Value'].values[0]
    display_metric("Min End Value", leveraged_min_value, mean_invested_amount)

with col4:
    leveraged_median_value = selected_data[selected_data['Strategy'] == 'Leveraged S&P 500']['Median_End_Value'].values[0]
    display_metric("Median End Value", leveraged_median_value, mean_invested_amount)

# Load and display distribution plot for selected duration
st.subheader(f"Distribution of End Portfolio Values for {selected_duration}-Year Duration")
dist_blob_path = f"plots/distribution_{selected_duration}_years.png"
dist_image = get_or_download_plot(dist_blob_path)
st.image(dist_image)

# Load and display risk curve for selected duration
st.subheader(f"Risk Curve for {selected_duration}-Year Duration")
risk_curve_blob_path = f"plots/risk_curve_{selected_duration}_years.png"
risk_curve_image = get_or_download_plot(risk_curve_blob_path)
st.image(risk_curve_image)

# Load and display box plot for selected duration
st.subheader(f"Box Plot of Final Portfolio Values for {selected_duration}-Year Duration")
box_plot_blob_path = f"plots/box_plot_{selected_duration}_years.png"
box_plot_image = get_or_download_plot(box_plot_blob_path)
st.image(box_plot_image)
