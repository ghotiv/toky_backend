import time

from data_util import get_currency_prices,set_tmp_price,get_tmp_price

def main():
    while True:
        currency_list = ['BTC','ETH','POL','BNB']
        res_prices = get_currency_prices(currency_list,exchange=None)
        for currency,price in res_prices.items():
            print(time.strftime('%Y-%m-%d %H:%M:%S'))
            print(f"set {currency} price: {price}")
            set_tmp_price(currency,price)
        time.sleep(30)

if __name__ == '__main__':
    main()