def calculate_portfolio_value(stocks, prices):
    return sum(stocks[symbol] * prices[symbol] for symbol in stocks)

def update_stock_quantity(stocks, symbol, quantity):
    if symbol in stocks:
        stocks[symbol] += quantity
    else:
        stocks[symbol] = quantity
    return stocks

def show_top_performers(prices):
    sorted_prices = sorted(prices, key=prices.get, reverse=True)
    return sorted_prices[:3]

def simulate_market_change(prices, change_factor):
    for stock in prices:
        prices[stock] *= change_factor
    return prices

def manage_portfolio_changes(stocks, prices, symbol, quantity, change_factor):
    stocks = update_stock_quantity(stocks, symbol, quantity)
    prices = simulate_market_change(prices, change_factor)
    return stocks, prices

def main():
    stocks = {"AAPL": 10, "GOOGL": 5, "AMZN": 2, "MSFT": 8, "TSLA": 4}
    stock_prices = {"AAPL": 150, "GOOGL": 1800, "AMZN": 3100, "MSFT": 250, "TSLA": 700}
    stocks, stock_prices = manage_portfolio_changes(stocks, stock_prices, "GOOGL", 1, 0.95)
    top_performers = show_top_performers(stock_prices)
    portfolio_value = calculate_portfolio_value(stocks, stock_prices)
    
    print("Portfolio value:", portfolio_value)
    print("Top performers:", top_performers)

main()
