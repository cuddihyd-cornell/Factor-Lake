# Factor-Lake

A factor-investing research toolkit with a Streamlit UI and a test suite. The codebase now follows a src/ layout.

## Project layout

- `src/` — application and library code (canonical source)
- `UnitTests/` — test suite (pytest)
- `Visualizations/` — plotting utilities used by the app
- `scripts/` — CI helpers for security scans (bandit, safety)
- `streamlit_app.py` — Streamlit UI entrypoint
- `streamlit.py` — convenience launcher for Streamlit

Notable cleanup: duplicate modules previously at the repository root have been removed in favor of `src/`. Import from `src` explicitly, e.g. `from src.market_object import load_data`.

## Quick start

1) Install dependencies

```pwsh
pip install -r requirements.txt
```

2) Run tests

```pwsh
pytest -q
```

3) Launch Streamlit app

```pwsh
python .\app\streamlit.py
```

The app will open in your browser. If you want to run the Streamlit module directly:

```pwsh
python -m streamlit run .\app\streamlit_app.py
```

## Imports

Always import code from `src`:

- Library usage: `from src.calculate_holdings import rebalance_portfolio`
- CLI/UI usage: `python .\streamlit.py`

## Notes

- Tests add the project root to `sys.path`. Test imports have been updated to use `src.*` to avoid ambiguity.
- Streamlit app already prepends `src/` to sys.path for convenience.

