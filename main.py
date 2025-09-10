
from fastapi import FastAPI
from typing import Dict, Any

from web3_util import call_fill_relay_by_alchemy,get_decode_calldata

app = FastAPI()

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    # print('data: ', data)
    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    print('depositHash: ', transaction_dict['hash'])
    tx_hash = call_fill_relay_by_alchemy(data)
    print('fill_relay_hash: ', tx_hash)
    return "success"