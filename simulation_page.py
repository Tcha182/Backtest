import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import seaborn as sns
import os
import logging
from dotenv import load_dotenv
from matplotlib.ticker import FuncFormatter
import gcs_utils  # Ensure you have the GCS utility module configured as shown previously

# Load environment variables
load_dotenv()
GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")

# Set up logging to capture errors
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.title("Optimized Investment Simulation")

@st.cache_data
def load_data():
    ticker = '^GSPC'
    sp500_data = yf.download(ticker, start='1928-01-01', end=datetime.today().strftime('%Y-%m-%d'))
    sp500_data = sp500_data['Adj Close']
    return sp500_data

# Load data
data_load_state = st.text('Loading data...')
daily_prices = load_data()
data_load_state.text('Data loaded successfully!')

# Simulation parameters
num_simulations = st.number_input('Number of Simulations', min_value=100, max_value=1000000, value=1000, step=100)
min_duration_years = st.number_input('Minimum Duration (Years)', min_value=1, max_value=40, value=1, step=1)
max_duration_years = st.number_input('Maximum Duration (Years)', min_value=1, max_value=40, value=30, step=1)
min_duration_days = int(min_duration_years * 252)
max_duration_days = int(max_duration_years * 252)

# Investment and fees
monthly_investment = 833.33
daily_investment = monthly_investment / 21
sp500_annual_fee = 0.25 / 100  # 0.25%
leveraged_annual_fee = 0.35 / 100  # 0.35%

# Function to run individual simulation
def simulate_investment(args):
    start_idx, duration_days, daily_prices_array, daily_investment, annual_fee, leverage = args
    end_idx = start_idx + duration_days
    if end_idx >= len(daily_prices_array):
        return None

    simulation_prices = daily_prices_array[start_idx:end_idx + 1].flatten()
    if len(simulation_prices) != duration_days + 1:
        return None

    daily_returns = np.diff(simulation_prices) / simulation_prices[:-1]
    daily_fee_rate = (1 + annual_fee) ** (1 / 252) - 1  # Daily fee as a percentage

    leveraged_daily_returns = daily_returns * leverage
    cumulative_returns = np.cumprod(1 + leveraged_daily_returns)

    invested_amounts = np.cumsum(np.full(duration_days, daily_investment))
    portfolio_values = invested_amounts * cumulative_returns
    daily_fees = portfolio_values * daily_fee_rate
    net_portfolio_values = portfolio_values - np.cumsum(daily_fees)

    total_invested = daily_investment * duration_days
    total_value = net_portfolio_values[-1]
    total_fee = np.sum(daily_fees)
    total_return = (total_value - total_invested) / total_invested
    annualized_return = (1 + total_return) ** (252 / duration_days) - 1

    return {
        'Start Date': daily_prices.index[start_idx],
        'Duration (Days)': duration_days,
        'Total Invested (€)': total_invested,
        'Total Fee (€)': total_fee,
        'End Portfolio Value (€)': total_value,
        'Total Return': total_return,
        'Annualized Return': annualized_return
    }

# Function to run multiple simulations
def run_simulations(num_simulations, min_duration_days, max_duration_days, daily_prices, daily_investment, annual_fee, leverage=1.0):
    total_days = len(daily_prices)
    possible_start_indices = np.arange(0, total_days - max_duration_days - 1)
    daily_prices_array = daily_prices.values

    simulation_args = []
    for _ in range(num_simulations):
        start_idx = np.random.choice(possible_start_indices)
        duration_days = np.random.randint(min_duration_days, max_duration_days + 1)
        simulation_args.append((start_idx, duration_days, daily_prices_array, daily_investment, annual_fee, leverage))

    simulation_results = []
    batch_size = 100
    progress_bar = st.progress(0)
    for i in range(0, len(simulation_args), batch_size):
        batch_args = simulation_args[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(simulate_investment, batch_args))
            simulation_results.extend([res for res in batch_results if res is not None])
        progress_bar.progress((i + batch_size) / len(simulation_args))

    return simulation_results

# Function to save plot to GCS
def save_fig_to_gcs(fig, file_name):
    local_path = f"{file_name}"  # Temporarily save locally
    fig.savefig(local_path)
    gcs_utils.upload_to_gcs(GS_BUCKET_NAME, local_path, f"plots/{file_name}")
    os.remove(local_path)  # Remove local file after upload
    plt.close(fig)  # Close figure to save memory

def currency_format(x, pos):
    return f'€{x:,.0f}'

# Button to start simulation
if st.button("Run Simulations"):
    # Run simulations and save results
    status_text = st.empty()
    
    status_text.text("Running simulations for S&P 500")
    results_sp500 = run_simulations(num_simulations, min_duration_days, max_duration_days, daily_prices, daily_investment, sp500_annual_fee, leverage=1.0)
    
    status_text.text("Running simulations for Leveraged S&P 500")
    results_leveraged = run_simulations(num_simulations, min_duration_days, max_duration_days, daily_prices, daily_investment, leveraged_annual_fee, leverage=2.0)
    
    # Save results to DataFrame
    all_results = results_sp500 + results_leveraged
    results_df = pd.DataFrame(all_results)
    results_df['Strategy'] = ['S&P 500'] * len(results_sp500) + ['Leveraged S&P 500'] * len(results_leveraged)
    results_df['Duration (Years)'] = (results_df['Duration (Days)'] / 252).round().astype(int)
    #results_df.to_csv("simulation_results.csv", index=False)
    gcs_utils.upload_to_gcs(GS_BUCKET_NAME, "simulation_results.csv", "data/simulation_results.csv")

    # Summary table
    summary_table = results_df.groupby(['Duration (Years)', 'Strategy']).agg(
        Mean_End_Value=('End Portfolio Value (€)', 'mean'),
        Median_End_Value=('End Portfolio Value (€)', 'median'),
        Min_End_Value=('End Portfolio Value (€)', 'min'),
        Max_End_Value=('End Portfolio Value (€)', 'max'),
        Mean_Invested_Amount=('Total Invested (€)', 'mean'),
        Mean_Fee=('Total Fee (€)', 'mean'),
        Positive_Return_Percentage=('Total Return', lambda x: (x > 0).mean() * 100)
    ).reset_index()
    #summary_table.to_csv("summary_table.csv", index=False)
    gcs_utils.upload_to_gcs(GS_BUCKET_NAME, "summary_table.csv", "data/summary_table.csv")

    # Create plots
    total_durations = len(results_df['Duration (Years)'].unique())
    chart_progress_bar = st.progress(0)

    for i, duration in enumerate(sorted(results_df['Duration (Years)'].unique()), 1):
        status_text.text(f"Creating distribution plot for {duration}-year duration")
        duration_data = results_df[results_df['Duration (Years)'] == duration]
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data=duration_data, x='End Portfolio Value (€)', hue='Strategy', kde=True, ax=ax)
        avg_invested = duration * 12 * monthly_investment
        ax.axvline(avg_invested, color='red', linestyle='--', label=f'Average Invested (€{avg_invested:,.0f})')
        ax.set_title(f"End Portfolio Value Distribution for {duration}-Year Duration")
        ax.set_xlabel("End Portfolio Value (€)")
        ax.get_yaxis().set_visible(False)
        ax.xaxis.set_major_formatter(FuncFormatter(currency_format))
        sns.despine(left=True)
        ax.legend()
        save_fig_to_gcs(fig, f"distribution_{duration}_years.png")
        chart_progress_bar.progress(i / (total_durations * 3))

    for i, duration in enumerate(sorted(results_df['Duration (Years)'].unique()), 1):
        status_text.text(f"Creating risk curve for {duration}-year duration")
        fig, ax = plt.subplots(figsize=(10, 6))
        risk_data = results_df.groupby(['Duration (Years)', 'Strategy'], as_index=False).apply(
            lambda x: pd.Series({"Negative Return Probability (%)": (x['Total Return'] < 0).mean() * 100})
        )
        sns.lineplot(data=risk_data, x='Duration (Years)', y='Negative Return Probability (%)', hue='Strategy', hue_order=['S&P 500', 'Leveraged S&P 500'], ax=ax)
        selected_risk_data = risk_data[risk_data['Duration (Years)'] == duration]
        sns.scatterplot(data=selected_risk_data, x='Duration (Years)', y='Negative Return Probability (%)', hue='Strategy', hue_order=['S&P 500', 'Leveraged S&P 500'], s=100, ax=ax, legend=False)
        for _, row in selected_risk_data.iterrows():
            ax.text(row['Duration (Years)'], row['Negative Return Probability (%)'] + 1, f"{row['Negative Return Probability (%)']:.1f}%", ha='center')
        ax.set_title("Risk Curve: Likelihood of Negative Returns by Duration")
        ax.set_xlabel("Investment Duration (Years)")
        ax.set_ylabel("Probability of Negative Returns (%)")
        sns.despine()
        save_fig_to_gcs(fig, f"risk_curve_{duration}_years.png")
        chart_progress_bar.progress((i + total_durations) / (total_durations * 3))

    for i, duration in enumerate(sorted(results_df['Duration (Years)'].unique()), 1):
        status_text.text(f"Creating box plot for {duration}-year duration")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.boxplot(data=results_df, x='Duration (Years)', y='End Portfolio Value (€)', hue='Strategy', palette="Greys", ax=ax, dodge=True, legend=False)
        sns.boxplot(data=results_df[results_df['Duration (Years)'] == duration], x='Duration (Years)', y='End Portfolio Value (€)', hue='Strategy', palette="bright", ax=ax)
        ax.set_title(f"Final Portfolio Values for {duration}-Year Duration")
        ax.set_xlabel("Investment Duration (Years)")
        ax.set_ylabel("End Portfolio Value (€)")
        ax.yaxis.set_major_formatter(FuncFormatter(currency_format))
        sns.despine()
        save_fig_to_gcs(fig, f"box_plot_{duration}_years.png")
        chart_progress_bar.progress((i + total_durations * 2) / (total_durations * 3))

    st.success("Simulations and chart creation completed successfully!")
    status_text.text("All tasks completed.")
