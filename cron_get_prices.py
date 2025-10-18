import time

from data_util import get_currency_prices,set_tmp_price,get_tmp_price

def main():
    while True:
        currency_list = ['BTC','ETH','POL','BNB']
        res_prices = {}
        try:
            res_prices = get_currency_prices(currency_list,exchange=None)
        except Exception as e:
            print(time.strftime('%Y-%m-%d %H:%M:%S'))
            print(f"error: {e}")
            continue
        print(time.strftime('%Y-%m-%d %H:%M:%S'))
        for currency,price in res_prices.items():
            print(f"set {currency} price: {price}")
            set_tmp_price(currency,price)
        time.sleep(30)
        print(f"sleep 30 seconds")

if __name__ == '__main__':
    main()  