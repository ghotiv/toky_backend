import redis
import time
from contextlib import contextmanager

class DistributedDepositProcessor:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    @contextmanager
    def distributed_lock(self, lock_key, timeout=10):
        """分布式锁"""
        lock_value = str(time.time())
        try:
            # 尝试获取锁
            if self.redis_client.set(lock_key, lock_value, nx=True, ex=timeout):
                yield
            else:
                raise Exception(f"无法获取锁: {lock_key}")
        finally:
            # 释放锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            self.redis_client.eval(lua_script, 1, lock_key, lock_value)
    
    def check_and_mark_processed(self, deposit_hash):
        """原子性检查并标记处理"""
        key = f"processed_deposit:{deposit_hash}"
        
        # 使用 Redis 的原子操作
        result = self.redis_client.set(key, "1", nx=True, ex=86400)  # 24小时过期
        return result  # True=首次处理, False=重复
    
    def get_safe_nonce(self, vault_address):
        """跨进程安全的 nonce 获取"""
        lock_key = f"nonce_lock:{vault_address}"
        
        with self.distributed_lock(lock_key):
            # 从 Redis 获取当前 nonce
            nonce_key = f"current_nonce:{vault_address}"
            redis_nonce = self.redis_client.get(nonce_key)
            
            # 从链上获取最新 nonce
            chain_nonce = w3.eth.get_transaction_count(vault_address, 'pending')
            
            # 取较大值
            if redis_nonce:
                safe_nonce = max(int(redis_nonce), chain_nonce)
            else:
                safe_nonce = chain_nonce
            
            # 更新 Redis 中的 nonce
            self.redis_client.set(nonce_key, safe_nonce + 1, ex=3600)  # 1小时过期
            
            return safe_nonce

'''
# 全局分布式处理器
distributed_processor = DistributedDepositProcessor()

# 进程A: webhook 使用
async def webhook_process_deposit(data):
    deposit_hash = extract_deposit_hash(data)
    vault_address = extract_vault_address(data)
    
    # 跨进程去重检查
    if not distributed_processor.check_and_mark_processed(deposit_hash):
        return {"status": "duplicate_across_processes"}
    
    # 跨进程安全获取 nonce
    safe_nonce = distributed_processor.get_safe_nonce(vault_address)
    
    # 执行交易
    result = call_fill_relay_with_nonce(data, safe_nonce)
    return {"status": "success", "nonce": safe_nonce}

# 进程B: etherscan 使用相同逻辑
def etherscan_process_deposit(tx_dict):
    pass
    # ... 相同的处理逻辑
'''