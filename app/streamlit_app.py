"""
Streamlit Application for Factor-Lake Portfolio Analysis
Interactive web interface for running factor-based portfolio backtests
"""
import sys
import os

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Add src directory to path by searching parent directories until a `src` folder
# is found. This makes the app runnable from different working directories
def _ensure_src_on_path():
    p = Path(__file__).resolve().parent
    # Look up to 6 parent levels for a sibling 'src' directory
    for _ in range(6):
        candidate = p / 'src'
        if candidate.is_dir():
            sys.path.insert(0, str(p))
            return
        p = p.parent
    # Fallback: use the original one-level-up heuristic
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'src')))

_ensure_src_on_path()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Import project modules
from src.market_object import load_data
from src.calculate_holdings import rebalance_portfolio
from src.factor_function import (
    Momentum6m, Momentum12m, Momentum1m, ROE, ROA, 
    P2B, NextFYrEarns, OneYrPriceVol,
    AccrualsAssets, ROAPercentage, OneYrAssetGrowth, OneYrCapEXGrowth, BookPrice
)
# Import from Visualizations (not in src)
from Visualizations.portfolio_growth_plot import plot_portfolio_growth

# Page configuration
st.set_page_config(
    page_title="Factor-Lake Portfolio Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Extensive styling options
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Alert boxes */
    .stAlert {
        margin-top: 1rem;
        border-radius: 10px;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #1f77b4;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Dataframes */
    .dataframe {
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* Checkboxes */
    .stCheckbox {
        padding: 5px 0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Success/Error messages */
    .element-container .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    
    .element-container .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    
    /* Custom card styling */
    .custom-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Hide Streamlit branding (optional) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive design adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'rdata' not in st.session_state:
    st.session_state.rdata = None
if 'results' not in st.session_state:
    st.session_state.results = None

# Factor mapping
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

# Sector options
SECTOR_OPTIONS = [
    'Consumer',
    'Technology',
    'Financials',
    'Industrials',
    'Healthcare'
]

def main():
    # Header
    st.markdown('<div class="main-header">Factor-Lake Portfolio Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Welcome to the Factor-Lake Portfolio Analysis tool! This application allows you to:
    - Select investment factors for portfolio construction
    - Apply fossil fuel restrictions and sector filters
    - Backtest portfolio performance from 2002-2023
    - Visualize portfolio growth vs. Russell 2000 benchmark
    """)
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("Configuration")
        # Data Source Selection
        st.subheader("Data Source")
        use_supabase = st.radio(
            "Select data source:",
            options=[True, False],
            format_func=lambda x: "Supabase (Cloud)" if x else "Local Excel File (🚧 Working on it)",
            index=0,
            help="Choose between cloud database or local Excel file"
        )

        excel_file = None
        uploaded_file = None
        if not use_supabase:
            st.info("🚧 **Excel/CSV upload feature is currently under development**")
            st.markdown("*Please use Supabase (Cloud) option for now.*")
            
            # Disabled file uploader (greyed out)
            uploaded_file = st.file_uploader(
                "Upload Excel/CSV file:",
                type=['xlsx', 'xls', 'csv'],
                help="Feature temporarily disabled - working on improvements",
                disabled=True
            )
            
            # Disabled text input (greyed out)
            st.markdown("**OR** enter Google Drive path (Colab only):")
            excel_file = st.text_input(
                "File path:",
                value="",
                placeholder="/content/drive/MyDrive/yourfolder/data.xlsx",
                help="Feature temporarily disabled - working on improvements",
                disabled=True
            )

        st.write("---")
        # Fossil Fuel Restriction
        st.subheader("ESG Filters")
        restrict_fossil_fuels = st.checkbox(
            "Restrict Fossil Fuel Companies",
            value=False,
            help="Exclude oil, gas, coal, and fossil energy companies"
        )
        st.write("---")
        # Sector Selection
        st.subheader("Sector Selection")
        sector_filter_enabled = st.checkbox("Enable Sector Filter", value=False)
        selected_sectors = []
        if sector_filter_enabled:
            selected_sectors = st.multiselect(
                "Select sectors to include:",
                options=SECTOR_OPTIONS,
                default=SECTOR_OPTIONS,
                help="Choose which sectors to include in the analysis"
            )
        st.write("---")
        # Date Range
        st.subheader("Analysis Period")
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Start Year", min_value=2002, max_value=2023, value=2002)
        with col2:
            end_year = st.number_input("End Year", min_value=2002, max_value=2023, value=2023)
        st.write("---")
        # Initial Investment
        st.subheader("Initial Investment")
        initial_aum = st.number_input(
            "Initial AUM ($)",
            min_value=1.0,
            max_value=1000000000.0,
            value=1000000.0,
            step=100000.0,
            format="%.2f",
            help="Starting portfolio value in dollars"
        )
        st.write("---")
        # Verbosity
        st.subheader("Output Detail")
        verbosity_level = st.select_slider(
            "Verbosity Level",
            options=[0, 1, 2, 3],
            value=1,
            format_func=lambda x: ["Silent", "Basic", "Detailed", "Debug"][x],
            help="Control the amount of detail in output logs"
        )
        show_loading = st.checkbox("Show data loading progress", value=True)

    # Main content area
    tab1, tab2, tab3 = st.tabs(["Analysis", "Results", "About"])
    
    with tab1:
        st.header("Factor Selection")
        st.write("Select one or more factors for your portfolio strategy:")
        
        # Create columns for factor selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Momentum Factors")
            momentum_factors = {
                '12-Mo Momentum %': st.checkbox('12-Mo Momentum %', key='12m'),
                '6-Mo Momentum %': st.checkbox('6-Mo Momentum %', key='6m'),
                '1-Mo Momentum %': st.checkbox('1-Mo Momentum %', key='1m')
            }
            st.subheader("Profitability Factors")
            profitability_factors = {
                'ROE using 9/30 Data': st.checkbox('ROE using 9/30 Data', key='roe'),
                'ROA using 9/30 Data': st.checkbox('ROA using 9/30 Data', key='roa'),
                'ROA %': st.checkbox('ROA %', key='roa_pct')
            }
            st.subheader("Growth Factors")
            growth_factors = {
                '1-Yr Asset Growth %': st.checkbox('1-Yr Asset Growth %', key='asset_growth'),
                '1-Yr CapEX Growth %': st.checkbox('1-Yr CapEX Growth %', key='capex_growth')
            }
        with col2:
            st.subheader("Value Factors")
            value_factors = {
                'Price to Book Using 9/30 Data': st.checkbox('Price to Book Using 9/30 Data', key='ptb'),
                'Book/Price': st.checkbox('Book/Price', key='btp'),
                'Next FY Earns/P': st.checkbox('Next FY Earns/P', key='fey')
            }
            st.subheader("Quality Factors")
            quality_factors = {
                'Accruals/Assets': st.checkbox('Accruals/Assets', key='accruals'),
                '1-Yr Price Vol %': st.checkbox('1-Yr Price Vol %', key='vol')
            }
        # Only include the specified 13 factors
        all_factor_selections = {
            **momentum_factors,
            **profitability_factors,
            **growth_factors,
            **value_factors,
            **quality_factors
        }
        
        selected_factor_names = [name for name, selected in all_factor_selections.items() if selected]
        
        st.write("---")
        
        # Display selected factors
        if selected_factor_names:
            st.success(f"Selected {len(selected_factor_names)} factor(s): {', '.join(selected_factor_names)}")
        else:
            st.warning("Please select at least one factor to run the analysis")
        
        st.write("---")
        
        # Load Data Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Load Data", use_container_width=True, type="primary"):
                if not use_supabase and not excel_file and not uploaded_file:
                    st.error("Please upload a file or provide an Excel file path")
                else:
                    with st.spinner("Loading market data..."):
                        try:
                            sectors_to_use = selected_sectors if sector_filter_enabled else None
                            
                            # Determine data source
                            data_source = None
                            if use_supabase:
                                data_source = None  # load_data will use Supabase
                            elif uploaded_file:
                                # Use uploaded file object directly
                                data_source = uploaded_file
                            elif excel_file:
                                # Use file path
                                data_source = excel_file
                            
                            rdata = load_data(
                                restrict_fossil_fuels=restrict_fossil_fuels,
                                use_supabase=use_supabase,
                                data_path=data_source if not use_supabase else None,
                                show_loading_progress=show_loading,
                                sectors=sectors_to_use
                            )
                            
                            # Data preprocessing
                            rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(
                                lambda x: x.split('-')[0].strip()
                            )
                            rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year
                            
                            # Keep only relevant columns
                            cols_to_keep = ['Ticker', 'Year']
                            if 'Ending Price' in rdata.columns:
                                cols_to_keep.append('Ending Price')
                            elif 'Ending_Price' in rdata.columns:
                                rdata['Ending Price'] = rdata['Ending_Price']
                                cols_to_keep.append('Ending Price')
                            
                            for factor in FACTOR_MAP.keys():
                                if factor in rdata.columns:
                                    cols_to_keep.append(factor)
                            
                            rdata = rdata[cols_to_keep]
                            
                            st.session_state.rdata = rdata
                            st.session_state.data_loaded = True
                            
                            st.success(f"Data loaded successfully! {len(rdata)} records from {rdata['Year'].min()} to {rdata['Year'].max()}")
                            
                            # Show data preview
                            with st.expander("Data Preview"):
                                st.dataframe(rdata.head(100), use_container_width=True)
                                st.write(f"**Shape:** {rdata.shape[0]} rows × {rdata.shape[1]} columns")
                                st.write(f"**Years:** {sorted(rdata['Year'].unique())}")
                                st.write(f"**Unique Tickers:** {rdata['Ticker'].nunique()}")
                        
                        except Exception as e:
                            st.error(f"Error loading data: {str(e)}")
                            st.exception(e)
        
        st.write("---")
        
        # Run Analysis Button
        if st.session_state.data_loaded:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Run Portfolio Analysis", use_container_width=True, type="primary", disabled=len(selected_factor_names) == 0):
                    if not selected_factor_names:
                        st.error("Please select at least one factor")
                    else:
                        with st.spinner("Running portfolio backtest..."):
                            try:
                                # Create factor objects
                                factor_objects = [FACTOR_MAP[name]() for name in selected_factor_names]
                                
                                # Run rebalancing
                                results = rebalance_portfolio(
                                    st.session_state.rdata,
                                    factor_objects,
                                    start_year=int(start_year),
                                    end_year=int(end_year),
                                    initial_aum=initial_aum,
                                    verbosity=verbosity_level,
                                    restrict_fossil_fuels=restrict_fossil_fuels
                                )
                                
                                st.session_state.results = results
                                st.session_state.selected_factors = selected_factor_names
                                st.session_state.restrict_ff = restrict_fossil_fuels
                                st.session_state.initial_aum = initial_aum
                                
                                st.success("Analysis complete! Check the Results tab.")
                            
                            except Exception as e:
                                st.error(f"Error running analysis: {str(e)}")
                                st.exception(e)
    
    with tab2:
        st.header("Portfolio Performance Results")
        
        if st.session_state.results is not None:
            results = st.session_state.results
            
            # Summary metrics
            st.subheader("Performance Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                final_value = results['portfolio_values'][-1]
                st.metric("Final Portfolio Value", f"${final_value:,.2f}")
            
            with col2:
                total_return = ((final_value / st.session_state.initial_aum) - 1) * 100
                st.metric("Total Return", f"{total_return:.2f}%")
            
            with col3:
                years = len(results['years'])
                cagr = (((final_value / st.session_state.initial_aum) ** (1/years)) - 1) * 100
                st.metric("CAGR", f"{cagr:.2f}%")
            
            with col4:
                if 'benchmark_returns' in results and results['benchmark_returns']:
                    # Convert percentages to decimals before calculating
                    benchmark_final = st.session_state.initial_aum * np.prod([1 + r/100 for r in results['benchmark_returns']])
                    alpha = ((final_value / benchmark_final) - 1) * 100
                    st.metric("Alpha vs Russell 2000", f"{alpha:.2f}%")
                else:
                    st.metric("Rebalances", str(len(results['years'])))
            
            st.divider()
            
            # Portfolio growth chart
            st.subheader("Portfolio Growth Over Time")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            years = results['years']
            portfolio_values = results['portfolio_values']
            
            ax.plot(years, portfolio_values, marker='o', linewidth=2, markersize=6, label='Portfolio', color='#1f77b4')
            
            # Add benchmark if available
            if 'benchmark_returns' in results and results['benchmark_returns']:
                benchmark_values = [st.session_state.initial_aum]
                for ret in results['benchmark_returns']:
                    # Convert percentage to decimal (ret is stored as percentage like 34.62)
                    benchmark_values.append(benchmark_values[-1] * (1 + ret / 100))
                ax.plot(years, benchmark_values, marker='s', linewidth=2, markersize=4, 
                       label='Russell 2000', linestyle='--', alpha=0.7, color='#ff7f0e')
            
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel('Portfolio Value ($)', fontsize=12)
            ax.set_title(f'Portfolio Growth: {", ".join(st.session_state.selected_factors)}', fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            st.pyplot(fig)
            
            st.divider()
            
            # Year-by-year performance table
            st.subheader("Year-by-Year Performance")
            
            perf_data = {
                'Year': results['years'],
                'Portfolio Value': [f"${v:,.2f}" for v in results['portfolio_values']],
            }
            
            # Calculate year-over-year returns
            if len(results['portfolio_values']) > 1:
                yoy_returns = ['-']
                for i in range(1, len(results['portfolio_values'])):
                    ret = ((results['portfolio_values'][i] / results['portfolio_values'][i-1]) - 1) * 100
                    yoy_returns.append(f"{ret:.2f}%")
                perf_data['YoY Return'] = yoy_returns
            
            if 'benchmark_returns' in results and results['benchmark_returns']:
                # Benchmark returns are already in percentage format (like 34.62)
                perf_data['Benchmark Return'] = ['-'] + [f"{r:.2f}%" for r in results['benchmark_returns']]
            
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Advanced Backtest Statistics
            if 'sharpe_portfolio' in results and 'max_drawdown_portfolio' in results:
                st.subheader("Advanced Backtest Statistics")
                
                # Display key metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Max Drawdown (Portfolio)", 
                             f"{results['max_drawdown_portfolio']*100:.2f}%",
                             delta=None,
                             help="Largest peak-to-trough decline in portfolio value")
                
                with col2:
                    st.metric("Max Drawdown (Benchmark)", 
                             f"{results['max_drawdown_benchmark']*100:.2f}%",
                             delta=None,
                             help="Largest peak-to-trough decline in Russell 2000")
                
                with col3:
                    sharpe_delta = results['sharpe_portfolio'] - results['sharpe_benchmark']
                    st.metric("Sharpe Ratio (Portfolio)", 
                             f"{results['sharpe_portfolio']:.4f}",
                             delta=f"{sharpe_delta:+.4f} vs benchmark",
                             help="Risk-adjusted return (return per unit of volatility)")
                
                with col4:
                    st.metric("Sharpe Ratio (Benchmark)", 
                             f"{results['sharpe_benchmark']:.4f}",
                             delta=None,
                             help="Risk-adjusted return for Russell 2000")
                
                # Win rate and information ratio
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Yearly Win Rate", 
                             f"{results['win_rate']*100:.2f}%",
                             delta=None,
                             help="Percentage of years portfolio outperformed benchmark")
                
                with col2:
                    if 'information_ratio' in results and results['information_ratio'] is not None:
                        st.metric("Information Ratio", 
                                 f"{results['information_ratio']:.4f}",
                                 delta=None,
                                 help="Active return per unit of active risk")
                
                with col3:
                    st.metric("Risk-Free Rate Source", 
                             results.get('risk_free_rate_source', 'N/A'),
                             delta=None,
                             help="Data source for risk-free rate calculations")
                
                # Yearly win/loss comparison table
                if 'yearly_comparisons' in results:
                    st.subheader("Yearly Win/Loss vs Benchmark")
                    
                    comparison_data = {
                        'Year': [comp['year'] for comp in results['yearly_comparisons']],
                        'Portfolio Return': [f"{comp['portfolio_return']:.2f}%" for comp in results['yearly_comparisons']],
                        'Benchmark Return': [f"{comp['benchmark_return']:.2f}%" for comp in results['yearly_comparisons']],
                        'Outperformed': ['✓' if comp['win'] else '✗' for comp in results['yearly_comparisons']]
                    }
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                
                st.divider()
            
            # Download results
            st.subheader("Download Results")
            
            csv = perf_df.to_csv(index=False)
            st.download_button(
                label="Download Performance Data (CSV)",
                data=csv,
                file_name=f"portfolio_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("👈 Run an analysis from the Analysis tab to see results here")
    
    with tab3:
        st.header("About Factor-Lake Portfolio Analysis")
        
        st.markdown("""
        ### What is Factor Investing?
            
        Factor investing is a strategy that targets specific drivers of returns across asset classes. 
        This tool allows you to backtest various factor strategies on historical market data.
            
        ### Available Factors
            
        **Momentum Factors:**
        - Stocks that have performed well in the past tend to continue performing well
            
        **Value Factors:**
        - Stocks trading at low prices relative to their fundamentals
            
        **Profitability Factors:**
        - Companies with strong profit margins and returns
            
        **Growth Factors:**
        - Companies with strong growth in assets and capital expenditure
            
        **Quality Factors:**
        - Companies with stable earnings and low volatility
            
        ### How to Use
            
        1. **Configure** your data source and filters in the sidebar
        2. **Select** one or more factors in the Analysis tab
        3. **Load** the market data
        4. **Run** the portfolio analysis
        5. **View** results and download performance data
            
        ### Data Sources
            
        - **Supabase**: Cloud-hosted database with historical market data
        - **Excel**: Load data from a local Excel file
            
        ### Disclaimer
            
        This tool is for educational and research purposes only. Past performance does not guarantee future results.
        Always consult with a qualified financial advisor before making investment decisions.
            
        ### Resources
            
        - [Project Repository](https://github.com/FMDX-7/Factor-Lake_2)
        - [Documentation](README.md)
            
        ---
            
        **Version:** 1.0.0  
        **Last Updated:** October 2025
        """)

if __name__ == "__main__":
    main()
