import yfinance as yf

stocks = [
    'TSLA',
    'AAPL',
    'MSFT',
    'AMZN',
    'NVDA',
    'GOOGL',
    'META',
    'V',
    'MA',
    'PEP',
    'KO',
    'ADBE',
    'MCD',
    'NFLX',
    'ORCL',
    'INTC',
    'NKE',
    'QCOM',
    'SBUX',
    'BLK',
    'DPZ',
    'UBER',
    'MARA',
    'RIOT',
    'COIN',
    'MSTR',
    'BITF',
    'CORZ',
    'CLSK'
]

class StockMarketCup:
    def format_market_cap(self, value):
        if value >= 1e12:  # Trillions
            value /= 1e12
            return "${:.2f}T".format(value)
        elif value >= 1e9:  # Billions
            value /= 1e9
            return "${:.2f}B".format(value)
        elif value >= 1e6:  # Millions
            value /= 1e6
            return "${:.2f}M".format(value)
        else:
            return "${:.2f}".format(value)

    def check(self):
        ticker_string = ' '.join(stocks)
        data = yf.Tickers(ticker_string)
        
        with open("stock_volumes.txt", "w") as f:
            for ticker in stocks:
                marketcap = self.format_market_cap(data.tickers[ticker].info['marketCap'])
                volume_last_24h = self.format_market_cap(data.tickers[ticker].history(period="1d")['Volume'].iloc[-1])
                output = f"{ticker} CAP: {marketcap}, Volume (last 24h): {volume_last_24h}"
                
                print(output)
                f.write(output + "\n")

def scan_stock_volumes():
    StockMarketCup().check()

if __name__ == '__main__':
    StockMarketCup().check()
