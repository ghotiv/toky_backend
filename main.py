import time

from fastapi import FastAPI
from typing import Dict, Any

from web3_util import call_fill_relay_by_alchemy

app = FastAPI()

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    print('time: ', time.time(), 'depositHash: ', transaction_dict['hash'])
    # time.sleep(10)
    # tx_hash = call_fill_relay_by_alchemy(data)
    # print('time: ', time.time(), 'tx_hash: ', tx_hash)
    return "success"