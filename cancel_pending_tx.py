#!/usr/bin/env python3
"""
取消卡住的pending交易的脚本
通过发送一个相同nonce但更高gas价格的空交易来替换卡住的交易
"""

from web3_call import get_w3
from web3_util import get_optimal_gas_price
from my_private_conf import VAULT_PRIVATE_KEY, VAULT

def cancel_pending_transaction(chain_id, account_private_key, account_address, stuck_nonce):
    """
    取消指定nonce的pending交易
    
    Args:
        chain_id: 链ID
        account_private_key: 账户私钥
        account_address: 账户地址
        stuck_nonce: 卡住的nonce
    """
    print(f"🔧 尝试取消 Chain {chain_id} 上nonce {stuck_nonce}的pending交易...")
    
    try:
        # 获取Web3连接
        w3 = get_w3(chain_id=chain_id)
        if not w3:
            print("❌ 无法连接到网络")
            return None
        
        # 获取当前gas价格
        current_gas_price = w3.eth.gas_price
        current_gas_gwei = w3.from_wei(current_gas_price, 'gwei')
        print(f"📊 当前网络gas价格: {current_gas_gwei:.2f} gwei")
        
        # 检查是否支持EIP-1559
        from my_conf import NOT_EIP1599_IDS
        supports_eip1559 = chain_id not in NOT_EIP1599_IDS
        
        # 初始化变量
        cancel_gas_gwei = 0
        
        if supports_eip1559:
            print(f"📊 使用EIP-1559模式")
            from web3_util import get_eip1559_params
            gas_params = get_eip1559_params(w3, priority='fast', is_l2=False)
            if gas_params:
                max_fee_gwei = w3.from_wei(gas_params['maxFeePerGas'], 'gwei')
                priority_fee_gwei = w3.from_wei(gas_params['maxPriorityFeePerGas'], 'gwei')
                cancel_gas_gwei = max_fee_gwei  # 使用MaxFee作为显示的gas价格
                print(f"📊 MaxFee: {max_fee_gwei:.2f} gwei, Priority: {priority_fee_gwei:.2f} gwei")
                
                # 构建EIP-1559取消交易
                cancel_tx = {
                    'from': account_address,
                    'to': account_address,
                    'value': 0,
                    'gas': 21000,
                    'maxFeePerGas': gas_params['maxFeePerGas'],
                    'maxPriorityFeePerGas': gas_params['maxPriorityFeePerGas'],
                    'nonce': stuck_nonce,
                    'chainId': chain_id,
                    'type': 2  # EIP-1559 transaction type
                }
            else:
                print(f"❌ 获取EIP-1559参数失败，回退到传统模式")
                supports_eip1559 = False
        
        if not supports_eip1559:
            print(f"📊 使用传统gasPrice模式")
            cancel_gas_price = get_optimal_gas_price(w3, chain_id, priority='fast', is_l2=False)
            cancel_gas_gwei = w3.from_wei(cancel_gas_price, 'gwei')
            print(f"📊 取消交易gas价格: {cancel_gas_gwei:.2f} gwei")
            
            # 构建传统取消交易
            cancel_tx = {
                'from': account_address,
                'to': account_address,
                'value': 0,
                'gas': 21000,
                'gasPrice': cancel_gas_price,
                'nonce': stuck_nonce,
                'chainId': chain_id
            }
        
        print(f"📋 取消交易参数:")
        print(f"  - From: {account_address}")
        print(f"  - To: {account_address}")
        print(f"  - Value: 0 ETH")
        print(f"  - Gas: 21,000")
        print(f"  - Gas Price: {cancel_gas_gwei:.2f} gwei")
        print(f"  - Nonce: {stuck_nonce}")
        
        # 确认执行
        confirm = input(f"\n确认发送取消交易? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 已取消")
            return None
        
        # 签名并发送交易
        signed_tx = w3.eth.account.sign_transaction(cancel_tx, private_key=account_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📤 取消交易已发送！")
        print(f"🔗 交易哈希: {tx_hash.hex()}")
        
        # 区块链浏览器链接
        if chain_id == 97:
            print(f"🔗 BSCScan: https://testnet.bscscan.com/tx/{tx_hash.hex()}")
        elif chain_id == 56:
            print(f"🔗 BSCScan: https://bscscan.com/tx/{tx_hash.hex()}")
        elif chain_id == 59141:
            print(f"🔗 LineaScan: https://sepolia.lineascan.build/tx/{tx_hash.hex()}")
        elif chain_id == 59144:
            print(f"🔗 LineaScan: https://lineascan.build/tx/{tx_hash.hex()}")
        elif chain_id == 11155111:
            print(f"🔗 Etherscan: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        elif chain_id == 1:
            print(f"🔗 Etherscan: https://etherscan.io/tx/{tx_hash.hex()}")
        elif chain_id == 84532:
            print(f"🔗 BaseScan: https://sepolia.basescan.org/tx/{tx_hash.hex()}")
        elif chain_id == 8453:
            print(f"🔗 BaseScan: https://basescan.org/tx/{tx_hash.hex()}")
        elif chain_id == 421614:
            print(f"🔗 Arbiscan: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
        elif chain_id == 42161:
            print(f"🔗 Arbiscan: https://arbiscan.io/tx/{tx_hash.hex()}")
        elif chain_id == 919:
            print(f"🔗 Mode Explorer: https://sepolia.explorer.mode.network/tx/{tx_hash.hex()}")
        else:
            print(f"🔗 交易哈希: {tx_hash.hex()}")
        
        return tx_hash.hex()
        
    except Exception as e:
        print(f"❌ 取消交易失败: {e}")
        return None

def check_account_status(chain_id, account_address):
    """检查账户当前状态"""
    print(f"🔍 检查账户状态...")
    
    try:
        w3 = get_w3(chain_id=chain_id)
        if not w3:
            print("❌ 无法连接到网络")
            return
        
        # 获取nonce信息
        confirmed_nonce = w3.eth.get_transaction_count(account_address, 'latest')
        pending_nonce = w3.eth.get_transaction_count(account_address, 'pending')
        
        print(f"📊 账户状态:")
        print(f"  - 地址: {account_address}")
        print(f"  - 已确认nonce: {confirmed_nonce}")
        print(f"  - 待处理nonce: {pending_nonce}")
        
        if pending_nonce > confirmed_nonce:
            print(f"⚠️ 检测到pending交易: nonce {confirmed_nonce} 到 {pending_nonce-1}")
            return confirmed_nonce, pending_nonce
        else:
            print(f"✅ 没有pending交易")
            return confirmed_nonce, confirmed_nonce
            
    except Exception as e:
        print(f"❌ 检查账户状态失败: {e}")
        return None, None

def main():
    """主函数"""
    import sys
    
    print("🔧 Pending交易取消工具")
    print("=" * 50)
    
    if len(sys.argv) >= 2:
        chain_id = int(sys.argv[1])
    else:
        chain_id = int(input("请输入链ID (例如97为BSC Testnet): "))
    
    # 默认使用VAULT账户
    account_address = VAULT
    account_private_key = VAULT_PRIVATE_KEY
    
    print(f"\n🌐 目标网络: Chain {chain_id}")
    print(f"👤 账户地址: {account_address}")
    
    # 检查账户状态
    confirmed_nonce, pending_nonce = check_account_status(chain_id, account_address)
    
    if confirmed_nonce is None:
        return
    
    if pending_nonce > confirmed_nonce:
        # 有pending交易
        stuck_nonce = confirmed_nonce
        print(f"\n🚨 发现卡住的交易: nonce {stuck_nonce}")
        
        # 取消pending交易
        result = cancel_pending_transaction(chain_id, account_private_key, account_address, stuck_nonce)
        
        if result:
            print(f"\n✅ 取消交易发送成功!")
            print(f"💡 请等待几分钟让网络处理，然后可以重新发送原始交易")
        else:
            print(f"\n❌ 取消交易失败")
    else:
        print(f"\n✅ 当前没有pending交易，账户状态正常")

if __name__ == "__main__":
    main()
