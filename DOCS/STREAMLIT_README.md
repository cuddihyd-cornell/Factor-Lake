# Factor-Lake Streamlit Application (alternative option that is not currently implemented)

An interactive web application for factor-based portfolio analysis and backtesting.

## Quick Start

### Local Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python run_streamlit.py
   ```
   
   Or directly:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Open your browser** to `http://localhost:8501`

### Google Colab

1. **Open the Colab notebook:**
   - Upload `colab_setup.ipynb` to Google Colab
   - Or click: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FMDX-7/Factor-Lake_2/blob/main/colab_setup.ipynb)

2. **Get an ngrok auth token (Optional - most likely not needed):**
   - Visit: https://dashboard.ngrok.com/get-started/your-authtoken
   - Sign up for free
   - Copy your auth token

3. **Run all cells in order:**
   - Paste your ngrok token when prompted
   - Click the generated URL to access the app

## ✨ Features

### Interactive Factor Selection
* **Momentum Factors**: 1-month, 6-month, 12-month momentum
* **Value Factors**: Price-to-Book, Book-to-Price, Forward Earnings Yield
* **Profitability Factors**: ROE, ROA
* **Growth Factors**: Asset Growth, CapEx Growth
* **Quality Factors**: Low Accruals, Low Volatility

### ESG & Sector Filters
- Exclude fossil fuel companies
- Select specific sectors
- Customize universe

### Portfolio Analysis
- Backtest from 2002-2023
- Compare against Russell 2000 benchmark
- Year-by-year performance breakdown
- Calculate CAGR and Alpha

### Export Results
- Download performance data as CSV
- Export portfolio holdings
- Save visualizations

## How to Use

1. **Configure Settings** (Left Sidebar)
   - Choose data source (Supabase or Excel)
   - Set ESG filters
   - Select analysis period
   - Set initial investment amount

2. **Select Factors** (Analysis Tab)
   - Check boxes for desired factors
   - Can select multiple factors
   - Factors are combined with equal weighting

3. **Load Data**
   - Click "Load Data" button
   - Preview data statistics
   - Verify date range and ticker count

4. **Run Analysis**
   - Click "Run Portfolio Analysis"
   - Wait for backtest to complete
   - View results in Results tab

5. **Review Results** (Results Tab)
   - View performance metrics
   - Analyze portfolio growth chart
   - Compare to benchmark
   - Download CSV data

## File Structure

```
Factor-Lake_2/
├── streamlit_app.py          # Main Streamlit application
├── run_streamlit.py           # Launcher script
├── colab_setup.ipynb          # Google Colab notebook
├── requirements.txt           # Python dependencies
├── src/                       # Source code
│   ├── main.py
│   ├── market_object.py
│   ├── calculate_holdings.py
│   ├── factor_function.py
│   ├── portfolio.py
│   └── ...
├── UnitTests/                 # Test files
├── Visualizations/            # Plotting utilities
└── README.md
```

## Configuration

### Environment Variables

For Supabase connection:
```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

Or set in the app's sidebar when running.

### Data Sources

**Option 1: Supabase (Recommended)**
- Cloud-hosted database
- Automatic updates
- No local files needed

**Option 2: Local Excel File**
- Provide path to Excel file
- Must contain required columns
- See data format requirements

## Data Requirements

Your data source must include:
- `Ticker-Region`: Stock ticker with region
- `Date`: Date of observation
- `Ending Price`: Stock price
- Factor columns (e.g., "ROE using 9/30 Data")
- `FactSet Industry`: For sector filtering

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Make sure you're in the project root
cd Factor-Lake_2

# Reinstall requirements
pip install -r requirements.txt
```

### Streamlit Won't Start
```bash
# Check Streamlit installation
pip show streamlit

# Reinstall if needed
pip install --upgrade streamlit
```

### Data Loading Issues

**Supabase Connection Failed:**
- Verify your Supabase URL and key
- Check internet connection
- Try using Excel file instead

**Excel File Not Found:**
- Use absolute file path
- Check file permissions
- Verify file format (xlsx)

### Google Colab Issues

**Ngrok tunnel error:**
- Make sure you set your auth token
- Get a free token at https://dashboard.ngrok.com/
- Token is required for public URL

**Import errors in Colab:**
- Run the installation cell again
- Restart runtime if needed
- Check that git clone succeeded

## Customization

### Add New Factors

1. Define factor in `src/factor_function.py`:
   ```python
   class MyNewFactor(Factor):
       def __init__(self):
           super().__init__('My Factor Column Name')
       
       def get(self, ticker, market):
           # Implement factor logic
           return value
   ```

2. Add to `FACTOR_MAP` in `streamlit_app.py`:
   ```python
   FACTOR_MAP = {
       ...
       'My New Factor': MyNewFactor,
   }
   ```

3. Add checkbox in the appropriate section

### Modify Styling

Edit CSS in `streamlit_app.py`:
```python
st.markdown("""
<style>
    /* Your custom CSS here */
</style>
""", unsafe_allow_html=True)
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Project Repository](https://github.com/FMDX-7/Factor-Lake_2)
- [Factor Investing Guide](https://www.investopedia.com/terms/f/factor-investing.asp)

## Disclaimer

This tool is for educational and research purposes only. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines.

## License

See LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section above

---

**Happy Investing!**
