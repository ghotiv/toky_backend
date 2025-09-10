
from fastapi import FastAPI
from typing import Dict, Any

from web3_util import call_fill_relay_by_alchemy,get_decode_calldata

app = FastAPI()

import time
import uuid

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    # 生成请求追踪ID
    request_trace_id = str(uuid.uuid4())[:8]
    current_time = time.time()
    
    print(f"🎯 [WEBHOOK-{request_trace_id}] 收到请求 - 时间戳: {current_time}")
    
    try:
        transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
        print(f'🎯 [WEBHOOK-{request_trace_id}] depositHash: {transaction_dict["hash"]}')
        
        tx_hash = call_fill_relay_by_alchemy(data)
        
        print(f'🎯 [WEBHOOK-{request_trace_id}] fill_relay_hash: {tx_hash}')
        print(f'🎯 [WEBHOOK-{request_trace_id}] 请求处理完成')
        
        return "success"
    except Exception as e:
        print(f'🎯 [WEBHOOK-{request_trace_id}] 请求处理失败: {e}')
        raise