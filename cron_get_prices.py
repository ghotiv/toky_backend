from data_util import get_currency_prices,set_tmp_price,get_tmp_price

def main():
    currency_list = ['BTC','ETH','POL','BNB']
    res_prices = get_currency_prices(currency_list,exchange=None)
    for currency,price in res_prices.items():
        set_tmp_price(currency,price)
    for currency in currency_list:
        price = get_tmp_price(currency)
        print(f"{currency}: {price}")

if __name__ == '__main__':
    main()