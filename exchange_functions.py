
def convert_to_currency(source,target,amount):
    #TODO Implement live transaction rates, should return the amount in the target currency based on the current exhange rates
    if source == "HUF":
        return amount
    else:
        return amount * 420