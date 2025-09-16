import time

from eth_utils import to_checksum_address, keccak, is_address, to_bytes

from my_conf import *

def is_poa_chain(w3):
    """检测是否为POA链"""
    try:
        chain_id = w3.eth.chain_id
        if chain_id in POA_CHAIN_IDS:
            return True, -2  # -2表示通过已知链ID识别
    except:
        pass
    
    try:
        # 尝试获取最新区块
        latest_block = w3.eth.get_block('latest')
        # 检查extraData字段长度，POA链通常大于32字节
        if hasattr(latest_block, 'extraData') and latest_block.extraData:
            extra_data_length = len(latest_block.extraData)
            # 标准以太坊区块的extraData最大32字节，POA链会更长
            if extra_data_length > 32:
                return True, extra_data_length
        return False, 0
    except Exception as e:
        # 如果获取区块失败，可能就是因为extraData问题，说明是POA链
        error_msg = str(e).lower()
        if 'extradata' in error_msg and ('bytes' in error_msg or 'should be 32' in error_msg):
            return True, -1  # -1表示通过错误信息推断
        return False, 0

def inject_poa_middleware(w3):
    """注入POA中间件的通用函数"""
    # 检查是否已经有POA中间件
    middleware_names = [str(middleware) for middleware in w3.middleware_onion]
    if any('poa' in name.lower() or 'extradata' in name.lower() for name in middleware_names):
        return "already_exists"
    
    try:
        # Web3.py 6.x+ 版本
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return "ExtraDataToPOAMiddleware"
    except ImportError:
        try:
            # Web3.py 5.x 版本
            from web3.middleware import geth_poa_middleware
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            return "geth_poa_middleware"
        except ImportError:
            try:
                # 备用导入路径
                from web3.middleware.geth_poa import geth_poa_middleware
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                return "geth_poa_middleware(alt)"
            except ImportError:
                return None

def auto_inject_poa_middleware_if_needed(w3):
    """自动检测并注入POA中间件（如果需要）"""
    try:
        # 先检测是否为POA链
        is_poa, extra_data_len = is_poa_chain(w3)
        
        if is_poa:
            print(f"🔍 检测到POA链 (ExtraData长度: {extra_data_len}字节)，注入POA中间件...")
            middleware_name = inject_poa_middleware(w3)
            if middleware_name == "already_exists":
                print(f"✅ POA中间件已存在")
                return "already_exists"
            elif middleware_name:
                print(f"✅ 已注入POA中间件: {middleware_name}")
                # 注入后立即验证
                try:
                    w3.eth.get_block('latest')
                    print(f"✅ POA中间件验证成功")
                except Exception as verify_e:
                    print(f"⚠️ POA中间件验证失败: {verify_e}")
                return middleware_name
            else:
                print(f"⚠️ 无法导入POA中间件")
                return None
        else:
            # 不是POA链，不需要中间件
            return "not_needed"
            
    except Exception as e:
        # 如果检测过程中遇到extraData错误，直接注入中间件
        error_msg = str(e).lower()
        if 'extradata' in error_msg:
            print(f"🔍 检测过程中遇到extraData错误，强制注入POA中间件...")
            middleware_name = inject_poa_middleware(w3)
            if middleware_name and middleware_name != "already_exists":
                print(f"✅ 已注入POA中间件: {middleware_name}")
                # 注入后立即验证
                try:
                    w3.eth.get_block('latest')
                    print(f"✅ 强制注入的POA中间件验证成功")
                except Exception as verify_e:
                    print(f"⚠️ 强制注入的POA中间件验证失败: {verify_e}")
            return middleware_name
        else:
            print(f"⚠️ POA检测失败: {e}")
            return None

def get_wei_amount(human_amount, decimals=18):
    return int(human_amount * 10**decimals)

def get_bytes32_address(address):
    #暂时支持evm
    #有没'0x'都支持
    res = to_bytes(hexstr=address).rjust(32, b'\0')
    return res

#暂时只支持evm地址
def get_recipient_vaild_address(recipient):
    res = None
    recipient_str = recipient.hex()
    if 24*'0' in recipient_str:
        recipient_replace = recipient_str.replace(24*'0','')
        if is_address(recipient_replace):
            #自动加0x前缀
            res = to_checksum_address(recipient_replace)
    return res

def get_method_id(func_sign):
    return '0x'+keccak(text=func_sign).hex()[:8]

def decode_contract_error(error_data):
    """解码合约自定义错误"""
    # 常见的错误选择器映射
    error_selectors = {
        '0xea8e4eb5': 'NotAuthorized()',
        '0x4ff64a9f': 'RelayAlreadyFilled()',
        '0x7a2c8890': 'InsufficientBalance()', 
        '0x8c379a00': 'Error(string)',  # 标准revert错误
        '0x4e487b71': 'Panic(uint256)',  # Panic错误
        '0x08c379a0': 'Error(string)',  # 另一种格式
        '0x1e4fbdf7': 'OwnableUnauthorizedAccount(address)',
        '0x49df728c': 'OwnableInvalidOwner(address)',
        '0x118cdaa7': 'AddressEmptyCode(address)',
        '0x5274afe7': 'AddressInsufficientBalance(address)',
        '0x7939f424': 'SafeERC20FailedOperation(address)',
        '0xa9059cbb': 'transfer(address,uint256)',  # ERC20 transfer
        '0x095ea7b3': 'approve(address,uint256)',   # ERC20 approve
    }
    
    if isinstance(error_data, tuple) and len(error_data) >= 1:
        error_selector = error_data[0]
        if error_selector in error_selectors:
            error_name = error_selectors[error_selector]
            print(f"🔍 解码错误: {error_selector} -> {error_name}")
            return error_name
        else:
            print(f"❓ 未知错误选择器: {error_selector}")
            return f"UnknownError({error_selector})"
    
    return str(error_data)

def get_safe_nonce(w3, account_address):
    """获取安全的nonce，使用pending避免冲突"""
    # 获取链上确认的nonce
    confirmed_nonce = w3.eth.get_transaction_count(account_address, 'latest')
    # 获取待处理的nonce  
    pending_nonce = w3.eth.get_transaction_count(account_address, 'pending')
    # 直接使用pending_nonce，让RPC节点自己处理nonce排队
    safe_nonce = pending_nonce
    has_pending = pending_nonce > confirmed_nonce
    print(f"📊 Nonce信息: 已确认={confirmed_nonce}, 待处理={pending_nonce}, 使用={safe_nonce}, Pending交易={has_pending}")
    return safe_nonce, has_pending

def wait_for_pending_transaction(w3, account_address, expected_nonce):
    """等待pending交易完成"""
    print(f"🔍 等待nonce {expected_nonce}的pending交易完成...")
    
    max_wait_time = 60  # 最多等待60秒
    check_interval = 1  # 每1秒检查一次
    
    for i in range(max_wait_time // check_interval):
        confirmed_nonce = w3.eth.get_transaction_count(account_address, 'latest')
        pending_nonce = w3.eth.get_transaction_count(account_address, 'pending')
        
        # 如果confirmed nonce已经超过了expected nonce，说明交易已完成
        if confirmed_nonce > expected_nonce:
            print(f"✅ Pending交易已确认，当前confirmed nonce: {confirmed_nonce}")
            return True
        
        # 如果没有pending交易了，也说明完成了
        if confirmed_nonce == pending_nonce:
            print(f"✅ 没有pending交易了，当前nonce: {confirmed_nonce}")
            return True
        
        elapsed_time = (i + 1) * check_interval
        print(f"⏳ 等待pending交易完成... ({elapsed_time}s/{max_wait_time}s) - 确认:{confirmed_nonce}, 待处理:{pending_nonce}")
        
        # 每隔10秒检查一次网络状态
        if elapsed_time % 10 == 0:
            try:
                current_gas_price = w3.eth.gas_price
                print(f"🔍 网络状态检查: 当前gas价格={w3.from_wei(current_gas_price, 'gwei'):.12f} gwei")
            except:
                pass
        
        time.sleep(check_interval)
    
    print(f"⏰ 等待超时，pending交易可能卡住了")
    print(f"💡 建议: 如果是测试环境，可以考虑使用更高的gas价格")
    print(f"📊 最终状态: 确认nonce={confirmed_nonce}, 待处理nonce={pending_nonce}")
    return False

def handle_already_known_transaction(w3, account_address, nonce):
    """处理already known交易，尝试等待确认"""
    print(f"🔍 检查nonce {nonce}的交易状态...")
    
    # 等待一段时间，检查交易是否被确认
    max_wait_time = 30  # 最多等待30秒
    check_interval = 1  # 每1秒检查一次
    
    for i in range(max_wait_time // check_interval):
        current_confirmed = w3.eth.get_transaction_count(account_address, 'latest')
        if current_confirmed > nonce:
            print(f"✅ Nonce {nonce}的交易已确认")
            return True
        
        print(f"⏳ 等待交易确认... ({i*check_interval}s/{max_wait_time}s)")
        time.sleep(check_interval)
    
    print(f"⏰ 等待超时，交易可能仍在pending状态")
    return False

def get_optimal_gas_price(w3, chain_id, priority='standard', is_l2=True):
    """获取优化的gas价格"""
    if not chain_id:
        return None
    try:
        # 获取当前网络gas价格
        current_gas_price = w3.eth.gas_price
        
        # Polygon网络特殊处理：需要满足最低gas price要求
        if chain_id == 80002:  # Polygon Amoy
            min_gas_price = w3.to_wei('25', 'gwei')
            base_price = max(current_gas_price, min_gas_price)
            print(f"📊 Polygon Amoy 最低gas price: {w3.from_wei(min_gas_price, 'gwei')} gwei")
            print(f"📊 调整后base price: {w3.from_wei(base_price, 'gwei')} gwei")
            if priority == 'fast':
                return int(base_price * 1.2)  # 提高20%
            elif priority == 'slow':
                return base_price  # 使用最低价格
            else:  # standard
                return int(base_price * 1.1)  # 提高10%
        elif chain_id in [137, 80001]:  # Polygon Mainnet/Mumbai
            min_gas_price = w3.to_wei('30', 'gwei')
            base_price = max(current_gas_price, min_gas_price)
            print(f"📊 Polygon 最低gas price: {w3.from_wei(min_gas_price, 'gwei')} gwei")
            if priority == 'fast':
                return int(base_price * 1.2)
            elif priority == 'slow':
                return base_price
            else:  # standard
                return int(base_price * 1.1)
        elif chain_id in [421614, 42161]:  # Arbitrum Sepolia/Mainnet
            # Arbitrum 使用动态pricing，基于网络实际价格
            print(f"📊 Arbitrum 动态gas price: {w3.from_wei(current_gas_price, 'gwei')} gwei")
            if priority == 'fast':
                return int(current_gas_price * 1.5)
            elif priority == 'slow':
                return int(current_gas_price * 1.1)
            else:  # standard
                return int(current_gas_price * 1.25)
        elif chain_id in [97, 56]:  # BSC Testnet/Mainnet
            # BSC 网络使用动态计算，基于当前网络价格
            current_gwei = w3.from_wei(current_gas_price, 'gwei')
            print(f"📊 BSC 传统模式当前网络gas价格: {current_gwei:.2f} gwei")
            
            # 基于当前价格的动态倍数，与EIP-1559模式保持一致
            if priority == 'fast':
                multiplier = 3.0  # 快速：当前价格的3倍
                gas_price = int(current_gas_price * multiplier)
            elif priority == 'slow':
                multiplier = 1.2  # 慢速：当前价格的1.2倍  
                gas_price = int(current_gas_price * multiplier)
            else:  # standard
                multiplier = 1.5  # 标准：当前价格的1.5倍
                gas_price = int(current_gas_price * multiplier)
            
            # 设置最低限制，避免过低
            min_fee = w3.to_wei('0.1', 'gwei')  # 最低0.1 gwei
            gas_price = max(gas_price, min_fee)
            
            final_gwei = w3.from_wei(gas_price, 'gwei')
            print(f"📊 BSC 传统模式 {priority} gas价格: {final_gwei:.2f} gwei (当前价格 × {multiplier})")
            return gas_price
        
        # L2网络策略：完全基于实际价格动态调整
        if is_l2:
            # L2网络使用实际价格的倍数，如果价格为0则使用1 wei作为基础
            base_price = max(current_gas_price, 1)  # 确保不为0
            if priority == 'fast':
                return int(base_price * 5)  # 5倍确保快速确认
            elif priority == 'slow':
                return int(base_price * 1.2)  # 1.2倍节省费用
            else:  # standard
                return int(base_price * 2.5)  # 2.5倍平衡速度和成本
        
        # ZKSync特殊处理：基于实际价格动态调整
        if chain_id == 300:
            base_price = max(current_gas_price, 1)  # 确保不为0
            if priority == 'fast':
                return int(base_price * 2)  # 2倍确保确认
            elif priority == 'slow':
                return int(base_price * 1.1)  # 1.1倍节省费用
            else:  # standard
                return int(base_price * 1.5)  # 1.5倍平衡
        
        # 主网和其他网络使用动态价格
        if priority == 'fast':
            return int(current_gas_price * 1.25)  # 提高25%确保快速确认
        elif priority == 'slow':
            return int(current_gas_price * 0.85)  # 降低15%节省费用
        else:  # standard
            return int(current_gas_price * 1.05)  # 略微提高5%确保确认
            
    except Exception as e:
        print(f"⚠️ 获取动态gas价格失败，使用默认值: {e}")
        # 回退到保守的默认价格（只在完全无法获取价格时使用）
        if chain_id == 80002:  # Polygon Amoy
            return w3.to_wei('25', 'gwei')
        elif chain_id in [137, 80001]:  # Polygon networks
            return w3.to_wei('30', 'gwei')
        elif chain_id in [421614, 42161]:  # Arbitrum networks
            return w3.to_wei('0.1', 'gwei')
        elif chain_id in [97, 56]:  # BSC networks
            return w3.to_wei('5', 'gwei')  # BSC 保守默认值
        elif chain_id == 300:  # ZKSync
            return w3.to_wei('0.25', 'gwei')
        elif is_l2:  # L2网络
            return w3.to_wei('0.001', 'gwei')  # 极低的默认价格
        else:  # 主网等
            return w3.to_wei('20', 'gwei')

#数据库里面提前设置
def check_eip1559_support(w3):
    """检查网络是否支持EIP-1559"""
    try:
        # 自动检测并注入POA中间件（如果需要）
        auto_inject_poa_middleware_if_needed(w3)
        
        latest_block = w3.eth.get_block('latest')
        return hasattr(latest_block, 'baseFeePerGas') and latest_block.baseFeePerGas is not None
    except:
        return False

def get_eip1559_params(w3, priority='standard', is_l2=None):
    """获取EIP-1559参数"""
    chain_id = w3.eth.chain_id
    if not chain_id:
        return None
    
    # 如果没有显式指定is_l2，根据链配置自动判断
    if is_l2 is None:
        from data_util import get_chain
        try:
            chain_config = get_chain(chain_id=chain_id)
            is_l2 = chain_config.get('is_l2', True)  # 默认为L2
        except:
            is_l2 = True  # 回退默认值
    try:
        # 自动检测并注入POA中间件（如果需要）
        auto_inject_poa_middleware_if_needed(w3)
        
        latest_block = w3.eth.get_block('latest')
        base_fee = latest_block.baseFeePerGas
        print(f"🔍 EIP-1559参数计算: Chain={chain_id}, Priority={priority}, is_L2={is_l2}, BaseFee={w3.from_wei(base_fee, 'gwei'):.12f} gwei")
        
        # 尝试获取网络建议的优先费用
        try:
            suggested_priority_fee = w3.eth.max_priority_fee
        except:
            suggested_priority_fee = None
        
        # 根据网络类型和优先级设置优先费用
        if not is_l2:
            # L1网络使用动态优先费用
            print(f"📊 L1网络优先费用计算...")
            
            # BSC网络特殊处理 - 基于链上实际价格的动态倍数
            if chain_id in [97, 56]:  # BSC Testnet/Mainnet
                print(f"📊 BSC网络动态优先费用计算...")
                
                # 获取当前网络实际gas价格
                try:
                    current_gas_price = w3.eth.gas_price
                    current_gwei = w3.from_wei(current_gas_price, 'gwei')
                    print(f"📊 当前网络gas价格: {current_gwei:.2f} gwei")
                    
                    # 基于当前价格设置动态倍数
                    if priority == 'fast':
                        multiplier = 3.0  # 快速：当前价格的3倍
                        priority_fee = int(current_gas_price * multiplier)
                    elif priority == 'slow':
                        multiplier = 1.2  # 慢速：当前价格的1.2倍  
                        priority_fee = int(current_gas_price * multiplier)
                    else:  # standard
                        multiplier = 2.0  # 标准：当前价格的2倍
                        priority_fee = int(current_gas_price * multiplier)
                    
                    # 设置最低限制，避免过低
                    min_fee = w3.to_wei('0.1', 'gwei')  # 最低0.1 gwei
                    priority_fee = max(priority_fee, min_fee)
                    
                    final_gwei = w3.from_wei(priority_fee, 'gwei')
                    print(f"📊 BSC {priority} 优先费用: {final_gwei:.2f} gwei (当前价格 × {multiplier})")
                    
                except Exception as e:
                    print(f"⚠️ 获取当前gas价格失败，使用默认值: {e}")
                    # 回退到固定值
                    if priority == 'fast':
                        priority_fee = w3.to_wei('2', 'gwei')
                    elif priority == 'slow':
                        priority_fee = w3.to_wei('0.2', 'gwei')
                    else:  # standard
                        priority_fee = w3.to_wei('0.5', 'gwei')
                    print(f"📊 BSC {priority} 优先费用(回退): {w3.from_wei(priority_fee, 'gwei')} gwei")
            elif suggested_priority_fee:
                print(f"📊 使用建议优先费用: {w3.from_wei(suggested_priority_fee, 'gwei'):.12f} gwei")
                if priority == 'fast':
                    priority_fee = int(suggested_priority_fee * 1.5)
                elif priority == 'slow':
                    priority_fee = int(suggested_priority_fee * 0.8)
                else:  # standard
                    priority_fee = suggested_priority_fee
            else:
                print(f"📊 使用base_fee计算优先费用...")
                # 回退到基于base_fee的动态值
                if priority == 'fast':
                    priority_fee = max(base_fee // 10, 1)  # base_fee的10%，最少1 wei
                elif priority == 'slow':
                    priority_fee = max(base_fee // 50, 1)  # base_fee的2%，最少1 wei
                else:  # standard
                    priority_fee = max(base_fee // 20, 1)  # base_fee的5%，最少1 wei
        else:
            # L2网络优先费用基于base_fee的百分比
            print(f"📊 L2网络优先费用计算...")
            
            # 为不同L2网络设置特定的最低优先费用
            if chain_id == 80002:  # Polygon Amoy
                min_priority_fee = w3.to_wei('25', 'gwei')  # Polygon 要求最少25 gwei
                print(f"📊 Polygon Amoy 最低优先费用: {w3.from_wei(min_priority_fee, 'gwei')} gwei")
            elif chain_id in [137, 80001]:  # Polygon Mainnet/Mumbai
                min_priority_fee = w3.to_wei('30', 'gwei')  # Polygon 主网通常需要更高
            elif chain_id in [421614, 42161]:  # Arbitrum Sepolia/Mainnet
                min_priority_fee = w3.to_wei('0.01', 'gwei')  # Arbitrum 使用较低的费用
                print(f"📊 Arbitrum 最低优先费用: {w3.from_wei(min_priority_fee, 'gwei')} gwei")
            elif chain_id in [97, 56]:  # BSC Testnet/Mainnet - L2模式动态计算
                try:
                    current_gas_price = w3.eth.gas_price
                    current_gwei = w3.from_wei(current_gas_price, 'gwei')
                    print(f"📊 BSC L2模式当前网络gas价格: {current_gwei:.2f} gwei")
                    
                    # L2模式使用更保守的倍数
                    min_priority_fee = int(current_gas_price * 1.5)  # 当前价格的1.5倍
                    min_priority_fee = max(min_priority_fee, w3.to_wei('0.1', 'gwei'))  # 最低0.1 gwei
                    
                    print(f"📊 BSC L2模式最低优先费用: {w3.from_wei(min_priority_fee, 'gwei'):.2f} gwei (当前价格 × 1.5)")
                except Exception as e:
                    print(f"⚠️ BSC L2模式获取gas价格失败，使用默认值: {e}")
                    min_priority_fee = w3.to_wei('0.5', 'gwei')  # 回退默认值
                    print(f"📊 BSC L2模式最低优先费用(回退): {w3.from_wei(min_priority_fee, 'gwei')} gwei")
            else:
                min_priority_fee = w3.to_wei('0.001', 'gwei')  # 其他L2的默认最低值
            
            if priority == 'fast':
                priority_fee = max(base_fee // 50, min_priority_fee)
            elif priority == 'slow':
                priority_fee = max(base_fee // 500, min_priority_fee)
            else:  # standard
                priority_fee = max(base_fee // 100, min_priority_fee)
        
        print(f"📊 计算结果: PriorityFee={w3.from_wei(priority_fee, 'gwei'):.12f} gwei")

        # 计算最大费用
        if not is_l2:
            # L1网络：base_fee可能快速变化，使用较大的倍数
            max_fee = int(base_fee * 2) + priority_fee
        else:
            # L2网络：base_fee变化不大，使用较小的倍数
            max_fee = int(base_fee * 1.5) + priority_fee
        
        return {
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': priority_fee,
            'type': '0x2'  # EIP-1559 transaction type
        }
    except Exception as e:
        print(f"⚠️ 获取EIP-1559参数失败: {e}")
        return None

def get_network_congestion(w3):
    """检测网络拥堵程度"""
    try:
        # 自动检测并注入POA中间件（如果需要）
        auto_inject_poa_middleware_if_needed(w3)
        
        latest_block = w3.eth.get_block('latest')
        if latest_block.gasLimit > 0:
            utilization = latest_block.gasUsed / latest_block.gasLimit
            
            if utilization > 0.9:
                return 'high'
            elif utilization > 0.7:
                return 'medium'
            else:
                return 'low'
    except:
        pass
    return 'unknown'

def estimate_gas_for_tx_type(w3, tx_type, account_address, to_address=None, value=0, data='0x'):
    """基于交易类型估算gas使用量"""
    try:
        if tx_type == 'eth_transfer':
            # ETH转账的基础估算
            tx_params = {
                'from': account_address,
                'to': to_address or account_address,  # 如果没有to地址，用自己
                'value': value or w3.to_wei('0.001', 'ether'),  # 小额测试
            }
            return w3.eth.estimate_gas(tx_params)
            
        elif tx_type in ['erc20_transfer', 'erc20_approve']:
            # ERC20交易估算（使用标准的transfer/approve方法）
            # 构造标准ERC20方法调用data
            if tx_type == 'erc20_transfer':
                # transfer(address,uint256) 方法签名
                method_id = '0xa9059cbb'
            else:  # erc20_approve
                # approve(address,uint256) 方法签名  
                method_id = '0x095ea7b3'
            
            # 构造完整的calldata (方法ID + 32字节地址 + 32字节金额)
            calldata = method_id + '0' * 24 + (to_address or account_address)[2:] + '0' * 64
            
            tx_params = {
                'from': account_address,
                'to': to_address or account_address,
                'data': calldata,
            }
            return w3.eth.estimate_gas(tx_params)
            
        else:
            # 对于复杂合约调用，如果有data就用，否则估算空调用
            tx_params = {
                'from': account_address,
                'to': to_address or account_address,
                'data': data,
            }
            return w3.eth.estimate_gas(tx_params)
            
    except Exception as e:
        print(f"⚠️ Gas估算失败: {e}")
        # 对于特殊网络，尝试使用更大的基础估算
        if w3.eth.chain_id in [421614, 42161]:
            print(f"🔧 Arbitrum网络，尝试使用保守估算...")
            if tx_type == 'erc20_approve':
                return 100000  # Arbitrum approve 保守估算
            elif tx_type == 'erc20_transfer':
                return 80000
            elif tx_type == 'contract_call':
                return 150000
            else:
                return 100000
        elif w3.eth.chain_id in [97, 56]:
            print(f"🔧 BSC网络，尝试使用保守估算...")
            if tx_type == 'erc20_approve':
                return 80000  # BSC approve 保守估算
            elif tx_type == 'erc20_transfer':
                return 60000
            elif tx_type == 'contract_call':
                return 120000
            else:
                return 80000
        return None

def get_gas_buffer_multiplier(chain_id, tx_type='contract_call', is_l2=True):
    """根据网络特性和交易类型获取gas缓冲倍数"""
    if chain_id == 300:  # ZKSync
        return 2.5  # ZKSync需要更大缓冲
    elif chain_id in [421614, 42161]:  # Arbitrum networks
        if tx_type == 'erc20_approve':
            return 4.0  # Arbitrum approve操作gas估算特别不准
        elif tx_type == 'contract_call':
            return 3.0  # 复杂合约调用需要更大缓冲
        else:
            return 2.5  # 其他操作也需要较大缓冲
    elif chain_id in [97, 56]:  # BSC networks
        if tx_type == 'erc20_approve':
            return 3.0  # BSC approve操作需要更大缓冲
        elif tx_type == 'contract_call':
            return 2.5  # BSC合约调用缓冲
        else:
            return 2.0  # BSC其他操作缓冲
    elif not is_l2:  # 主网
        if tx_type == 'erc20_approve':
            return 1.8  # approve操作需要更大缓冲
        return 1.3  # 主网适中缓冲
    else:  # L2网络
        if tx_type == 'erc20_approve':
            return 2.0  # L2上approve也需要更大缓冲
        return 1.5  # L2网络中等缓冲

# 没估算gas时使用，还没完全测试
def get_fallback_gas_limit(chain_id, tx_type, is_l2=True):
    """当无法估算时的回退gas limit"""
    if chain_id == 300:  # ZKSync
        gas_map = {
            'eth_transfer': 300000,
            'erc20_transfer': 500000,
            'erc20_approve': 500000,
            'contract_call': 1000000,
            'complex_contract': 1500000
        }
    elif chain_id in [421614, 42161]:  # Arbitrum networks
        gas_map = {
            'eth_transfer': 50000,
            'erc20_transfer': 120000,
            'erc20_approve': 150000,  # Arbitrum approve需要更多gas
            'contract_call': 250000,
            'complex_contract': 400000
        }
    elif chain_id in [97, 56]:  # BSC networks
        gas_map = {
            'eth_transfer': 25000,
            'erc20_transfer': 80000,
            'erc20_approve': 120000,  # BSC approve保守估算
            'contract_call': 200000,
            'complex_contract': 350000
        }
    elif not is_l2:  # 主网
        gas_map = {
            'eth_transfer': 25000,
            'erc20_transfer': 80000,
            'erc20_approve': 100000,  # 增加approve的回退值
            'contract_call': 200000,
            'complex_contract': 350000
        }
    else:  # L2网络
        gas_map = {
            'eth_transfer': 25000,
            'erc20_transfer': 70000,
            'erc20_approve': 90000,  # 增加approve的回退值
            'contract_call': 150000,
            'complex_contract': 250000
        }
    
    return gas_map.get(tx_type, gas_map['contract_call'])

def get_optimal_gas_limit(w3, chain_id, tx_type='contract_call', estimated_gas=None, 
                         account_address=None, to_address=None, value=0, data='0x', is_l2=True):
    """获取优化的gas limit - 基于实际估算而非固定值"""
    
    # 步骤1: 确定基础gas使用量
    base_gas = None
    
    if estimated_gas:
        # 如果外部已提供估算值，直接使用
        base_gas = estimated_gas
        print(f"📊 使用提供的gas估算: {base_gas:,}")
    elif w3 and account_address:
        # 尝试实际估算
        estimated = estimate_gas_for_tx_type(w3, tx_type, account_address, to_address, value, data)
        if estimated:
            base_gas = estimated
            print(f"📊 Gas估算成功: {base_gas:,}")
    
    if not base_gas:
        # 无法估算，使用回退值
        base_gas = get_fallback_gas_limit(chain_id, tx_type, is_l2=is_l2)
        print(f"⚠️ 无法估算gas，使用回退值: {base_gas:,}")
    
    # 步骤2: 应用网络特性缓冲
    buffer_multiplier = get_gas_buffer_multiplier(chain_id, tx_type, is_l2=is_l2)
    final_gas_limit = int(base_gas * buffer_multiplier)
    
    print(f"📊 最终gas limit: {final_gas_limit:,} (基础: {base_gas:,} × 缓冲: {buffer_multiplier})")
    
    return final_gas_limit

def get_gas_params(w3, account_address, chain_id=None, priority='standard', tx_type='contract_call', 
                        estimated_gas=None, is_eip1559=True, is_l2=None):
    """
    获取优化的gas参数
    
    Args:
        w3: Web3实例
        account_address: 账户地址
        chain_id: 链ID
        priority: 优先级 ('slow', 'standard', 'fast')
        tx_type: 交易类型 ('eth_transfer', 'erc20_transfer', 'erc20_approve', 'contract_call')
        estimated_gas: 预估的gas使用量
    """
    # 如果没有提供chain_id，尝试从w3获取
    if chain_id is None:
        try:
            chain_id = w3.eth.chain_id
        except:
            chain_id = 0
    
    # 如果没有显式指定is_l2，根据链配置自动判断
    if is_l2 is None:
        from data_util import get_chain
        try:
            chain_config = get_chain(chain_id=chain_id)
            is_l2 = chain_config.get('is_l2', True)  # 默认为L2
            print(f"🔍 自动检测网络类型: Chain {chain_id} -> {'L2' if is_l2 else 'L1'}")
        except:
            is_l2 = True  # 回退默认值
            print(f"⚠️ 无法检测网络类型，使用默认L2")
    
    print(f"⛽ 优化gas参数: Chain {chain_id}, Priority {priority}, Type {tx_type}")
    
    # 基础参数
    safe_nonce, has_pending = get_safe_nonce(w3, account_address)
    gas_params = {
        'from': account_address,
        'nonce': safe_nonce,
    }
    
    # 如果有pending交易，等待其完成而不是尝试替换
    if has_pending:
        print(f"⚠️ 检测到pending交易，等待其完成...")
        if wait_for_pending_transaction(w3, account_address, safe_nonce - 1):
            print(f"✅ Pending交易已完成，继续发送新交易")
            # 重新获取nonce，因为pending交易已完成
            safe_nonce, has_pending = get_safe_nonce(w3, account_address)
            gas_params['nonce'] = safe_nonce
            
            # 等待pending交易完成后，返回特殊标记，让调用方重新检查relay状态
            return "pending_completed_recheck_needed"
        else:
            print(f"⏰ Pending交易等待超时，可能需要手动处理")
            return None
    
    # 设置gas limit - 传递更多上下文信息以便更好地估算
    gas_limit = get_optimal_gas_limit(w3, chain_id, tx_type, estimated_gas, account_address, None, 0, '0x', is_l2=is_l2)
    gas_params['gas'] = gas_limit
    
    # 检测网络拥堵并调整优先级
    congestion = get_network_congestion(w3)
    if congestion == 'high' and priority == 'standard':
        priority = 'fast'
        print(f"⚠️ 检测到网络拥堵，自动调整为快速模式")
    
    # 检查是否支持EIP-1559
    if is_eip1559:
        print(f"🚀 使用EIP-1559模式")
        eip1559_params = get_eip1559_params(w3, priority, is_l2)
        if eip1559_params:
            gas_params.update(eip1559_params)
            
            # 显示EIP-1559参数信息
            max_fee_gwei = w3.from_wei(eip1559_params['maxFeePerGas'], 'gwei')
            priority_fee_gwei = w3.from_wei(eip1559_params['maxPriorityFeePerGas'], 'gwei')
            print(f"📊 原始值: MaxFee={eip1559_params['maxFeePerGas']} wei, PriorityFee={eip1559_params['maxPriorityFeePerGas']} wei")
            print(f"📊 MaxFee: {max_fee_gwei:.12f} gwei, PriorityFee: {priority_fee_gwei:.12f} gwei")
            
            return gas_params
    
    # 传统gasPrice模式
    print(f"⚡ 使用传统gasPrice模式")
    gas_price = get_optimal_gas_price(w3, chain_id, priority, is_l2=is_l2)
    gas_params['gasPrice'] = gas_price
    
    # 显示gas价格信息
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    print(f"📊 GasPrice: {gas_price_gwei:.2f} gwei, GasLimit: {gas_limit:,}")
    
    return gas_params