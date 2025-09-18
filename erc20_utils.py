"""
ERC20 代币授权和余额检查工具函数
优化 gas 估算和错误处理
"""

from web3 import Web3
from eth_utils import to_checksum_address
from web3_util import get_w3, get_gas_params
from data_util import get_chain

# 标准 ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def check_erc20_balance(token_address, account_address, chain_id):
    """检查 ERC20 代币余额"""
    try:
        w3 = get_w3(chain_id=chain_id)
        if not w3 or not w3.is_connected():
            print(f"❌ 无法连接到网络: {chain_id}")
            return 0
        
        token_contract = w3.eth.contract(
            address=to_checksum_address(token_address), 
            abi=ERC20_ABI
        )
        
        balance = token_contract.functions.balanceOf(
            to_checksum_address(account_address)
        ).call()
        
        # 获取代币精度
        try:
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            balance_formatted = balance / (10 ** decimals)
            print(f"💰 {symbol} 余额: {balance_formatted:.6f} ({balance} wei)")
        except:
            print(f"💰 代币余额: {balance} wei")
        
        return balance
        
    except Exception as e:
        print(f"❌ 检查余额失败: {e}")
        return 0

def check_erc20_allowance(token_address, owner_address, spender_address, chain_id):
    """检查 ERC20 代币授权额度"""
    try:
        w3 = get_w3(chain_id=chain_id)
        if not w3 or not w3.is_connected():
            print(f"❌ 无法连接到网络: {chain_id}")
            return 0
        
        token_contract = w3.eth.contract(
            address=to_checksum_address(token_address), 
            abi=ERC20_ABI
        )
        
        allowance = token_contract.functions.allowance(
            to_checksum_address(owner_address),
            to_checksum_address(spender_address)
        ).call()
        
        # 获取代币信息
        try:
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            allowance_formatted = allowance / (10 ** decimals)
            print(f"🔓 {symbol} 授权额度: {allowance_formatted:.6f} ({allowance} wei)")
        except:
            print(f"🔓 授权额度: {allowance} wei")
        
        return allowance
        
    except Exception as e:
        print(f"❌ 检查授权失败: {e}")
        return 0

def approve_erc20_optimized(token_address, spender_address, amount, chain_id, private_key):
    """优化的 ERC20 授权函数，带有智能 gas 估算"""
    try:
        w3 = get_w3(chain_id=chain_id)
        if not w3 or not w3.is_connected():
            print(f"❌ 无法连接到网络: {chain_id}")
            return None
        
        # 获取链配置
        chain_config = get_chain(chain_id=chain_id)
        is_eip1559 = chain_config.get('is_eip1559', True)
        is_l2 = chain_config.get('is_l2', True)
        
        # 创建账户和合约实例
        account = w3.eth.account.from_key(private_key)
        account_address = account.address
        
        token_contract = w3.eth.contract(
            address=to_checksum_address(token_address), 
            abi=ERC20_ABI
        )
        
        print(f"🔓 开始授权 ERC20 代币...")
        print(f"📍 代币地址: {token_address}")
        print(f"📍 被授权地址: {spender_address}")
        print(f"📍 授权数量: {amount}")
        
        # 构建基础交易参数
        base_tx_params = {'from': account_address}
        
        # 智能 gas 估算
        estimated_gas = None
        try:
            print(f"📊 估算授权交易 gas...")
            estimated_gas = token_contract.functions.approve(
                to_checksum_address(spender_address), 
                amount
            ).estimate_gas(base_tx_params)
            print(f"📊 实际 gas 估算: {estimated_gas:,}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Gas 估算失败: {e}")
            
            if 'out of gas' in error_msg or 'gas required exceeds' in error_msg:
                # 提取需要的 gas 数量
                import re
                gas_match = re.search(r'gas required exceeds: (\d+)', error_msg)
                if gas_match:
                    required_gas = int(gas_match.group(1))
                    estimated_gas = int(required_gas * 3.0)  # 增加200%缓冲（授权操作需要更多缓冲）
                    print(f"🔧 检测到授权 gas 不足，大幅增加 gas limit...")
                    print(f"📊 调整 gas limit: {required_gas:,} -> {estimated_gas:,}")
                else:
                    estimated_gas = 150000  # 授权操作的保守默认值
                    print(f"📊 使用授权操作的保守 gas 估算: {estimated_gas:,}")
            else:
                estimated_gas = 120000  # 标准授权操作默认值
                print(f"📊 使用标准授权 gas 估算: {estimated_gas:,}")
        
        # 获取优化的 gas 参数
        tx_params = get_gas_params(
            w3, account_address, chain_id, 
            priority='standard', 
            tx_type='erc20_approve',  # 指定为授权操作
            estimated_gas=estimated_gas, 
            is_eip1559=is_eip1559, 
            is_l2=is_l2
        )
        
        if not tx_params or tx_params == "pending_completed_recheck_needed":
            print(f"❌ 无法获取 gas 参数")
            return None
        
        # 构建授权交易
        transaction = token_contract.functions.approve(
            to_checksum_address(spender_address), 
            amount
        ).build_transaction(tx_params)
        
        # 签名并发送
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"✅ 授权交易已发送: {tx_hash.hex()}")
        
        # 等待确认
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(f"✅ 授权交易确认成功")
                return tx_hash.hex()
            else:
                print(f"❌ 授权交易失败")
                return None
        except Exception as e:
            print(f"⏰ 等待授权确认超时: {e}")
            return tx_hash.hex()  # 返回 hash，让调用者自己检查
        
    except Exception as e:
        print(f"❌ 授权操作失败: {e}")
        return None

def ensure_erc20_allowance(token_address, owner_address, spender_address, required_amount, chain_id, private_key):
    """确保有足够的 ERC20 授权额度，不足时自动授权"""
    try:
        # 检查当前授权额度
        current_allowance = check_erc20_allowance(token_address, owner_address, spender_address, chain_id)
        
        if current_allowance >= required_amount:
            print(f"✅ 授权额度充足: {current_allowance} >= {required_amount}")
            return True
        
        print(f"⚠️ 授权额度不足: {current_allowance} < {required_amount}")
        print(f"🔓 开始自动授权...")
        
        # 授权一个较大的数量，避免频繁授权
        # 使用 required_amount 的 10 倍或最小 1000000 * 10^18
        approve_amount = max(required_amount * 10, 1000000 * 10**18)
        
        result = approve_erc20_optimized(token_address, spender_address, approve_amount, chain_id, private_key)
        
        if result:
            print(f"✅ 自动授权成功")
            return True
        else:
            print(f"❌ 自动授权失败")
            return False
            
    except Exception as e:
        print(f"❌ 确保授权额度失败: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    print("ERC20 工具函数测试")
