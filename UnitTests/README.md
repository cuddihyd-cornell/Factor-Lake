# Factor-Lake Test Suite

Comprehensive test suite for the Factor-Lake portfolio management system.

## Test Structure

```
UnitTests/
├── conftest.py                      # Pytest configuration and fixtures
├── test_market_object.py            # Market data loading and processing
├── test_factors.py                  # Factor classes and calculations
├── test_portfolio.py                # Portfolio management and valuation
├── test_calculate_holdings.py       # Portfolio construction and rebalancing
├── test_supabase_integration.py     # Database integration tests
├── test_known_good.py              # Regression tests (existing)
└── test_multiple_factors.py        # Multi-factor tests (existing)
```

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- All project dependencies

### Run All Tests

```bash
pytest UnitTests/ -v
```

Or use the test runner:

```bash
python run_tests.py all
```

## Test Categories

### 1. Market Object Tests (`test_market_object.py`)

Tests for data loading and market object creation:
- Supabase data loading
- Column name standardization
- Market object initialization
- Price retrieval
- Fossil fuel filtering
- Missing value handling

**Run:**
```bash
python run_tests.py market
```

### 2. Factor Tests (`test_factors.py`)

Tests for all factor classes:
- All 15 factor classes (Momentum, ROE, ROA, etc.)
- Factor value retrieval
- Missing data handling
- Edge cases (NaN values, missing tickers)

**Run:**
```bash
python run_tests.py factors
```

### 3. Portfolio Tests (`test_portfolio.py`)

Tests for portfolio management:
- Portfolio creation
- Adding/removing investments
- Valuation calculations
- Return calculations
- Fractional shares
- Missing stocks handling

**Run:**
```bash
python run_tests.py portfolio
```

### 4. Calculate Holdings Tests (`test_calculate_holdings.py`)

Tests for portfolio construction and rebalancing:
- Top 10% stock selection
- Equal weighting
- Factor-based ranking
- Portfolio growth calculation
- Multi-year rebalancing
- Information ratio calculation
- Fossil fuel restrictions

**Run:**
```bash
python run_tests.py holdings
```

### 5. Supabase Integration Tests (`test_supabase_integration.py`)

Tests for database connectivity:
- Data loading
- Pagination functionality
- Data quality checks
- Connection resilience
- Error handling

**Run:**
```bash
python run_tests.py supabase
```

## Running Tests

### Run All Tests
```bash
pytest UnitTests/ -v
# or
python run_tests.py all
```

### Run Fast Tests Only
Excludes slow integration tests:
```bash
python run_tests.py fast
```

### Run Unit Tests Only
Excludes integration tests:
```bash
python run_tests.py unit
```

### Run Integration Tests Only
Only runs tests that connect to real data:
```bash
python run_tests.py integration
```

### Run Specific Module Tests
```bash
python run_tests.py market      # Market object tests
python run_tests.py factors     # Factor tests
python run_tests.py portfolio   # Portfolio tests
python run_tests.py holdings    # Holdings calculation tests
python run_tests.py supabase    # Supabase integration tests
```

### Run with Coverage Report
```bash
python run_tests.py coverage
```

This generates:
- Terminal coverage summary
- HTML report in `htmlcov/index.html`

## 📊 Test Coverage

Current test coverage includes:

### Core Functionality
- ✅ Data loading (Supabase and Excel)
- ✅ Column name standardization
- ✅ Market object creation
- ✅ All 15 factor classes
- ✅ Factor value retrieval
- ✅ Portfolio management
- ✅ Portfolio valuation
- ✅ Return calculations
- ✅ Stock selection (top 10%)
- ✅ Equal weighting
- ✅ Multi-factor portfolios
- ✅ Rebalancing logic
- ✅ Growth calculations
- ✅ Information ratio

### Edge Cases
- ✅ Missing data handling
- ✅ NaN values
- ✅ Empty portfolios
- ✅ Missing stocks in market
- ✅ Fossil fuel filtering
- ✅ Zero values
- ✅ Special characters in tickers

### Integration
- ✅ Real Supabase data
- ✅ Multi-year rebalancing
- ✅ Complete portfolio lifecycle
- ✅ Known good results (regression)

## 🔧 Pytest Configuration

Configuration in `pytest.ini`:
- Test discovery patterns
- Output formatting
- Custom markers
- Coverage settings

### Custom Markers

Mark slow tests:
```python
@pytest.mark.slow
def test_long_running_operation():
    ...
```

Mark integration tests:
```python
@pytest.mark.integration
def test_with_real_data():
    ...
```

## 📝 Writing New Tests

### Test Structure
```python
import pytest
from your_module import YourClass

class TestYourFeature:
    """Test suite for your feature"""
    
    @pytest.fixture
    def sample_data(self):
        """Create reusable test data"""
        return {...}
    
    def test_basic_functionality(self, sample_data):
        """Test description"""
        # Arrange
        obj = YourClass(sample_data)
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected
```

### Best Practices
1. **Use descriptive names**: `test_portfolio_value_with_missing_stocks`
2. **One assertion per test** (when possible)
3. **Use fixtures** for common setup
4. **Test edge cases**: empty inputs, NaN, None, zeros
5. **Test error handling**: invalid inputs, exceptions
6. **Add docstrings**: explain what the test validates

## 🐛 Debugging Failed Tests

### Verbose Output
```bash
pytest UnitTests/test_your_test.py -v -s
```
- `-v`: Verbose output
- `-s`: Print statements visible

### Run Single Test
```bash
pytest UnitTests/test_market_object.py::TestMarketObject::test_get_price -v
```

### Show Local Variables on Failure
```bash
pytest UnitTests/ -v -l
```

### Drop into Debugger on Failure
```bash
pytest UnitTests/ --pdb
```

## 📈 Continuous Integration

Tests can be integrated into CI/CD:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest UnitTests/ -v --cov=.
```

## 🎓 Test Examples

### Example 1: Testing Factor Value Retrieval
```python
def test_momentum_6m_retrieval():
    """Test retrieving 6-month momentum factor"""
    # Create test data
    data = pd.DataFrame({
        'Ticker-Region': ['AAPL-US'],
        'Ending Price': [150.0],
        '6-Mo Momentum %': [0.20],
        'Year': [2022]
    })
    
    # Create market
    market = MarketObject(data, 2022)
    
    # Create factor and retrieve value
    factor = Momentum6m()
    value = factor.get('AAPL', market)
    
    # Verify
    assert value == 0.20
```

### Example 2: Testing Portfolio Valuation
```python
def test_portfolio_present_value():
    """Test portfolio valuation calculation"""
    # Create portfolio
    portfolio = Portfolio("Test")
    portfolio.add_investment('AAPL', 10)  # 10 shares
    
    # Create market with prices
    market = MarketObject(...)  # AAPL at $150
    
    # Calculate value
    value = portfolio.present_value(market)
    
    # Should be 10 shares * $150 = $1,500
    assert value == 1500.0
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >80% coverage
4. Add integration tests for real data
5. Update this README

## ❓ Common Issues

### Issue: Import Errors
**Solution:** Make sure you're running tests from project root:
```bash
cd Factor-Lake
pytest UnitTests/
```

### Issue: Supabase Connection Failed
**Solution:** Check `.env` file has correct credentials:
```bash
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

### Issue: Slow Tests
**Solution:** Run fast tests only:
```bash
python run_tests.py fast
```

## 📞 Support

For test-related questions:
1. Check this README
2. Review test files for examples
3. Check pytest documentation
4. Open an issue on GitHub
