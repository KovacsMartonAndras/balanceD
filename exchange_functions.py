from forex_python.converter import CurrencyRates

def convert_to_currency(source,target,amount):
    c = CurrencyRates()
    if source == target:
        return amount
    try:
        rate = c.get_rate(source, target)
        converted_amount = amount * rate
        return converted_amount
    except Exception as e:
        print(f"Error converting {amount} from {source} to {target}: {e}")
        return None
    
if __name__ == "__main__":
    print(convert_to_currency("EUR","USD",100))
