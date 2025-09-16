#!/usr/bin/env python3
"""
测试不同网络的EIP-1559支持情况
"""

from web3_call import get_w3
from web3_util import check_eip1559_support, auto_inject_poa_middleware_if_needed
from data_util import get_chain

def test_eip1559_support_for_chain(chain_id):
    """测试指定链的EIP-1559支持情况"""
    print(f"\n🔍 测试 Chain ID {chain_id} 的 EIP-1559 支持情况...")
    print("=" * 60)
    
    try:
        # 获取链信息
        chain_info = get_chain(chain_id=chain_id)
        if not chain_info:
            print(f"❌ 找不到 Chain ID {chain_id} 的配置信息")
            return False
        
        print(f"📊 网络信息:")
        print(f"  - Chain ID: {chain_id}")
        print(f"  - RPC URL: {chain_info.get('rpc_url', 'N/A')}")
        print(f"  - 是否主网: {chain_info.get('is_mainnet', 'N/A')}")
        print(f"  - 是否L2: {chain_info.get('is_l2', 'N/A')}")
        print(f"  - 配置中EIP-1559支持: {chain_info.get('is_eip1559', 'N/A')}")
        
        # 创建Web3连接
        print(f"\n🌐 连接网络...")
        w3 = get_w3(chain_id=chain_id)
        if not w3:
            print(f"❌ 无法连接到网络")
            return False
        
        print(f"✅ 网络连接成功")
        
        # 检查连接状态
        try:
            is_connected = w3.is_connected()
            print(f"📡 连接状态: {is_connected}")
        except:
            print(f"📡 连接状态: 无法检测")
        
        # 自动处理POA中间件
        print(f"\n🔧 检查POA中间件需求...")
        poa_result = auto_inject_poa_middleware_if_needed(w3)
        print(f"📋 POA处理结果: {poa_result}")
        
        # 获取网络基本信息
        print(f"\n📊 获取网络基本信息...")
        try:
            actual_chain_id = w3.eth.chain_id
            print(f"  - 实际Chain ID: {actual_chain_id}")
            
            block_number = w3.eth.block_number
            print(f"  - 当前区块号: {block_number:,}")
            
            gas_price = w3.eth.gas_price
            print(f"  - 当前Gas价格: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
            
        except Exception as e:
            print(f"⚠️ 获取基本信息时出错: {e}")
        
        # 测试EIP-1559支持
        print(f"\n🎯 测试EIP-1559支持...")
        try:
            # 方法1：使用内置函数检查
            supports_eip1559 = check_eip1559_support(w3)
            print(f"📋 check_eip1559_support() 结果: {supports_eip1559}")
            
            # 方法2：直接获取最新区块检查
            print(f"\n🔍 获取最新区块信息...")
            latest_block = w3.eth.get_block('latest')
            
            print(f"📊 区块信息:")
            print(f"  - 区块号: {latest_block.number:,}")
            print(f"  - Gas Limit: {latest_block.gasLimit:,}")
            print(f"  - Gas Used: {latest_block.gasUsed:,}")
            print(f"  - 利用率: {(latest_block.gasUsed/latest_block.gasLimit*100):.1f}%")
            
            # 检查EIP-1559字段
            has_base_fee = hasattr(latest_block, 'baseFeePerGas')
            print(f"  - 有baseFeePerGas字段: {has_base_fee}")
            
            if has_base_fee and latest_block.baseFeePerGas is not None:
                base_fee_gwei = w3.from_wei(latest_block.baseFeePerGas, 'gwei')
                print(f"  - Base Fee: {latest_block.baseFeePerGas} wei ({base_fee_gwei:.6f} gwei)")
                
                # 测试获取最大优先费
                try:
                    max_priority_fee = w3.eth.max_priority_fee
                    priority_fee_gwei = w3.from_wei(max_priority_fee, 'gwei')
                    print(f"  - Max Priority Fee: {max_priority_fee} wei ({priority_fee_gwei:.6f} gwei)")
                except Exception as e:
                    print(f"  - Max Priority Fee: 无法获取 ({e})")
                
                print(f"\n✅ 确认支持 EIP-1559!")
                return True
            else:
                print(f"\n❌ 不支持 EIP-1559 (没有baseFeePerGas)")
                return False
                
        except Exception as e:
            print(f"❌ 检查EIP-1559支持时出错: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 EIP-1559 支持情况测试脚本")
    print("=" * 60)
    
    # 要测试的网络列表
    test_chains = [
        {"chain_id": 80002, "name": "Polygon Amoy 测试网"},
        {"chain_id": 11155111, "name": "以太坊 Sepolia 测试网"},
        {"chain_id": 84532, "name": "Base Sepolia 测试网"},
        {"chain_id": 300, "name": "ZKSync Era Sepolia 测试网"},
        {"chain_id": 59902, "name": "Metis Sepolia 测试网"},
    ]
    
    results = {}
    
    for chain in test_chains:
        chain_id = chain["chain_id"]
        name = chain["name"]
        
        print(f"\n\n🌐 开始测试: {name}")
        result = test_eip1559_support_for_chain(chain_id)
        results[chain_id] = {
            "name": name,
            "supports_eip1559": result
        }
    
    # 输出总结
    print("\n\n" + "=" * 60)
    print("📊 EIP-1559 支持情况总结:")
    print("=" * 60)
    
    for chain_id, info in results.items():
        status = "✅ 支持" if info["supports_eip1559"] else "❌ 不支持"
        print(f"  {chain_id:>6} - {info['name']:<25} {status}")
    
    print("\n🎯 重点关注: Polygon Amoy (80002)")
    polygon_result = results.get(80002, {})
    if polygon_result.get("supports_eip1559"):
        print("✅ Polygon Amoy 确认支持 EIP-1559!")
    else:
        print("❌ Polygon Amoy 不支持 EIP-1559")

if __name__ == "__main__":
    main()
