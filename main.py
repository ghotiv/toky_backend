import time
from collections import OrderedDict

from fastapi import FastAPI, BackgroundTasks
from typing import Dict, Any

from web3_call import call_fill_relay_by_alchemy

app = FastAPI()

def process_fill_relay(data: Dict[str, Any], deposit_hash: str):
    """后台处理fillRelay任务"""
    try:
        tx_hash = call_fill_relay_by_alchemy(data)
        print('time: ', time.time(), 'tx_hash: ', tx_hash, 'depositHash: ', deposit_hash)
    except Exception as e:
        print('time: ', time.time(), 'error: ', e, 'depositHash: ', deposit_hash)

@app.post("/webhook")
def webhook(data: Dict[str, Any], background_tasks: BackgroundTasks):
    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    deposit_hash = transaction_dict['hash']
    print('time: ', time.time(), 'depositHash: ', deposit_hash)
    
    # 添加后台任务
    background_tasks.add_task(process_fill_relay, data, deposit_hash)
    
    # 立即返回响应
    return {"status": "accepted", "depositHash": deposit_hash}