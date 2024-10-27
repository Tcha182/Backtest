# simulation_page.py

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
from numerize import numerize  # Make sure to install numerize

# Set up logging to capture errors
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

st.title("Optimized Investment Simulation")

@st.cache_data
def load_data():
    ticker = '^GSPC'
    sp500_data = yf.download(ticker, start='1930-01-01', end=datetime.today().strftime('%Y-%m-%d'))
    sp500_data = sp500_data['Adj Close']
    return sp500_data

# Set up directory to store outputs
output_dir = "simulation_outputs"
os.makedirs(output_dir, exist_ok=True)

# Load data
data_load_state = st.text('Loading data...')
daily_prices = load_data()
data_load_state.text('Data loaded successfully!')

# Simulation parameters
num_simulations = st.number_input('Number of Simulations', min_value=100, max_value=1000000, value=1000, step=100)
min_duration_years = st.number_input('Minimum Duration (Years)', min_value=1, max_value=30, value=1, step=1)
max_duration_years = st.number_input('Maximum Duration (Years)', min_value=1, max_value=30, value=20, step=1)
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
    daily_fee = (1 + annual_fee) ** (1 / 252) - 1
    daily_returns = daily_returns * leverage - daily_fee

    cumulative_returns = np.cumprod(1 + daily_returns[:duration_days])
    reverse_cumulative_returns = cumulative_returns[-1] / cumulative_returns[:duration_days]
    future_values = daily_investment * reverse_cumulative_returns[:duration_days]

    total_invested = daily_investment * duration_days
    total_value = np.sum(future_values)
    total_fee = annual_fee * (duration_days / 252) * total_invested
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
    for i in range(0, len(simulation_args), batch_size):
        batch_args = simulation_args[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(simulate_investment, batch_args))
            simulation_results.extend([res for res in batch_results if res is not None])

    return simulation_results

# Run simulations and save results
progress_bar = st.progress(0)
status_text = st.empty()

status_text.text("Running simulations for S&P 500")
results_sp500 = run_simulations(num_simulations, min_duration_days, max_duration_days, daily_prices, daily_investment, sp500_annual_fee, leverage=1.0)
progress_bar.progress(0.5)

status_text.text("Running simulations for Leveraged S&P 500")
results_leveraged = run_simulations(num_simulations, min_duration_days, max_duration_days, daily_prices, daily_investment, leveraged_annual_fee, leverage=2.0)
progress_bar.progress(1.0)

# Save results to DataFrame
all_results = results_sp500 + results_leveraged
results_df = pd.DataFrame(all_results)
results_df['Strategy'] = ['S&P 500'] * len(results_sp500) + ['Leveraged S&P 500'] * len(results_leveraged)
results_df['Duration (Years)'] = (results_df['Duration (Days)'] / 252).round().astype(int)
results_df.to_csv(f"{output_dir}/simulation_results.csv", index=False)

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

# Format numbers in summary table using `numerize`
summary_table['Mean_End_Value'] = summary_table['Mean_End_Value'].apply(lambda x: numerize.numerize(x, 1))
summary_table['Median_End_Value'] = summary_table['Median_End_Value'].apply(lambda x: numerize.numerize(x, 1))
summary_table['Min_End_Value'] = summary_table['Min_End_Value'].apply(lambda x: numerize.numerize(x, 1))
summary_table['Max_End_Value'] = summary_table['Max_End_Value'].apply(lambda x: numerize.numerize(x, 1))
summary_table['Mean_Invested_Amount'] = summary_table['Mean_Invested_Amount'].apply(lambda x: numerize.numerize(x, 1))
summary_table['Mean_Fee'] = summary_table['Mean_Fee'].apply(lambda x: numerize.numerize(x, 1))

summary_table.to_csv(f"{output_dir}/summary_table.csv", index=False)

# Create plots
from matplotlib.ticker import FuncFormatter

def currency_format(x, pos):
    return f'€{x:,.0f}'

for duration in sorted(results_df['Duration (Years)'].unique()):
    duration_data = results_df[results_df['Duration (Years)'] == duration]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(data=duration_data, x='End Portfolio Value (€)', hue='Strategy', kde=True, ax=ax)
    
    avg_invested = duration * 12 * monthly_investment
    ax.axvline(avg_invested, color='red', linestyle='--', label=f'Average Invested (€{avg_invested:,.2f})')
    ax.set_title(f"End Portfolio Value Distribution for {duration}-Year Duration")
    ax.set_xlabel("End Portfolio Value (€)")
    ax.set_ylabel("Frequency")
    ax.xaxis.set_major_formatter(FuncFormatter(currency_format))
    ax.legend()
    fig.savefig(f"{output_dir}/distribution_{duration}_years.png")

# Risk Curve
risk_curve = results_df.groupby(['Duration (Years)', 'Strategy'], as_index=False).apply(
    lambda x: pd.Series({
        "Negative Return Probability (%)": (x['Total Return'] < 0).mean() * 100
    })
).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=risk_curve, x='Duration (Years)', y='Negative Return Probability (%)', hue='Strategy', hue_order=['S&P 500', 'Leveraged S&P 500'], ax=ax)
ax.set_title("Risk Curve: Likelihood of Negative Returns by Duration")
ax.set_xlabel("Investment Duration (Years)")
ax.set_ylabel("Probability of Negative Returns (%)")
fig.savefig(f"{output_dir}/risk_curve.png")

fig, ax = plt.subplots(figsize=(12, 6))
sns.boxplot(data=results_df, x='Duration (Years)', y='End Portfolio Value (€)', hue='Strategy', ax=ax)
ax.set_title("Final Portfolio Values by Duration and Strategy")
ax.set_xlabel("Investment Duration (Years)")
ax.set_ylabel("End Portfolio Value (€)")
fig.savefig(f"{output_dir}/box_plot.png")
