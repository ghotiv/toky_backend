
from fastapi import FastAPI
from typing import Dict, Any

from web3_util import get_decode_calldata

app = FastAPI()

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    print(data)
    calldata = data['event']['data']['block']['logs'][0]['transaction']['inputData']
    res_decode_calldata = get_decode_calldata(calldata)
    print(res_decode_calldata)
    return "success"