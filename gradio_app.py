import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import re
import io
import logging

from market_object import load_data
from calculate_holdings import rebalance_portfolio
from factor_function import (
    Momentum6m, Momentum12m, Momentum1m, ROE, ROA, 
    P2B, NextFYrEarns, OneYrPriceVol,
    AccrualsAssets, ROAPercentage, OneYrAssetGrowth, OneYrCapEXGrowth, BookPrice
)

FACTOR_MAP = {
    'ROE using 9/30 Data': ROE,
    'ROA using 9/30 Data': ROA,
    '12-Mo Momentum %': Momentum12m,
    '6-Mo Momentum %': Momentum6m,
    '1-Mo Momentum %': Momentum1m,
    'Price to Book Using 9/30 Data': P2B,
    'Next FY Earns/P': NextFYrEarns,
    '1-Yr Price Vol %': OneYrPriceVol,
    'Accruals/Assets': AccrualsAssets,
    'ROA %': ROAPercentage,
    '1-Yr Asset Growth %': OneYrAssetGrowth,
    '1-Yr CapEX Growth %': OneYrCapEXGrowth,
    'Book/Price': BookPrice
}

SECTOR_OPTIONS = ['Consumer', 'Technology', 'Financials', 'Industrials', 'Healthcare']

def run_analysis(selected_factors, restrict_fossil_fuels, selected_sectors, start_year, end_year, initial_aum, verbosity):
    factor_objects = [FACTOR_MAP[name]() for name in selected_factors]

    rdata = load_data(
        restrict_fossil_fuels=restrict_fossil_fuels,
        use_supabase=True,
        data_path=None,
        show_loading_progress=True,
        sectors=selected_sectors if selected_sectors else None
    )

    rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(lambda x: x.split('-')[0].strip())
    rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year

    cols_to_keep = ['Ticker', 'Year']
    if 'Ending Price' in rdata.columns:
        cols_to_keep.append('Ending Price')
    elif 'Ending_Price' in rdata.columns:
        rdata['Ending Price'] = rdata['Ending_Price']
        cols_to_keep.append('Ending Price')

    for factor in selected_factors:
        if factor in rdata.columns:
            cols_to_keep.append(factor)

    rdata = rdata[cols_to_keep]

    results = rebalance_portfolio(
        rdata, factor_objects,
        start_year=start_year,
        end_year=end_year,
        initial_aum=initial_aum,
        verbosity=verbosity,
        restrict_fossil_fuels=restrict_fossil_fuels
    )

    # Build performance table
    perf_data = {
        'Year': results['years'],
        'Portfolio Value': [f"${v:,.2f}" for v in results['portfolio_values']],
    }

    if len(results['portfolio_values']) > 1:
        yoy_returns = ['-']
        for i in range(1, len(results['portfolio_values'])):
            ret = ((results['portfolio_values'][i] / results['portfolio_values'][i-1]) - 1) * 100
            yoy_returns.append(f"{ret:.2f}%")
        perf_data['YoY Return'] = yoy_returns

    if 'benchmark_returns' in results and results['benchmark_returns']:
        perf_data['Benchmark Return'] = ['-'] + [f"{r:.2f}%" for r in results['benchmark_returns']]

    perf_df = pd.DataFrame(perf_data)

    # Plot portfolio growth
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(results['years'], results['portfolio_values'], label='Portfolio', marker='o')
    if 'benchmark_returns' in results and results['benchmark_returns']:
        benchmark_values = [initial_aum]
        for ret in results['benchmark_returns']:
            benchmark_values.append(benchmark_values[-1] * (1 + ret / 100))
        ax.plot(results['years'][1:], benchmark_values[1:], label='Russell 2000', linestyle='--')
    ax.set_title("Portfolio Growth")
    ax.set_xlabel("Year")
    ax.set_ylabel("Value ($)")
    ax.legend()
    ax.grid(True)

    # Save CSV
    csv_path = f"/tmp/performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    perf_df.to_csv(csv_path, index=False)

    # Build structured summaries
    summary_main = f"""\
**Initial Portfolio Value:** ${results['portfolio_values'][0]:,.2f}  
**Final Portfolio Value after {results['years'][-1]}:** ${results['portfolio_values'][-1]:,.2f}  
**Overall Growth ({results['years'][0]}–{results['years'][-1]}):** {((results['portfolio_values'][-1] / results['portfolio_values'][0] - 1) * 100):.2f}%
"""

    summary_metrics = f"""\
- **Annualized Return (Portfolio):** {results.get('portfolio_annualized_return', 'N/A')}%  
- **Annualized Return (Benchmark):** {results.get('benchmark_annualized_return', 'N/A')}%  
- **Annualized Volatility (Portfolio):** {results.get('portfolio_volatility', 'N/A')}%  
- **Annualized Volatility (Benchmark):** {results.get('benchmark_volatility', 'N/A')}%  
- **Active Volatility:** {results.get('active_volatility', 'N/A')}%  
- **Information Ratio:** {results.get('information_ratio', 'N/A')}
"""

    summary_advanced = f"""\
- **Risk-Free Rate Source:** FRED (Oct 1)  
- **Max Drawdown (Portfolio):** {results.get('portfolio_max_drawdown', 'N/A')}%  
- **Max Drawdown (Benchmark):** {results.get('benchmark_max_drawdown', 'N/A')}%  
- **Sharpe Ratio (Portfolio):** {results.get('portfolio_sharpe', 'N/A')}  
- **Sharpe Ratio (Benchmark):** {results.get('benchmark_sharpe', 'N/A')}  
- **Yearly Win Rate vs Benchmark:** {results.get('win_rate', 'N/A')}%
"""

    return fig, perf_df, csv_path, summary_main, summary_metrics, summary_advanced

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 📊 Factor-Lake Portfolio Analysis (Gradio Edition)")

    with gr.Row():
        restrict_fossil_fuels = gr.Checkbox(label="Restrict Fossil Fuel Companies?", value=False)
        selected_sectors = gr.CheckboxGroup(label="Select Sectors to Run (None runs all)", choices=SECTOR_OPTIONS)

    selected_factors = gr.CheckboxGroup(label="Select Factors", choices=list(FACTOR_MAP.keys()))
    start_year = gr.Number(label="Start Year", value=2002, precision=0)
    end_year = gr.Number(label="End Year", value=2023, precision=0)
    initial_aum = gr.Number(label="Initial AUM ($)", value=1, precision=2)
    verbosity = gr.Slider(label="Verbosity Level", minimum=0, maximum=3, step=1, value=1)

    run_button = gr.Button("Run Analysis")

    output_plot = gr.Plot()
    output_table = gr.Dataframe()

    with gr.Accordion("📈 Final Summary", open=True):
        output_summary_main = gr.Markdown()

    with gr.Accordion("📊 Performance Metrics", open=False):
        output_summary_metrics = gr.Markdown()

    with gr.Accordion("📉 Advanced Backtest Stats", open=False):
        output_summary_advanced = gr.Markdown()
        
    output_csv = gr.File(label="Download CSV")
    def on_run(factors, ff, sectors, sy, ey, aum, verb):
        return run_analysis(factors, ff, sectors, int(sy), int(ey), float(aum), int(verb))

    run_button.click(
        fn=on_run,
        inputs=[selected_factors, restrict_fossil_fuels, selected_sectors, start_year, end_year, initial_aum, verbosity],
        outputs=[
            output_plot,
            output_table,
            output_csv,
            output_summary_main,
            output_summary_metrics,
            output_summary_advanced
        ]
    )


logging.getLogger("gradio").setLevel(logging.ERROR)

launch_info = demo.launch(share=True)
public_url = launch_info.get("share_url")

if public_url:
    print(f"\n🚀 App is live! Click here to open: {public_url}\n")
    print("🔗 This link is temporary and will expire in 1 week.\n")
else:
    print("\n⚠️ App launched, but no public URL was returned.\n")

