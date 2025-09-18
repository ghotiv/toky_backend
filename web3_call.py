from data_util import get_chain,get_token,set_tmp_key,get_tmp_key
from web3 import Web3
from web3_util import get_method_id, decode_contract_error, get_recipient_vaild_address, \
    get_gas_params,handle_already_known_transaction, get_bytes32_address
from eth_abi import decode
from eth_utils import to_checksum_address, decode_hex
import time
import random
import requests
from my_conf import *

def get_etherscan_txs(chain_id='',limit=2,apikeys=ETHERSCAN_API_KEYS,contract_type='contract_deposit'):
    res = []
    apikey = random.choice(apikeys)
    address = ''
    if contract_type == 'contract_deposit':
        address = to_checksum_address(get_chain(chain_id=chain_id).get('contract_deposit',''))
    if contract_type == 'contract_fillRelay':
        address = to_checksum_address(get_chain(chain_id=chain_id).get('contract_fillRelay',''))
    if address:
        url = f'https://api.etherscan.io/v2/api?chainid={chain_id}&module=account&action=txlist&address={address}&page=1&offset={limit}&sort=desc&apikey={apikey}'
        response = requests.get(url)
        res = response.json()['result']
    return res

def get_w3(rpc_url='',chain_id=''):
    if chain_id:
        rpc_url = get_chain(chain_id=chain_id).get('rpc_url','')
    if not rpc_url:
        return
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # 自动检测并注入POA中间件（如果需要）
    from web3_util import auto_inject_poa_middleware_if_needed
    poa_result = auto_inject_poa_middleware_if_needed(w3)
    if poa_result and poa_result not in ["not_needed", "already_exists"]:
        print(f"🔗 Chain {chain_id} POA中间件状态: {poa_result}")
    
    # print(w3.isConnected())
    return w3

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
                    block_chainid, private_key=None):
    res = None
    w3 = get_w3(chain_id=block_chainid)
    chain_dict = get_chain(chain_id=block_chainid)
    is_eip1559 = chain_dict['is_eip1559']
    is_l2 = chain_dict['is_l2']
    print(f"w3: {w3}")
    contract_address = chain_dict['contract_deposit']
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)
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
        error_msg = str(e)
        
        # 检查是否是ERC20授权相关错误
        if 'SafeERC20' in error_msg or 'low-level call failed' in error_msg:
            print(f"❌ 检测到ERC20授权错误，无法继续执行deposit")
            return None
        elif 'insufficient funds' in error_msg or 'insufficient balance' in error_msg:
            print(f"❌ 检测到余额不足错误，无法继续执行deposit")
            return None
        else:
            # 其他错误，使用默认gas值尝试
            estimated_gas = 150000  # 为deposit设置一个保守的默认值
            print(f"📊 使用默认gas估算: {estimated_gas:,}")
    
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
    try:
        print(f"🔍 检查relay状态...")
        print(f"  - 合约地址: {contract_address}")
        print(f"  - originChainId: {originChainId}")
        print(f"  - depositHash: {depositHash.hex() if hasattr(depositHash, 'hex') else depositHash}")
        print(f"  - recipient: {recipient}")
        print(f"  - outputToken: {outputToken}")
        
        # 检查合约地址是否有效
        if not w3.is_address(contract_address):
            print(f"❌ 无效的合约地址: {contract_address}")
            return None
            
        # 检查地址是否有代码（是否为合约）
        code = w3.eth.get_code(contract_address)
        if code == b'':
            print(f"❌ 地址 {contract_address} 没有合约代码，可能未部署")
            return None
        
        print(f"✅ 合约地址有效，代码长度: {len(code)} bytes")
        
        contract = w3.eth.contract(address=contract_address, abi=CHECK_RELAY_FILLED_ABI)
        is_filled = contract.functions.isRelayFilled(originChainId, depositHash, recipient, outputToken).call()
        print(f"✅ relay状态检查成功: {is_filled}")
        return is_filled
    except Exception as e:
        print(f"❌ 检查relay状态失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


def call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        block_chainid, private_key):
    res = None
    w3 = get_w3(chain_id=block_chainid)
    chain_dict = get_chain(chain_id=block_chainid)
    is_eip1559 = chain_dict['is_eip1559']
    is_l2 = chain_dict['is_l2']
    contract_address = chain_dict['contract_fillRelay']

    print(f"call_fill_relay 入参 时间: {time.time()}: {recipient}, {outputToken}, {outputAmount}, {originChainId}, {depositHash.hex()}, {message}")

    relay_filled = check_relay_filled(originChainId, depositHash, recipient, outputToken, contract_address, w3)
    if relay_filled is True:
        print(f"❌ RelayAlreadyFilled: 这个relay已经被填充过了,{depositHash.hex()}")
        return None
            
    contract = w3.eth.contract(address=contract_address, abi=FILL_RELAY_ABI)
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
        error_msg = str(e)
        
        # 检查是否是ERC20授权相关错误
        if 'SafeERC20' in error_msg or 'low-level call failed' in error_msg:
            print(f"❌ 检测到ERC20授权错误，无法继续执行fillRelay")
            return None
        elif 'insufficient funds' in error_msg or 'insufficient balance' in error_msg:
            print(f"❌ 检测到余额不足错误，无法继续执行fillRelay")
            return None
        else:
            # 其他错误，使用默认gas值尝试
            estimated_gas = 200000  # 为fillRelay设置一个保守的默认值
            print(f"📊 使用默认gas估算: {estimated_gas:,}")
    
    # 使用实际估算的gas获取优化的gas参数（在这里统一设置nonce）
    tx_params = get_gas_params(w3, account_address, block_chainid, 
                             priority='standard', tx_type='contract_call', 
                             estimated_gas=estimated_gas, is_eip1559=is_eip1559, is_l2=is_l2)
    
    # 如果等待pending交易完成后需要重新检查relay状态
    if tx_params == "pending_completed_recheck_needed":
        print(f"🔍 Pending交易完成后重新检查relay状态...")
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
                    print("🔍 确认是真正的余额不足问题...")
                
                return None
        elif 'InsufficientBalance' in decoded_error:
            # 直接是InsufficientBalance错误，进行余额诊断
            print("🔍 检测到InsufficientBalance错误...")
            return None
        else:
            # 其他类型的错误
            return None

    # 发送交易前再次检查relay状态（防止pending交易已经填充了这个relay）
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

def check_fill_args(vault,depositHash,originChainId,block_chainid,outputToken):
    print(f"vault: {vault}")
    if vault not in VAULTS:
        print(f"❌  vault not in VAULTS: {vault}")
        return False
    if get_tmp_key(f"depositHash_{depositHash}"):
        print(f"❌ depositHash已经存在: {depositHash.hex()}")
        return False
    #2minutes
    set_tmp_key(f"depositHash_{depositHash}",'1',ex=60*2)
    if not outputToken:
        print(f"❌ outputToken代币不存在")
        return False
    origin_is_mainnet = get_chain(chain_id=originChainId).get('is_mainnet',None)
    if origin_is_mainnet is None:
        print(f"❌  originChain或者is_mainnet不存在: {originChainId}")
        return False
    block_is_mainnet = get_chain(chain_id=block_chainid).get('is_mainnet',None)
    if block_is_mainnet is None:
        print(f"❌  block_chainid或者is_mainnet不存在: {block_chainid}")
        return False
    if origin_is_mainnet != block_is_mainnet:
        print(f"❌ 主网和测试网不能互相调用")
        return False
    return True

def call_fill_relay_by_alchemy(data):
    '''
        calldata_dict = {'vault': '0xbA37D7ed1cFF3dDab5f23ee99525291dcA00999D', 
            'recipient': '0xd45F62ae86E01Da43a162AA3Cd320Fca3C1B178d', 
            'inputToken': '0x0000000000000000000000000000000000000000', 
            'inputAmount': 100000000000000, 
            'destinationChainId': 84532, 'message': b'hello'}
    '''
    res = None

    # print(f"data: {data}")

    tx_dict = data['event']['data']['block']['logs'][0]['transaction']
    alchemy_network = data['event']['network']
    originChainId = get_chain(alchemy_network=alchemy_network)['chain_id']
    depositHash = get_bytes32_address(tx_dict['hash'])
    calldata = tx_dict['inputData']
    res = call_fill_relay_by_calldata(calldata,originChainId,depositHash)
    return res

def call_fill_relay_by_etherscan(chain_id='',limit=1,contract_type='contract_deposit'):
    tx_dicts = get_etherscan_txs(chain_id=chain_id,limit=limit,contract_type=contract_type)
    for tx_dict in tx_dicts:
        calldata = tx_dict['input']
        depositHash = get_bytes32_address(tx_dict['hash'])
        res =call_fill_relay_by_calldata(calldata,chain_id,depositHash)
        print(f"res: {res}")

#todo FILL_RATE 来自across
def call_fill_relay_by_calldata(calldata,originChainId,depositHash):
    res = None
    calldata_dict = get_decode_calldata(calldata)
    block_chainid = calldata_dict['destinationChainId']
    vault = to_checksum_address(calldata_dict['vault'])
    token_name_input = get_token(chain_id=originChainId,token_address=calldata_dict['inputToken'])['token_name']
    outputToken = get_token(chain_id=block_chainid,token_name=token_name_input,).get('token_address',None)

    outputAmount = int(calldata_dict['inputAmount']*FILL_RATE)
    message = b''
    recipient = to_checksum_address(calldata_dict['recipient'])

    if not check_fill_args(vault,depositHash,originChainId,block_chainid,outputToken):
        print(f"check_fill_args 不通过")
        return res
    try:
        res = call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                                block_chainid, private_key=VAULT_PRIVATE_KEY)
    except Exception as e:
        print(f"❌ call_fill_relay_by_alchemy失败: {e}")
    return res