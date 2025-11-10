from .market_object import load_data

class Factors:
    def __init__(self, column_name):
        self.column_name = column_name

    def __str__(self):
        # friendly name when converted to string
        return self.column_name

    def __repr__(self):
        # Helpful debug representation
        return f"{self.__class__.__name__}('{self.column_name}')"

    def get(self, ticker, market):
        # Pre-indexed market stocks for faster lookup
        try:
            value = market.stocks.loc[ticker, self.column_name]
            return value
        except KeyError:
            print(f"{ticker} - not found in market data for {market.t} - SKIPPING")
            return None
        except Exception as e:
            print(f"Error accessing {self.column_name} for {ticker}: {e}")
            return None

# Subclasses define specific factor columns
class Momentum6m(Factors):
    def __init__(self):
        super().__init__('6-Mo Momentum %')

class Momentum12m(Factors):
    def __init__(self):
        super().__init__('12-Mo Momentum %')

class Momentum1m(Factors):
    def __init__(self):
        super().__init__('1-Mo Momentum %')

class ROE(Factors):
    def __init__(self):
        super().__init__('ROE using 9/30 Data')

class ROA(Factors):
    def __init__(self):
        super().__init__('ROA using 9/30 Data')

class P2B(Factors):
    def __init__(self):
        super().__init__('Price to Book Using 9/30 Data')

class NextFYrEarns(Factors):
    def __init__(self):
        super().__init__('Next FY Earns/P')

class OneYrPriceVol(Factors):
    def __init__(self):
        super().__init__('1-Yr Price Vol %')

class AccrualsAssets(Factors):
    def __init__(self):
        super().__init__('Accruals/Assets')

class ROAPercentage(Factors):
    def __init__(self):
        super().__init__('ROA %')

class OneYrAssetGrowth(Factors):
    def __init__(self):
        super().__init__('1-Yr Asset Growth %')

class OneYrCapEXGrowth(Factors):
    def __init__(self):
        super().__init__('1-Yr CapEX Growth %')

class BookPrice(Factors):
    def __init__(self):
        super().__init__('Book/Price')

class NextYrReturn(Factors):
    def __init__(self):
        super().__init__("Next-Year's Return %")

class NextYrActiveReturn(Factors):
    def __init__(self):
        super().__init__("Next-Year's Active Return %")
