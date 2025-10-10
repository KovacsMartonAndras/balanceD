import yfinance as yf
import exchange_functions as ef

def get_stock_handles(file=None):
  """Gets the list of stocks the user owns, possibly from a CSV file"""
  handles = []
  if file is None:
    #TODO: implement
    return handles 
  try:
    #TODO: implement
    return handles
  except Exception as e:
      print(f"Stock handles could not be fetched: {e}")
    return None

def get_stock_numbers():
  """Returns the number of stocks the user owns organized in a dictionary with the stock handle as the keys."""
  #TODO
  return dict()

def get_stock_price(handle:str, currency=None)
  """Gets stock price of stock with given handle and the currency as a tuple. If currency is None, the base currency in which the stock is traded is used."""
  try:
    ticker = yf.Ticker(handle.capitalize())
    base_curr = ticker.info['currency']
    price = ticker.info['regularMarketPrice']
    if currency is None:
      currency = base_curr
    else:
      price = ef.convert_to_currency(base_curr,currency,price)
    return price, currency
  except Exception as e:
    print(f"Stock price of {handle.capitalize()} could not be fetched: {e}")
    return None, None
