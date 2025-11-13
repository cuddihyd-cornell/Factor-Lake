# Factor-Lake

An interactive factor-investing research toolkit with a Streamlit UI, Supabase data integration, and a pytest test suite. The codebase uses a modern `src/` layout and a cleaned UX.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/cuddihyd-cornell/Factor-Lake/blob/revamped_ux/colab_setup.ipynb)

## Quick Start

### Option A: Google Colab (no local setup)
Click the badge above or open `colab_setup.ipynb` and run all cells. It will clone the `revamped_ux` branch and launch the app via ngrok.

### Option B: Local Environment
```pwsh
git clone https://github.com/cuddihyd-cornell/Factor-Lake.git
cd Factor-Lake
git checkout revamped_ux
pip install -r requirements.txt
python .\app\streamlit.py
```
Then open http://localhost:8501

### Run the App with Raw Streamlit
```pwsh
python -m streamlit run .\app\streamlit_app.py
```

### Run Tests
```pwsh
pytest -q
```

## Features

- Clean factor selection (13 core factors: Momentum, Value, Quality, Growth, Profitability)
- ESG exclusion (fossil fuel filter)
- Sector filtering (5-sector classification)
- Supabase data loading (table selectable, column normalization)
- Excel/CSV fallback for offline use
- Annual rebalancing backtest (2002–2023)
- Benchmark comparison vs Russell 2000
- Performance metrics: CAGR, yearly returns, drawdown, Sharpe, Information Ratio, win rate
- Downloadable performance table

## Project Layout

```
Factor-Lake/
├── app/                    # Streamlit entrypoints
│   ├── streamlit.py        # Convenience launcher
│   └── streamlit_app.py    # Main UI
├── src/                    # Library & core logic
│   ├── market_object.py
│   ├── calculate_holdings.py
│   ├── factor_function.py
│   ├── portfolio.py
│   ├── sector_selection.py
│   ├── supabase_client.py
│   └── ...
├── Visualizations/         # Plot helpers
├── UnitTests/              # Pytest suite
├── scripts/                # CI / helper scripts
├── DOCS/                   # Supplementary documentation
├── colab_setup.ipynb       # Colab notebook
├── requirements.txt
└── README.md
```

## Import Conventions

Always import from `src`:
```python
from src.market_object import load_data
from src.calculate_holdings import rebalance_portfolio
```

In Streamlit UI we ensure `src` is on `sys.path`.

## Documentation

- `DOCS/STREAMLIT_README.md` – UI overview
- `DOCS/STREAMLIT_STYLING_GUIDE.md` – Styling / customization
- `DOCS/SUPABASE_SETUP.md` – Environment & table notes
- `DOCS/REORGANIZATION_SUMMARY.md` – Refactor rationale
- `DOCS/CONTRIBUTING.md` – Contribution guidelines

## Contributing

1. Create a feature branch from `revamped_ux`
2. Add/modify tests in `UnitTests/`
3. Run `pytest -q` to verify
4. Submit a PR describing UX/data impacts

## License

See `LICENSE` for details.

## Status

`revamped_ux` branch integrates the improved Streamlit UX and data normalization pipeline migrated from the Factor-Lake_2 prototype.

