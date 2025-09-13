import time
from collections import OrderedDict

from fastapi import FastAPI, BackgroundTasks
from typing import Dict, Any

from web3_util import call_fill_relay_by_alchemy

class LRUCache:
    def __init__(self, max_size=500):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def add(self, key):
        """添加key到缓存，如果已存在返回False，新添加返回True"""
        if key in self.cache:
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return False  # 已存在
        
        self.cache[key] = time.time()
        
        # 超过限制时删除最老的
        if len(self.cache) > self.max_size:
            oldest_key, _ = self.cache.popitem(last=False)
            print(f"🗑️ LRU缓存已满，移除最老的: {oldest_key[:16]}...")
        
        return True  # 新添加
    
    def size(self):
        return len(self.cache)

# 全局LRU缓存实例
processed_requests = LRUCache(max_size=500)

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
    
    # LRU缓存去重检查
    if not processed_requests.add(deposit_hash):
        print(f'🔄 重复请求已拦截: {deposit_hash}')
        return {"status": "duplicate", "depositHash": deposit_hash, "message": "Request already processed"}
    
    print(f'📊 LRU缓存状态: {processed_requests.size()}/500')
    
    # 添加后台任务
    background_tasks.add_task(process_fill_relay, data, deposit_hash)
    
    # 立即返回响应
    return {"status": "accepted", "depositHash": deposit_hash}