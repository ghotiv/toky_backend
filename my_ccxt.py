import ccxt

CLS_DICT = {
    # 'huobipro': ccxt.huobipro,
    # 'gateio': ccxt.gateio,
    # 'bitfinex': ccxt.bitfinex,
    'binance': ccxt.binance,
    # 'bitmex': ccxt.bitmex,
}

def format_symbol(symbol,is_ccxt=True,is_future=False):
    if is_ccxt:
        res = symbol.replace('-','/').replace('_','/').upper()
        if is_future:
            res = res.replace('/','')
    else:
        #okex
        res = symbol.replace('/','-').replace('_','-').upper()
        if is_future:
            res = res.replace('/','')
    return res

class MyCcxt(object):
    '''
        ccxt get exchage api
    '''
    def __init__(self, api_key=None, secret=None, ex_name=None,
                     passphrase=None, api_url=None, is_ccxt=True,
                     proxies=None):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.api_url = api_url
        self.is_ccxt = is_ccxt
        self.ex_name = ex_name
        if ex_name == 'okex':
            self.is_ccxt = False
        if self.is_ccxt:
            ccxt_arg_dict = {'apiKey': self.api_key,'secret': self.secret, 'timeout':10000,}
                                # 'verbose': True}
            if proxies:
                # proxies
                # {'http': 'http://localhost:1087','https': 'http://localhost:1087',}
                ccxt_arg_dict.update({'proxies':proxies})
            self.exchange = CLS_DICT[ex_name](ccxt_arg_dict)
            if api_url:
                self.exchange.urls['api'] = self.api_url
            #报错币安时间不同步，需要加
            # self.exchange.nonce = lambda: self.exchange.fetch_time()
        else:
            pass
            #okex
            # self.exchange = spot.SpotAPI(self.api_key, self.secret, self.passphrase, True)

    def fetch_symbol_last_price(self, symbol=None, currency=None):
        if currency:
            if currency.upper()=='USDT':
                return 1
            else:
                symbol=f'{currency.upper()}/USDT'
                # print(symbol)
            # print(self.exchange.fetch_ticker(symbol))
            return self.exchange.fetch_ticker(symbol)['last']
        if symbol:
            return self.exchange.fetch_ticker(symbol)['last']
        
    def fetch_ohlcv(self, symbol, timeframe='1h', since=None, limit=None, params={}):
        # [1675210740000, 23083.46, 23083.99, 23067.37, 23075.56, 124.87217]
        # [t,o,h,l,c,v]
        symbol = format_symbol(symbol,is_ccxt=self.is_ccxt)
        return self.exchange.fetch_ohlcv(symbol,limit=limit,timeframe=timeframe)



    
