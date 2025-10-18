from data_util import get_currency_prices,set_tmp_price

def main():
    currency_list = ['BTC','ETH','POL','BNB']
    res = get_currency_prices(currency_list,exchange=None)
    print(res)

if __name__ == '__main__':
    main()