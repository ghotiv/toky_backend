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

def get_safe_nonce(w3, account_address):
    """获取安全的nonce，避免nonce冲突"""
    # 获取链上确认的nonce
    confirmed_nonce = w3.eth.get_transaction_count(account_address, 'latest')
    # 获取待处理的nonce  
    pending_nonce = w3.eth.get_transaction_count(account_address, 'pending')
    safe_nonce = max(confirmed_nonce, pending_nonce)
    print(f"📊 Nonce信息: 已确认={confirmed_nonce}, 待处理={pending_nonce}, 使用={safe_nonce}")
    return safe_nonce

def get_optimal_gas_price(w3, chain_id, priority='standard'):
    """获取优化的gas价格"""
    if not chain_id:
        return None
    try:
        # 获取当前网络gas价格
        current_gas_price = w3.eth.gas_price
        
        # L2网络策略：完全基于实际价格动态调整
        if chain_id not in l1_chain_ids:
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
        elif chain_id not in l1_chain_ids:  # L2网络
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

def get_eip1559_params(w3, priority='standard', chain_id=None):
    """获取EIP-1559参数"""
    if not chain_id:
        return None
    try:
        latest_block = w3.eth.get_block('latest')
        base_fee = latest_block.baseFeePerGas
        
        # 尝试获取网络建议的优先费用
        try:
            suggested_priority_fee = w3.eth.max_priority_fee
        except:
            suggested_priority_fee = None
        
        # 根据网络类型和优先级设置优先费用
        if chain_id in l1_chain_ids:
            # L1网络使用动态优先费用
            if suggested_priority_fee:
                if priority == 'fast':
                    priority_fee = int(suggested_priority_fee * 1.5)
                elif priority == 'slow':
                    priority_fee = int(suggested_priority_fee * 0.8)
                else:  # standard
                    priority_fee = suggested_priority_fee
            else:
                # 回退到基于base_fee的动态值
                if priority == 'fast':
                    priority_fee = max(base_fee // 10, 1)  # base_fee的10%，最少1 wei
                elif priority == 'slow':
                    priority_fee = max(base_fee // 50, 1)  # base_fee的2%，最少1 wei
                else:  # standard
                    priority_fee = max(base_fee // 20, 1)  # base_fee的5%，最少1 wei
        else:
            # L2网络优先费用基于base_fee的百分比
            if priority == 'fast':
                priority_fee = max(base_fee // 50, 1)  # base_fee的2%，最少1 wei
            elif priority == 'slow':
                priority_fee = max(base_fee // 500, 1)  # base_fee的0.2%，最少1 wei
            else:  # standard
                priority_fee = max(base_fee // 100, 1)  # base_fee的1%，最少1 wei
        
        # 计算最大费用
        if chain_id in l1_chain_ids:
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

def get_gas_buffer_multiplier(chain_id):
    """根据网络特性获取gas缓冲倍数"""
    if chain_id == 300:  # ZKSync
        return 2.5  # ZKSync需要更大缓冲
    elif chain_id in l1_chain_ids:  # 主网
        return 1.3  # 主网适中缓冲
    else:  # L2网络
        return 1.5  # L2网络中等缓冲

def get_fallback_gas_limit(chain_id, tx_type):
    """当无法估算时的回退gas limit"""
    if chain_id == 300:  # ZKSync
        gas_map = {
            'eth_transfer': 300000,
            'erc20_transfer': 500000,
            'erc20_approve': 500000,
            'contract_call': 1000000,
            'complex_contract': 1500000
        }
    elif chain_id in l1_chain_ids:  # 主网
        gas_map = {
            'eth_transfer': 25000,
            'erc20_transfer': 80000,
            'erc20_approve': 80000,
            'contract_call': 200000,
            'complex_contract': 350000
        }
    else:  # L2网络
        gas_map = {
            'eth_transfer': 25000,
            'erc20_transfer': 70000,
            'erc20_approve': 70000,
            'contract_call': 150000,
            'complex_contract': 250000
        }
    
    return gas_map.get(tx_type, gas_map['contract_call'])

def get_optimal_gas_limit(w3, chain_id, tx_type='contract_call', estimated_gas=None, 
                         account_address=None, to_address=None, value=0, data='0x'):
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
        base_gas = get_fallback_gas_limit(chain_id, tx_type)
        print(f"⚠️ 无法估算gas，使用回退值: {base_gas:,}")
    
    # 步骤2: 应用网络特性缓冲
    buffer_multiplier = get_gas_buffer_multiplier(chain_id)
    final_gas_limit = int(base_gas * buffer_multiplier)
    
    print(f"📊 最终gas limit: {final_gas_limit:,} (基础: {base_gas:,} × 缓冲: {buffer_multiplier})")
    
    return final_gas_limit

def get_gas_params(w3, account_address, chain_id=None, priority='standard', tx_type='contract_call', 
                        estimated_gas=None, is_eip1559=True):
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
    gas_params = {
        'from': account_address,
        'nonce': get_safe_nonce(w3, account_address),
    }
    
    # 设置gas limit - 传递更多上下文信息以便更好地估算
    gas_limit = get_optimal_gas_limit(w3, chain_id, tx_type, estimated_gas, account_address)
    gas_params['gas'] = gas_limit
    
    # 检测网络拥堵并调整优先级
    congestion = get_network_congestion(w3)
    if congestion == 'high' and priority == 'standard':
        priority = 'fast'
        print(f"⚠️ 检测到网络拥堵，自动调整为快速模式")
    
    # 检查是否支持EIP-1559
    if is_eip1559:
        print(f"🚀 使用EIP-1559模式")
        eip1559_params = get_eip1559_params(w3, priority, chain_id)
        if eip1559_params:
            gas_params.update(eip1559_params)
            
            # 显示EIP-1559参数信息
            max_fee_gwei = w3.from_wei(eip1559_params['maxFeePerGas'], 'gwei')
            priority_fee_gwei = w3.from_wei(eip1559_params['maxPriorityFeePerGas'], 'gwei')
            print(f"📊 MaxFee: {max_fee_gwei:.2f} gwei, PriorityFee: {priority_fee_gwei:.2f} gwei")
            
            return gas_params
    
    # 传统gasPrice模式
    print(f"⚡ 使用传统gasPrice模式")
    gas_price = get_optimal_gas_price(w3, chain_id, priority)
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
            'is_eip1559': True,
        },
        #base sepolia
        {
            'rpc_url': 'https://sepolia.base.org',
            'chain_id': 84532,
            'contract_deposit': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'BASE_SEPOLIA',
            'is_mainnet': False,
            'is_eip1559': True,
        },
        #zksync sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/zksync_era_sepolia',
            'chain_id': 300,
            'contract_deposit': '0x9AA8668E11B1e9670B4DC8e81add17751bA1a4Ea',
            'contract_fillRelay': '0xEE89DAD29eb36835336d8A5C212FD040336B0dCb',
            'alchemy_network': 'ZKSYNC_SEPOLIA',
            'is_mainnet': False,
            'is_eip1559': True,
        },
        #metis sepolia
        {
            'rpc_url': 'https://sepolia.metisdevops.link',
            'chain_id': 59902,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '',
            'alchemy_network': 'METIS_SEPOLIA',
            'is_mainnet': False,
            'is_eip1559': True,
        },
    ]
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
    contract_address = get_chain(chain_id=block_chainid,is_mainnet=is_mainnet)['contract_deposit']
    contract = w3.eth.contract(address=contract_address, abi=deposit_abi)
    account = w3.eth.account.from_key(private_key)
    account_address = account.address
    
    # 首先构建基础交易参数来估算gas
    base_tx_params = {
        'from': account_address,
        'nonce': get_safe_nonce(w3, account_address)
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
    
    # 使用实际估算的gas获取优化的gas参数
    tx_params = get_gas_params(w3, account_address, block_chainid, 
                             priority='standard', tx_type='contract_call', 
                             estimated_gas=estimated_gas, is_eip1559=is_eip1559)
    
    if inputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = inputAmount
    
    try:
        print(f"🔍 模拟执行deposit...")
        call_result = contract.functions.deposit(vault, recipient, inputToken, 
                        inputAmount, destinationChainId, message).call(tx_params)
        print(f"🔍 模拟执行deposit成功: {call_result}, 可以发送交易")
    except Exception as call_error:
        print(f"❌ 模拟执行deposit失败: {call_error}")
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
        print(f"交易失败: {e}")
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
    
    # 首先构建基础交易参数来估算gas
    base_tx_params = {
        'from': account_address,
        'nonce': get_safe_nonce(w3, account_address)
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
    
    # 使用实际估算的gas获取优化的gas参数
    tx_params = get_gas_params(w3, account_address, block_chainid, 
                             priority='standard', tx_type='contract_call', 
                             estimated_gas=estimated_gas, is_eip1559=is_eip1559)
    
    if outputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = outputAmount
    
    try:
        print(f"🔍 模拟执行fillRelay...")
        call_result = contract.functions.fillRelay(recipient, outputToken, 
                    outputAmount, originChainId, depositHash, message).call(tx_params)
        print(f"🔍 模拟执行fillRelay成功: {call_result}, 可以发送交易")
    except Exception as call_error:
        print(f"❌ 模拟执行fillRelay失败: {call_error}")
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
        print(f"交易失败: {e}")
        raise
    return res


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
    originChainId = get_chain(alchemy_network=alchemy_network,is_mainnet=is_mainnet)['chain_id']
    token_name_input = get_token(chain_id=originChainId,token_address=calldata_dict['inputToken'],
                                    is_mainnet=is_mainnet)['token_name']
    outputToken = get_token(chain_id=block_chainid,token_name=token_name_input,
                                    is_mainnet=is_mainnet).get('token_address',None)
    if not outputToken:
        print(f"❌ 代币不存在: {token_name_input}")
        return res
    outputAmount = int(calldata_dict['inputAmount']*fill_rate)
    message = b''
    recipient = to_checksum_address(calldata_dict['recipient'])
    depositHash = get_bytes32_address(transaction_dict['hash'])
    res = call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                             block_chainid, private_key=vault_private_key, is_mainnet=is_mainnet)
    return res