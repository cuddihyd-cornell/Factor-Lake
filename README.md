# Factor-Lake

**Interactive Factor-Based Portfolio Analysis Tool**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FMDX-7/Factor-Lake_2/blob/main/colab_setup.ipynb)

## Quick Start

### Run on Google Colab (No Installation Required)
**Click the badge above** or see [Colab Instructions](COLAB_INSTRUCTIONS.md)

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python run_streamlit.py
```

Open http://localhost:8501 in your browser

## Features

- **Factor Selection**: 13+ investment factors (Momentum, Value, Quality, Growth, Profitability)
- **ESG Filters**: Exclude fossil fuel companies
- **Sector Filters**: Focus on specific industries
- **Backtesting**: Historical performance from 2002-2023
- **Benchmark Comparison**: Compare vs Russell 2000
- **Interactive Charts**: Visualize portfolio growth
- **Export Results**: Download performance data as CSV

## Project Structure

```
Factor-Lake_2/
├── src/                    # Source code
├── streamlit_app.py        # Web interface
├── colab_setup.ipynb       # Google Colab notebook
├── requirements.txt        # Dependencies
└── README.md
```

## Documentation

- [Colab Instructions](COLAB_INSTRUCTIONS.md) - Run on Google Colab
- [Streamlit Styling Guide](STREAMLIT_STYLING_GUIDE.md) - Customize the interface
- [Supabase Setup](SUPABASE_SETUP.md) - Database configuration

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

See LICENSE file for details.
 
