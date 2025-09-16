#!/usr/bin/env python3
"""
添加授权Relayer的脚本
使用deployer账户调用addAuthorizedRelayer函数
"""

import time
import sys
from data_util import *
from web3_util import *
from web3_call import *
from my_private_conf import DEPLOYER_PRIVATE_KEY
from my_conf import DEBUG_MODE

# addAuthorizedRelayer ABI
ADD_RELAYER_ABI = [
    {
        "inputs": [
            {"name": "relayer", "type": "address"}
        ],
        "name": "addAuthorizedRelayer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def add_authorized_relayer(chain_id, relayer_address):
    """添加授权的relayer"""
    print(f"🚀 开始添加授权Relayer...")
    print(f"📊 网络: Chain {chain_id}")
    print(f"🎯 Relayer地址: {relayer_address}")
    
    try:
        # 获取Web3实例和链配置
        w3 = get_w3(chain_id=chain_id)
        chain_dict = get_chain(chain_id=chain_id)
        
        # 检查链配置是否存在
        if not chain_dict:
            print(f"❌ 不支持的链ID: {chain_id}")
            return None
        
        # 获取fillRelay合约地址（通常这个合约也有addAuthorizedRelayer功能）
        contract_address = chain_dict.get('contract_fillRelay')
        if not contract_address or contract_address == '' or contract_address == '0x1234567890123456789012345678901234567890':
            print(f"❌ 链ID {chain_id} 的 fillRelay 合约地址未配置或无效")
            print(f"💡 请在 data_util.py 中配置正确的合约地址")
            return None
        print(f"📍 合约地址: {contract_address}")
        
        # 创建合约实例
        contract = w3.eth.contract(address=contract_address, abi=ADD_RELAYER_ABI)
        
        # 获取deployer账户
        account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
        account_address = account.address
        print(f"👤 Deployer地址: {account_address}")
        
        # 构建基础交易参数（用于模拟调用）
        base_tx_params = {
            'from': account_address
        }
        
        # 估算gas
        try:
            print(f"📊 估算addAuthorizedRelayer交易gas...")
            estimated_gas = contract.functions.addAuthorizedRelayer(relayer_address).estimate_gas(base_tx_params)
            print(f"📊 实际gas估算: {estimated_gas:,}")
        except Exception as e:
            print(f"⚠️ 无法估算gas，使用默认值: {e}")
            estimated_gas = 100000
        
        # 获取优化的gas参数
        is_l2 = chain_dict.get('is_l2', True)
        tx_params = get_gas_params(w3, account_address, chain_id=chain_id, 
                                 priority='standard', tx_type='contract_call',
                                 estimated_gas=estimated_gas, 
                                 is_eip1559=chain_dict.get('is_eip1559', True),
                                 is_l2=is_l2)
        
        if isinstance(tx_params, str):
            print(f"❌ 获取gas参数失败: {tx_params}")
            return None
        
        # 模拟执行检查
        print(f"🔍 模拟执行addAuthorizedRelayer...")
        try:
            result = contract.functions.addAuthorizedRelayer(relayer_address).call(base_tx_params)
            print(f"🔍 模拟执行成功: {result}")
        except Exception as e:
            print(f"❌ 模拟执行失败: {e}")
            return None
        
        # 构建完整交易
        transaction = contract.functions.addAuthorizedRelayer(relayer_address).build_transaction(tx_params)
        
        # 签名交易
        signed_tx = account.sign_transaction(transaction)
        
        # 发送交易
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"✅ 交易已发送，哈希: {tx_hash.hex()}")
        
        # 等待确认
        print(f"⏳ 等待交易确认...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ 交易确认成功！")
            print(f"📊 Gas使用量: {receipt.gasUsed:,}")
            print(f"💰 交易费用: {receipt.gasUsed * receipt.effectiveGasPrice / 10**18:.8f} ETH")
            return tx_hash.hex()
        else:
            print(f"❌ 交易失败，status: {receipt.status}")
            return None
            
    except Exception as e:
        print(f"❌ 添加授权Relayer失败: {e}")
        return None

def main():
    """主函数"""
    print("🔧 添加授权Relayer脚本")
    print("=" * 50)
    
    print(f"🌐 当前模式: {DEBUG_MODE}")
    
    # 支持的网络
    networks = {
        "1": {"name": "以太坊主网", "chain_id": 1},
        "2": {"name": "以太坊Sepolia测试网", "chain_id": 11155111},
        "3": {"name": "Base主网", "chain_id": 8453},
        "4": {"name": "Base测试网", "chain_id": 84532},
        "5": {"name": "ZKSync Era主网", "chain_id": 324},
        "6": {"name": "ZKSync Era测试网", "chain_id": 300},
    }
    
    # 命令行参数处理
    if len(sys.argv) >= 3:
        try:
            chain_id = int(sys.argv[1])
            relayer_address = sys.argv[2]
            
            if not relayer_address.startswith('0x') or len(relayer_address) != 42:
                print(f"❌ 无效的地址格式: {relayer_address}")
                return
                
            print(f"📋 使用命令行参数:")
            print(f"   Chain ID: {chain_id}")
            print(f"   Relayer地址: {relayer_address}")
            
            tx_hash = add_authorized_relayer(chain_id, relayer_address)
            if tx_hash:
                print(f"\n🎉 成功添加授权Relayer！")
                print(f"🔗 交易哈希: {tx_hash}")
            else:
                print(f"\n❌ 添加授权Relayer失败")
                
        except ValueError:
            print(f"❌ 无效的Chain ID: {sys.argv[1]}")
            return
    else:
        # 交互式模式
        print("\n可用网络:")
        for key, network in networks.items():
            print(f"  {key}. {network['name']} (Chain ID: {network['chain_id']})")
        
        try:
            choice = input("\n请选择网络 (1-6): ").strip()
            if choice not in networks:
                print("❌ 无效的选择")
                return
                
            chain_id = networks[choice]["chain_id"]
            network_name = networks[choice]["name"]
            
            relayer_address = input("请输入要授权的Relayer地址: ").strip()
            if not relayer_address.startswith('0x') or len(relayer_address) != 42:
                print(f"❌ 无效的地址格式")
                return
            
            print(f"\n📋 执行参数:")
            print(f"   网络: {network_name}")
            print(f"   Chain ID: {chain_id}")
            print(f"   Relayer地址: {relayer_address}")
            
            confirm = input("\n确认执行? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ 已取消")
                return
            
            print("\n" + "=" * 50)
            tx_hash = add_authorized_relayer(chain_id, relayer_address)
            
            if tx_hash:
                print(f"\n🎉 成功添加授权Relayer！")
                print(f"🔗 交易哈希: {tx_hash}")
            else:
                print(f"\n❌ 添加授权Relayer失败")
                
        except KeyboardInterrupt:
            print(f"\n❌ 用户取消")
            return
        except Exception as e:
            print(f"❌ 输入错误: {e}")
            return

if __name__ == "__main__":
    main()
