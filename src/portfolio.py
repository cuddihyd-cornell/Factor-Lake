class Portfolio:
    ### Initialize portfolio by providing a name and a list of investments ###
    def __init__(self, name, investments=None):
        self.name = name
        if investments is not None:
            self.investments = investments
        else:
            self.investments = []

    ### Add a stock to the portfolio ###
    def add_investment(self, ticker, nShares):
        investment = {'ticker': ticker, 'number_of_shares': nShares}
        self.investments.append(investment)

    ### Remove a stock from the portfolio ###
    def remove_investment(self, ticker):
        self.investments = [
            inv for inv in self.investments if inv['ticker'] != ticker
        ]

    ### Calculate portfolio value ###
    def present_value(self, market):
        total_value = 0
        for inv in self.investments:
            price = market.get_price(inv['ticker'])
            if price is not None:
                total_value += price * inv['number_of_shares']
        return total_value

    ### Calculate return for the portfolio ###
    def calculate_return(self, t1_value, t2_value):
        if t1_value != 0:
            return (t2_value - t1_value) / t1_value * 100
        else:
            raise ValueError('Value at time 1 is 0')

