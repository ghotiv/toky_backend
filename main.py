
from fastapi import FastAPI
from typing import Dict, Any

from web3_util import call_fill_replay_by_alchemy

app = FastAPI()

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    print(data)
    tx_hash = call_fill_replay_by_alchemy(data)
    print(tx_hash)
    return "success"