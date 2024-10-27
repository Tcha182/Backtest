import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from numerize import numerize  # Install this with 'pip install numerize'

output_dir = "simulation_outputs"

# Load data
@st.cache_data
def load_results():
    results_df = pd.read_csv(f"{output_dir}/simulation_results.csv")
    summary_table = pd.read_csv(f"{output_dir}/summary_table.csv")
    return results_df, summary_table

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
    # Min value and delta vs invested for S&P 500
    sp500_min_value = selected_data[selected_data['Strategy'] == 'S&P 500']['Min_End_Value'].values[0]
    display_metric("Min End Value", sp500_min_value, mean_invested_amount)

with col2:
    # Median value and delta vs invested for S&P 500
    sp500_median_value = selected_data[selected_data['Strategy'] == 'S&P 500']['Median_End_Value'].values[0]
    display_metric("Median End Value", sp500_median_value, mean_invested_amount)

# Column layout for Leveraged S&P 500 metrics
st.subheader("Leveraged S&P 500 Strategy")
col3, col4 = st.columns(2)

with col3:
    # Min value and delta vs invested for Leveraged S&P 500
    leveraged_min_value = selected_data[selected_data['Strategy'] == 'Leveraged S&P 500']['Min_End_Value'].values[0]
    display_metric("Min End Value", leveraged_min_value, mean_invested_amount)

with col4:
    # Median value and delta vs invested for Leveraged S&P 500
    leveraged_median_value = selected_data[selected_data['Strategy'] == 'Leveraged S&P 500']['Median_End_Value'].values[0]
    display_metric("Median End Value", leveraged_median_value, mean_invested_amount)

# Load and display distribution plot for selected duration
st.subheader(f"Distribution of End Portfolio Values for {selected_duration}-Year Duration")
dist_path = f"{output_dir}/distribution_{selected_duration}_years.png"
if os.path.exists(dist_path):
    st.image(dist_path)

# Display risk curve
st.subheader("Risk Curve: Likelihood of Negative Returns by Duration")
risk_curve_path = f"{output_dir}/risk_curve.png"
if os.path.exists(risk_curve_path):
    st.image(risk_curve_path)

# Display box plot of final portfolio values by duration and strategy
st.subheader("Box Plot of Final Portfolio Values by Duration and Strategy")
box_plot_path = f"{output_dir}/box_plot.png"
if os.path.exists(box_plot_path):
    st.image(box_plot_path)
