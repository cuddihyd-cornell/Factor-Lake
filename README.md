# Factor-Lake

An interactive factor-investing toolkit with a clean Streamlit UI, Supabase data integration, and a pytest test suite. The codebase uses a modern `src/` layout and a clean UX.

## Use the App

- Hosted: Share your Streamlit Community Cloud app URL. Users only need the link to use the app.
- Password: Set a secret named `password` in your app’s Settings → Secrets. Locally you can use `.streamlit/secrets.toml`.

Example secrets (TOML):
```
password = "your-strong-password"
```

## Quick Start (Local)

```pwsh
git clone https://github.com/cornell-sysen-5900/Factor-Lake.git
cd Factor-Lake
pip install -r requirements.txt
python -m streamlit run .\app\streamlit_app.py
```

Then open http://localhost:8501

## Features

- Clean factor selection (13 core factors: Momentum, Value, Quality, Growth, Profitability)
- ESG exclusion (fossil fuel filter)
- Sector filtering (5-sector classification)
- Supabase data loading with column normalization
- Annual rebalancing backtest (2002–2023)
- Benchmark comparison vs Russell 2000
- Performance metrics: CAGR, yearly returns, drawdown, Sharpe, Information Ratio, win rate
- Downloadable performance table

## Project Layout

```
Factor-Lake/
├── app/                    # Streamlit entrypoints
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
├── requirements.txt
└── README.md
```

## Import Conventions

Always import from `src`:
```python
from src.market_object import load_data
from src.calculate_holdings import rebalance_portfolio
```

## Documentation

- `DOCS/STREAMLIT_README.md` – UI overview
- `DOCS/STREAMLIT_STYLING_GUIDE.md` – Styling / customization
- `DOCS/SUPABASE_SETUP.md` – Environment & table notes
- `DOCS/REORGANIZATION_SUMMARY.md` – Refactor rationale

## Deployment

For detailed deployment instructions (Streamlit Community Cloud, secrets management, and troubleshooting), see `DOCS/DEPLOYMENT.md`.

## Contributing

1. Create a feature branch from `main`.
2. Add/modify tests in `UnitTests/` or `tests/`.
3. Run `pytest -q` to verify.
4. Submit a PR describing UX/data impacts.

## License

See `LICENSE` for details.

