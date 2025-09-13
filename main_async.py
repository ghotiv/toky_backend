import time
import asyncio

from fastapi import FastAPI
from typing import Dict, Any

from web3_util import call_fill_relay_by_alchemy

app = FastAPI()

async def process_fill_relay_async(data: Dict[str, Any], deposit_hash: str):
    """异步处理fillRelay任务"""
    try:
        # 在线程池中运行阻塞的区块链操作
        loop = asyncio.get_event_loop()
        tx_hash = await loop.run_in_executor(None, call_fill_relay_by_alchemy, data)
        print('time: ', time.time(), 'tx_hash: ', tx_hash, 'depositHash: ', deposit_hash)
    except Exception as e:
        print('time: ', time.time(), 'error: ', e, 'depositHash: ', deposit_hash)

@app.post("/webhook")
async def webhook(data: Dict[str, Any]):
    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    deposit_hash = transaction_dict['hash']
    print('time: ', time.time(), 'depositHash: ', deposit_hash)
    
    # 启动异步任务（不等待完成）
    asyncio.create_task(process_fill_relay_async(data, deposit_hash))
    
    # 立即返回响应
    return {"status": "accepted", "depositHash": deposit_hash}
