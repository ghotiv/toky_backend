import time

from web3 import Web3

try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except Exception as e:
    from web3.middleware import geth_poa_middleware

from eth_abi import decode
from eth_utils import to_checksum_address, decode_hex, keccak, is_address, to_bytes

from my_conf import *

def get_wei_amount(human_amount, decimals=18):
    return int(human_amount * 10**decimals)

def get_bytes32_address(address):
    #暂时支持evm
    #有没'0x'都支持
    res = to_bytes(hexstr=address).rjust(32, b'\0')
    return res

def get_method_id(func_sign):
    return '0x'+keccak(text=func_sign).hex()[:8]

def decode_contract_error(error_data):
    """解码合约自定义错误"""
    # 常见的错误选择器映射
    error_selectors = {
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

def diagnose_insufficient_balance(w3, account_address, output_token, output_amount, chain_id, is_mainnet=True):
    """诊断InsufficientBalance错误的具体原因"""
    print(f"🔍 诊断余额不足问题...")
    
    try:
        # 1. 检查ETH余额（用于gas费）
        eth_balance = w3.eth.get_balance(account_address)
        eth_balance_readable = eth_balance / 10**18
        print(f"💰 ETH余额: {eth_balance_readable:.6f} ETH")
        
        # 2. 检查代币余额
        if output_token == '0x0000000000000000000000000000000000000000':
            # 如果是ETH转账，检查ETH余额是否足够
            output_amount_readable = output_amount / 10**18
            print(f"💸 需要转账: {output_amount_readable:.6f} ETH")
            if eth_balance < output_amount:
                print(f"❌ ETH余额不足！需要 {output_amount_readable:.6f} ETH，但只有 {eth_balance_readable:.6f} ETH")
                return False
            else:
                print(f"✅ ETH余额充足")
        else:
            # ERC20代币检查
            erc20_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
            ]
            
            try:
                token_contract = w3.eth.contract(address=output_token, abi=erc20_abi)
                token_balance = token_contract.functions.balanceOf(account_address).call()
                
                # 获取代币信息
                try:
                    decimals = token_contract.functions.decimals().call()
                    symbol = token_contract.functions.symbol().call()
                except:
                    decimals = 18
                    symbol = "TOKEN"
                
                token_balance_readable = token_balance / (10**decimals)
                output_amount_readable = output_amount / (10**decimals)
                
                print(f"🪙 {symbol}余额: {token_balance_readable:.6f}")
                print(f"💸 需要转账: {output_amount_readable:.6f} {symbol}")
                
                if token_balance < output_amount:
                    print(f"❌ {symbol}余额不足！需要 {output_amount_readable:.6f}，但只有 {token_balance_readable:.6f}")
                    return False
                else:
                    print(f"✅ {symbol}余额充足")
                    
            except Exception as e:
                print(f"⚠️ 无法检查代币余额: {e}")
        
        # 3. 检查gas费是否足够
        estimated_gas_cost = 200000 * w3.eth.gas_price  # 粗略估算
        gas_cost_readable = estimated_gas_cost / 10**18
        
        if eth_balance < estimated_gas_cost:
            print(f"❌ ETH余额不足支付gas费！预估需要 {gas_cost_readable:.6f} ETH")
            return False
        else:
            print(f"✅ ETH余额足够支付gas费（预估: {gas_cost_readable:.6f} ETH）")
            
        print(f"🤔 余额检查都通过了，InsufficientBalance可能由其他原因引起：")
        print(f"   - 合约内部逻辑限制")
        print(f"   - 代币授权问题")
        print(f"   - 合约暂停或其他状态问题")
        
        # 进一步检查代币授权状态
        if output_token != '0x0000000000000000000000000000000000000000':
            try:
                print(f"\n🔐 检查代币授权状态...")
                # 需要获取fillRelay合约地址来检查授权
                chain_dict = get_chain(chain_id=chain_id, is_mainnet=is_mainnet)
                if 'contract_fillRelay' in chain_dict:
                    fillrelay_address = chain_dict['contract_fillRelay']
                    
                    # 重新创建代币合约实例来检查授权
                    token_contract = w3.eth.contract(address=output_token, abi=erc20_abi)
                    allowance = token_contract.functions.allowance(account_address, fillrelay_address).call()
                    allowance_readable = allowance / (10**decimals)
                    output_amount_readable = output_amount / (10**decimals)
                    
                    print(f"📊 授权状态:")
                    print(f"   - 所有者: {account_address}")
                    print(f"   - 被授权者: {fillrelay_address}")
                    print(f"   - 当前授权额度: {allowance_readable:.6f} {symbol}")
                    print(f"   - 需要转账金额: {output_amount_readable:.6f} {symbol}")
                    
                    if allowance < output_amount:
                        print(f"❌ 代币授权不足！这可能是InsufficientBalance的真正原因")
                        print(f"   需要授权: {output_amount_readable:.6f} {symbol}")
                        print(f"   当前授权: {allowance_readable:.6f} {symbol}")
                        print(f"   缺少授权: {(output_amount - allowance) / (10**decimals):.6f} {symbol}")
                        return False
                    else:
                        print(f"✅ 代币授权充足: {allowance_readable:.6f} ≥ {output_amount_readable:.6f}")
                        
            except Exception as e:
                print(f"⚠️ 无法检查代币授权: {e}")
        
        # 检查其他可能的问题
        print(f"\n🔍 其他可能的InsufficientBalance原因:")
        print(f"   1. 合约可能有最小/最大转账限制")
        print(f"   2. 合约可能被暂停或处于维护模式")
        print(f"   3. 可能有时间锁或冷却期限制")
        print(f"   4. 可能有白名单/黑名单检查")
        print(f"   5. 跨链桥可能流动性不足")
        print(f"   6. 合约可能要求特定的调用顺序")
        
        return True
        
    except Exception as e:
        print(f"❌ 余额诊断失败: {e}")
        return False

def get_safe_nonce(w3, account_address):
    """获取安全的nonce，避免nonce冲突"""
    # 获取链上确认的nonce
    confirmed_nonce = w3.eth.get_transaction_count(account_address, 'latest')
    # 获取待处理的nonce  
    pending_nonce = w3.eth.get_transaction_count(account_address, 'pending')
    safe_nonce = max(confirmed_nonce, pending_nonce)
    
    # 检查是否有pending交易
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
        time.sleep(check_interval)
    
    print(f"⏰ 等待超时，pending交易可能卡住了")
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
        if chain_id == 300:  # ZKSync
            return w3.to_wei('0.25', 'gwei')
        elif is_l2:  # L2网络
            return w3.to_wei('0.001', 'gwei')  # 极低的默认价格
        else:  # 主网等
            return w3.to_wei('20', 'gwei')

def check_eip1559_support(w3):
    """检查网络是否支持EIP-1559"""
    try:
        latest_block = w3.eth.get_block('latest')
        return hasattr(latest_block, 'baseFeePerGas') and latest_block.baseFeePerGas is not None
    except:
        return False

def get_eip1559_params(w3, priority='standard', chain_id=None, is_l2=True):
    """获取EIP-1559参数"""
    if not chain_id:
        return None
    try:
        latest_block = w3.eth.get_block('latest')
        base_fee = latest_block.baseFeePerGas
        print(f"🔍 EIP-1559参数计算: Chain={chain_id}, Priority={priority}, is_L2={is_l2}, BaseFee={w3.from_wei(base_fee, 'gwei'):.6f} gwei")
        
        # 尝试获取网络建议的优先费用
        try:
            suggested_priority_fee = w3.eth.max_priority_fee
        except:
            suggested_priority_fee = None
        
        # 根据网络类型和优先级设置优先费用
        if not is_l2:
            # L1网络使用动态优先费用
            print(f"📊 L1网络优先费用计算...")
            if suggested_priority_fee:
                print(f"📊 使用建议优先费用: {w3.from_wei(suggested_priority_fee, 'gwei'):.6f} gwei")
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
            if priority == 'fast':
                priority_fee = max(base_fee // 50, 1)  # base_fee的2%，最少1 wei
            elif priority == 'slow':
                priority_fee = max(base_fee // 500, 1)  # base_fee的0.2%，最少1 wei
            else:  # standard
                priority_fee = max(base_fee // 100, 1)  # base_fee的1%，最少1 wei
        
        print(f"📊 计算结果: PriorityFee={w3.from_wei(priority_fee, 'gwei'):.6f} gwei")

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
        return None

def get_gas_buffer_multiplier(chain_id, tx_type='contract_call', is_l2=True):
    """根据网络特性和交易类型获取gas缓冲倍数"""
    if chain_id == 300:  # ZKSync
        return 2.5  # ZKSync需要更大缓冲
    elif not is_l2:  # 主网
        if tx_type == 'erc20_approve':
            return 1.8  # approve操作需要更大缓冲
        return 1.3  # 主网适中缓冲
    else:  # L2网络
        if tx_type == 'erc20_approve':
            return 2.0  # L2上approve也需要更大缓冲
        return 1.5  # L2网络中等缓冲

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
                         account_address=None, to_address=None, value=0, data='0x',is_l2=True):
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
        base_gas = get_fallback_gas_limit(chain_id, tx_type,is_l2=is_l2)
        print(f"⚠️ 无法估算gas，使用回退值: {base_gas:,}")
    
    # 步骤2: 应用网络特性缓冲
    buffer_multiplier = get_gas_buffer_multiplier(chain_id, tx_type, is_l2=is_l2)
    final_gas_limit = int(base_gas * buffer_multiplier)
    
    print(f"📊 最终gas limit: {final_gas_limit:,} (基础: {base_gas:,} × 缓冲: {buffer_multiplier})")
    
    return final_gas_limit

def get_gas_params(w3, account_address, chain_id=None, priority='standard', tx_type='contract_call', 
                        estimated_gas=None, is_eip1559=True, is_l2=True):
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
    gas_limit = get_optimal_gas_limit(w3, chain_id, tx_type, estimated_gas, account_address, is_l2=is_l2)
    gas_params['gas'] = gas_limit
    
    # 检测网络拥堵并调整优先级
    congestion = get_network_congestion(w3)
    if congestion == 'high' and priority == 'standard':
        priority = 'fast'
        print(f"⚠️ 检测到网络拥堵，自动调整为快速模式")
    
    # 检查是否支持EIP-1559
    if is_eip1559:
        print(f"🚀 使用EIP-1559模式")
        eip1559_params = get_eip1559_params(w3, priority, chain_id, is_l2)
        if eip1559_params:
            gas_params.update(eip1559_params)
            
            # 显示EIP-1559参数信息
            max_fee_gwei = w3.from_wei(eip1559_params['maxFeePerGas'], 'gwei')
            priority_fee_gwei = w3.from_wei(eip1559_params['maxPriorityFeePerGas'], 'gwei')
            print(f"📊 原始值: MaxFee={eip1559_params['maxFeePerGas']} wei, PriorityFee={eip1559_params['maxPriorityFeePerGas']} wei")
            print(f"📊 MaxFee: {max_fee_gwei:.6f} gwei, PriorityFee: {priority_fee_gwei:.6f} gwei")
            
            return gas_params
    
    # 传统gasPrice模式
    print(f"⚡ 使用传统gasPrice模式")
    gas_price = get_optimal_gas_price(w3, chain_id, priority, is_l2=is_l2)
    gas_params['gasPrice'] = gas_price
    
    # 显示gas价格信息
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    print(f"📊 GasPrice: {gas_price_gwei:.2f} gwei, GasLimit: {gas_limit:,}")
    
    return gas_params

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

#todo:数据来自数据库
def get_chain(chain_id=None,alchemy_network=None,is_mainnet=True):
    res_dicts = [
        #sepolia
        {
            'rpc_url': 'https://ethereum-sepolia-rpc.publicnode.com',
            'chain_id': 11155111,
            'contract_deposit': '0x5bD6e85cD235d4c01E04344897Fc97DBd9011155',
            'contract_fillRelay': '0x460a94c037CD5DFAFb043F0b9F24c1867957AA5c',
            'alchemy_network': 'ETH_SEPOLIA',
            'is_mainnet': False,
        },
        #base sepolia
        {
            'rpc_url': 'https://sepolia.base.org',
            'chain_id': 84532,
            'contract_deposit': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'BASE_SEPOLIA',
            'is_mainnet': False,
        },
        #zksync sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/zksync_era_sepolia',
            'chain_id': 300,
            'contract_deposit': '0x9AA8668E11B1e9670B4DC8e81add17751bA1a4Ea',
            'contract_fillRelay': '0xEE89DAD29eb36835336d8A5C212FD040336B0dCb',
            'alchemy_network': 'ZKSYNC_SEPOLIA',
            'is_mainnet': False,
        },
        #metis sepolia
        {
            'rpc_url': 'https://sepolia.metisdevops.link',
            'chain_id': 59902,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '',
            'alchemy_network': 'METIS_SEPOLIA',
            'is_mainnet': False,
        },
    ]
    [i.update({'is_eip1559': chain_id not in NOT_EIP1599_IDS}) for i in res_dicts]
    [i.update({'is_l2': chain_id not in L1_CHAIN_IDS}) for i in res_dicts]
    if is_mainnet:
        res_dicts = [item for item in res_dicts if item['is_mainnet'] == True]
    else:
        res_dicts = [item for item in res_dicts if item['is_mainnet'] == False]
    if chain_id:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id), {})
    if alchemy_network:
        res = next((item for item in res_dicts if item['alchemy_network'] == alchemy_network), {})
    return res


def get_w3(rpc_url='',chain_id='',is_mainnet=True):
    if chain_id:
        rpc_url = get_chain(chain_id=chain_id,is_mainnet=is_mainnet).get('rpc_url','')
    if not rpc_url:
        return
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    # print(w3.isConnected())
    return w3


def get_token(chain_id=None,token_name=None,token_address=None,is_mainnet=True):
    res = {}
    if token_name:
        token_name = token_name.upper()
    if token_address:
        token_address = to_checksum_address(token_address)
    res_dicts = [
        {
            'chain_id': 11155111,
            'token_name': 'MBT',
            'token_address': '0xF904709e8a2E0825FcE724002bE52Dd853202750',
            'is_mainnet': False,
        },
        {
            'chain_id': 11155111,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 84532,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 84532,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 300,
            'token_name': 'MBT',
            'token_address': '0x0c0CB7D85a0fADD43Be91656cAF933Fd18e98168',
            'is_mainnet': False,
        },
        {
            'chain_id': 300,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
    ]
    if is_mainnet:
        res_dicts = [item for item in res_dicts if item['is_mainnet'] == True]
    else:
        res_dicts = [item for item in res_dicts if item['is_mainnet'] == False]
    if chain_id and token_name:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id and item['token_name'] == token_name), {})
    if chain_id and token_address:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id and item['token_address'] == token_address), {})
    return res


def get_decode_calldata(calldata):
    res = {}
    method_id_transfer_deposit = get_method_id("deposit(address,bytes32,address,uint256,uint256,bytes)")
    method_id = calldata[:10]
    encoded_data = calldata[10:]
    if method_id == method_id_transfer_deposit:
        function_abi = [
            {"type": "address", "name": "vault"},
            {"type": "bytes32", "name": "recipient"},
            {"type": "address", "name": "inputToken"},
            {"type": "uint256", "name": "inputAmount"},
            {"type": "uint256", "name": "destinationChainId"},
            {"type": "bytes", "name": "message"},
        ]
        abi_types = [item["type"] for item in function_abi]
        decoded_data = decode(abi_types, decode_hex(encoded_data))
        vault,recipient,inputToken,inputAmount,destinationChainId,message = decoded_data
        res = {
            'vault':to_checksum_address(vault),
            'recipient':get_recipient_vaild_address(recipient),
            'inputToken':to_checksum_address(inputToken),
            'inputAmount':inputAmount,
            'destinationChainId':destinationChainId,
            'message':message
        }
    return res


def call_deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message, 
                    block_chainid, private_key=None, is_mainnet=True):
    res = None
    w3 = get_w3(chain_id=block_chainid,is_mainnet=is_mainnet)
    chain_dict = get_chain(chain_id=block_chainid,is_mainnet=is_mainnet)
    is_eip1559 = chain_dict['is_eip1559']
    is_l2 = chain_dict['is_l2']
    print(f"w3: {w3}")
    deposit_abi = [
        {
            "inputs": [
                {"name": "vault", "type": "address"},
                {"name": "recipient", "type": "bytes32"},
                {"name": "inputToken", "type": "address"},
                {"name": "inputAmount", "type": "uint256"},
                {"name": "destinationChainId", "type": "uint256"},
                {"name": "message", "type": "bytes"}
            ],
            "name": "deposit",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    contract_address = chain_dict['contract_deposit']
    contract = w3.eth.contract(address=contract_address, abi=deposit_abi)
    account = w3.eth.account.from_key(private_key)
    account_address = account.address
    
    # 首先构建基础交易参数来估算gas（不包含nonce，避免冲突）
    base_tx_params = {
        'from': account_address
    }
    
    if inputToken == '0x0000000000000000000000000000000000000000':
        base_tx_params['value'] = inputAmount
    
    estimated_gas = None
    # 先估算实际需要的gas
    try:
        print(f"📊 估算deposit交易gas...")
        estimated_gas = contract.functions.deposit(vault, recipient, inputToken, 
                        inputAmount, destinationChainId, message).estimate_gas(base_tx_params)
        print(f"📊 实际gas估算: {estimated_gas:,}")
    except Exception as e:
        print(f"⚠️ Gas估算失败: {e}")
    
    # 使用实际估算的gas获取优化的gas参数（在这里统一设置nonce）
    tx_params = get_gas_params(w3, account_address, block_chainid, 
                             priority='standard', tx_type='contract_call', 
                             estimated_gas=estimated_gas, is_eip1559=is_eip1559, is_l2=is_l2)
    
    if inputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = inputAmount
    
    try:
        print(f"🔍 模拟执行deposit...")
        call_result = contract.functions.deposit(vault, recipient, inputToken, 
                        inputAmount, destinationChainId, message).call(tx_params)
        print(f"🔍 模拟执行deposit成功: {call_result}, 可以发送交易")
    except Exception as call_error:
        decoded_error = decode_contract_error(call_error.args if hasattr(call_error, 'args') else call_error)
        error_msg = str(call_error)
        print(f"❌ 模拟执行deposit失败: {call_error}")
        print(f"🔍 错误解析: {decoded_error}")
        
        # 如果是out of gas错误，尝试增加gas limit
        if 'out of gas' in error_msg:
            print("🔧 检测到gas不足，尝试增加gas limit...")
            original_gas = tx_params['gas']
            tx_params['gas'] = int(original_gas * 2)  # 增加到2倍
            print(f"📊 调整gas limit: {original_gas:,} -> {tx_params['gas']:,}")
            
            try:
                print("🔍 重新模拟执行deposit...")
                call_result = contract.functions.deposit(vault, recipient, inputToken, 
                                inputAmount, destinationChainId, message).call(tx_params)
                print(f"✅ 增加gas后模拟执行成功: {call_result}, 可以发送交易")
            except Exception as e2:
                decoded_error2 = decode_contract_error(e2.args if hasattr(e2, 'args') else e2)
                print(f"❌ 增加gas后仍然失败: {e2}")
                print(f"🔍 最终错误解析: {decoded_error2}")
                return None
        else:
            # 其他类型的错误（包括InsufficientBalance）
            return None
    
    try:
        tx = contract.functions.deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message).build_transaction(tx_params)
        # print(f"交易参数: {tx}")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"交易确认，状态: {receipt.status}")
        res = tx_hash.hex()
    except Exception as e:
        error_message = str(e)
        print(f"交易失败: {e}")
        
        # 处理特定的错误情况
        if 'already known' in error_message:
            print(f"⚠️ deposit交易已存在于mempool中，尝试等待确认...")
            # 尝试等待现有交易确认
            if handle_already_known_transaction(w3, account_address, tx_params['nonce']):
                # 如果交易确认了，返回成功（但没有tx_hash）
                return "deposit_confirmed_by_existing"
            else:
                return None
        elif 'replacement transaction underpriced' in error_message:
            print(f"⚠️ replacement transaction underpriced - 需要更高的gas价格")
            return None
        else:
            raise
    return res


def check_relay_filled(originChainId, depositHash, recipient, outputToken, contract_address, w3):
    """检查relay是否已经被填充"""
    check_abi = [
        {
            "inputs": [
                {"name": "originChainId", "type": "uint256"},
                {"name": "depositHash", "type": "bytes32"},
                {"name": "recipient", "type": "address"},
                {"name": "outputToken", "type": "address"}
            ],
            "name": "isRelayFilled",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    try:
        contract = w3.eth.contract(address=contract_address, abi=check_abi)
        is_filled = contract.functions.isRelayFilled(originChainId, depositHash, recipient, outputToken).call()
        return is_filled
    except Exception as e:
        print(f"检查relay状态失败: {e}")
        return None


def call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        block_chainid, private_key, check_before_send=True,
                        is_mainnet=True):
    res = None
    w3 = get_w3(chain_id=block_chainid,is_mainnet=is_mainnet)
    chain_dict = get_chain(chain_id=block_chainid,is_mainnet=is_mainnet)
    is_eip1559 = chain_dict['is_eip1559']
    is_l2 = chain_dict['is_l2']
    contract_address = chain_dict['contract_fillRelay']

    print(f"call_fill_relay 入参 时间: {time.time()}: {recipient}, {outputToken}, {outputAmount}, {originChainId}, {depositHash.hex()}, {message}")

    if check_before_send:
        relay_filled = check_relay_filled(originChainId, depositHash, recipient, outputToken, contract_address, w3)
        if relay_filled is True:
            print(f"❌ RelayAlreadyFilled: 这个relay已经被填充过了,{depositHash.hex()}")
            return None
            
    fill_relay_abi = [
        {
            "inputs": [
                {"name": "recipient", "type": "address"},
                {"name": "outputToken", "type": "address"},
                {"name": "outputAmount", "type": "uint256"},
                {"name": "originChainId", "type": "uint256"},
                {"name": "depositHash", "type": "bytes32"},
                {"name": "message", "type": "bytes"}
            ],
            "name": "fillRelay",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]

    contract = w3.eth.contract(address=contract_address, abi=fill_relay_abi)
    account = w3.eth.account.from_key(private_key)
    account_address = account.address
    
    # 首先构建基础交易参数来估算gas（不包含nonce，避免冲突）
    base_tx_params = {
        'from': account_address
    }
    
    if outputToken == '0x0000000000000000000000000000000000000000':
        base_tx_params['value'] = outputAmount
    
    # 先估算实际需要的gas
    estimated_gas = None
    try:
        print(f"📊 估算fillRelay交易gas...")
        estimated_gas = contract.functions.fillRelay(recipient, outputToken, outputAmount, 
                        originChainId, depositHash, message).estimate_gas(base_tx_params)
        print(f"📊 实际gas估算: {estimated_gas:,}")
    except Exception as e:
        print(f"⚠️ Gas估算失败: {e}")
    
    # 使用实际估算的gas获取优化的gas参数（在这里统一设置nonce）
    tx_params = get_gas_params(w3, account_address, block_chainid, 
                             priority='standard', tx_type='contract_call', 
                             estimated_gas=estimated_gas, is_eip1559=is_eip1559, is_l2=is_l2)
    
    # 如果等待pending交易完成后需要重新检查relay状态
    if tx_params == "pending_completed_recheck_needed":
        print(f"🔍 Pending交易完成后重新检查relay状态...")
        if check_before_send:
            relay_filled = check_relay_filled(originChainId, depositHash, recipient, outputToken, contract_address, w3)
            if relay_filled is True:
                print(f"❌ RelayAlreadyFilled: Pending交易完成后发现relay已被填充,{depositHash.hex()}")
                return None
        
        # 重新获取gas参数
        tx_params = get_gas_params(w3, account_address, block_chainid, 
                                 priority='standard', tx_type='contract_call', 
                                 estimated_gas=estimated_gas, is_eip1559=is_eip1559, is_l2=is_l2)
    
    if not tx_params or tx_params == "pending_completed_recheck_needed":
        print(f"❌ 无法获取有效的gas参数")
        return None
    
    if outputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = outputAmount
    
    try:
        print(f"🔍 模拟执行fillRelay...")
        call_result = contract.functions.fillRelay(recipient, outputToken, 
                    outputAmount, originChainId, depositHash, message).call(tx_params)
        print(f"🔍 模拟执行fillRelay成功: {call_result}, 可以发送交易")
    except Exception as call_error:
        decoded_error = decode_contract_error(call_error.args if hasattr(call_error, 'args') else call_error)
        error_msg = str(call_error)
        print(f"❌ 模拟执行fillRelay失败: {call_error}")
        print(f"🔍 错误解析: {decoded_error}")
        
        # 如果是out of gas错误，尝试增加gas limit
        if 'out of gas' in error_msg:
            print("🔧 检测到gas不足，尝试增加gas limit...")
            original_gas = tx_params['gas']
            tx_params['gas'] = int(original_gas * 2)  # 增加到2倍
            print(f"📊 调整gas limit: {original_gas:,} -> {tx_params['gas']:,}")
            
            try:
                print("🔍 重新模拟执行fillRelay...")
                call_result = contract.functions.fillRelay(recipient, outputToken, 
                            outputAmount, originChainId, depositHash, message).call(tx_params)
                print(f"✅ 增加gas后模拟执行成功: {call_result}, 可以发送交易")
            except Exception as e2:
                decoded_error2 = decode_contract_error(e2.args if hasattr(e2, 'args') else e2)
                print(f"❌ 增加gas后仍然失败: {e2}")
                print(f"🔍 最终错误解析: {decoded_error2}")
                
                # 如果增加gas后仍然是InsufficientBalance，那就是真的余额问题
                if 'InsufficientBalance' in decoded_error2:
                    print("🔍 确认是真正的余额不足问题，进行详细诊断...")
                    diagnose_insufficient_balance(w3, account_address, outputToken, outputAmount, block_chainid, is_mainnet)
                
                return None
        elif 'InsufficientBalance' in decoded_error:
            # 直接是InsufficientBalance错误，进行余额诊断
            print("🔍 检测到InsufficientBalance错误，进行详细诊断...")
            diagnose_insufficient_balance(w3, account_address, outputToken, outputAmount, block_chainid, is_mainnet)
            return None
        else:
            # 其他类型的错误
            return None

    # 发送交易前再次检查relay状态（防止pending交易已经填充了这个relay）
    if check_before_send:
        print(f"🔍 发送交易前再次检查relay状态...")
        relay_filled = check_relay_filled(originChainId, depositHash, recipient, outputToken, contract_address, w3)
        if relay_filled is True:
            print(f"❌ RelayAlreadyFilled: 在准备发送交易时发现relay已被填充,{depositHash.hex()}")
            return None
    
    try:
        # print(f"交易参数: {tx_params}")
        tx = contract.functions.fillRelay(recipient, outputToken, outputAmount, originChainId,
                     depositHash, message).build_transaction(tx_params)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"交易确认，状态: {receipt.status}")
        res = tx_hash.hex()
    except Exception as e:
        error_message = str(e)
        print(f"交易失败: {e}")
        
        # 处理特定的错误情况
        if 'already known' in error_message:
            print(f"⚠️ fillRelay交易已存在于mempool中，尝试等待确认...")
            # 尝试等待现有交易确认
            if handle_already_known_transaction(w3, account_address, tx_params['nonce']):
                # 如果交易确认了，返回成功（但没有tx_hash）
                return "fillRelay_confirmed_by_existing"
            else:
                return None
        elif 'replacement transaction underpriced' in error_message:
            print(f"⚠️ replacement transaction underpriced - 需要更高的gas价格")
            return None
        else:
            raise
    return res


#todo FILL_RATE 来自across
def call_fill_relay_by_alchemy(data):
    '''
        calldata_dict = {'vault': '0xbA37D7ed1cFF3dDab5f23ee99525291dcA00999D', 
            'recipient': '0xd45F62ae86E01Da43a162AA3Cd320Fca3C1B178d', 
            'inputToken': '0x0000000000000000000000000000000000000000', 
            'inputAmount': 100000000000000, 
            'destinationChainId': 84532, 'message': b'hello'}
    '''
    res = None

    is_mainnet = True
    if DEBUG_MODE:
        is_mainnet = False

    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    alchemy_network = data['event']['network']
    calldata_dict = get_decode_calldata(transaction_dict['inputData'])
    block_chainid = calldata_dict['destinationChainId']
    vault = to_checksum_address(calldata_dict['vault'])
    print(f"vault: {vault}")
    if vault not in VAULTS:
        print(f"❌  vault not in VAULTS: {vault}")
        return None
    originChainId = get_chain(alchemy_network=alchemy_network,is_mainnet=is_mainnet)['chain_id']
    token_name_input = get_token(chain_id=originChainId,token_address=calldata_dict['inputToken'],
                                    is_mainnet=is_mainnet)['token_name']
    outputToken = get_token(chain_id=block_chainid,token_name=token_name_input,
                                    is_mainnet=is_mainnet).get('token_address',None)
    if not outputToken:
        print(f"❌ 代币不存在: {token_name_input}")
        return res
    outputAmount = int(calldata_dict['inputAmount']*FILL_RATE)
    message = b''
    recipient = to_checksum_address(calldata_dict['recipient'])
    depositHash = get_bytes32_address(transaction_dict['hash'])
    try:
        res = call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                                block_chainid, private_key=VAULT_PRIVATE_KEY, is_mainnet=is_mainnet)
    except Exception as e:
        print(f"❌ call_fill_relay_by_alchemy失败: {e}")
    return res