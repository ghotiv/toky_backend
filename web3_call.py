
import time
from decimal import Decimal

from eth_utils import to_checksum_address
from web3 import Web3

from local_util import get_tmp_key,set_tmp_key,\
    get_bytes32_address,get_decode_calldata,\
    str_to_int,get_w3,get_web3_wei_amount,get_web3_human_amount

from web3_util import decode_contract_error,get_gas_params,\
        handle_already_known_transaction,get_erc_allowance

from data_util import get_chain,get_token,create_txl_webhook,\
    create_fill_txl_etherscan_by_hash,get_etherscan_txs,\
    create_txl_etherscan_txlist

from my_conf import DEPOSIT_ABI,FILL_RELAY_ABI,CHECK_RELAY_FILLED_ABI,VAULTS,FILL_RATE,\
    VAULT_PRIVATE_KEY

def call_erc_allowance(chain_id, token_address, spender_address, 
            owner_address, human=False):
    w3 = get_w3(chain_id=chain_id)
    token_dict = get_token(chain_id=chain_id, token_address=to_checksum_address(token_address))
    if token_dict is None:
        return None
    decimals = int(token_dict['decimals'])
    allowance = get_erc_allowance(w3, to_checksum_address(token_address), 
            to_checksum_address(spender_address), to_checksum_address(owner_address), 
            human=human, decimals=decimals)
    print(allowance)
    return allowance

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
        elif 'out of gas' in error_msg or 'gas required exceeds' in error_msg:
            # 提取需要的 gas 数量并增加缓冲
            import re
            gas_match = re.search(r'gas required exceeds: (\d+)', error_msg)
            if gas_match:
                required_gas = int(gas_match.group(1))
                estimated_gas = int(required_gas * 2.0)  # 增加100%缓冲
                print(f"🔧 检测到gas不足，尝试增加gas limit...")
                print(f"📊 调整gas limit: {required_gas:,} -> {estimated_gas:,}")
            else:
                estimated_gas = 200000  # 为deposit设置一个更保守的默认值
                print(f"📊 Gas不足但无法解析具体数值，使用保守估算: {estimated_gas:,}")
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
        print(f"交易参数: {tx_params}")
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
    print(f"chain_dict: {chain_dict}")
    contract_address = chain_dict['contract_fillrelay']

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
    tx_hash = depositHash.hex()
    if get_tmp_key(f"depositHash_{tx_hash}"):
        print(f"❌ depositHash已经存在: {tx_hash}")
        return False
    #2minutes
    set_tmp_key(f"depositHash_{tx_hash}",'1',ex=60*2)
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

    log_dict = data['event']['data']['block']['logs'][0]
    tx_dict = log_dict['transaction']
    calldata = tx_dict['inputData']
    calldata_dict = get_decode_calldata(calldata)

    alchemy_network = data['event']['network']
    print(f"alchemy_network: {alchemy_network}")
    chain_dict = get_chain(alchemy_network=alchemy_network)
    # dst_chain_dict = get_chain(chain_id=calldata_dict['destinationChainId'])

    originChainId = chain_dict['chain_id']
    depositHash = get_bytes32_address(tx_dict['hash'])

    token_dict = get_token(chain_id=originChainId,token_address=calldata_dict['inputToken'])
    # print(f"token_dict: {token_dict}")

    tx_dict.update({
        'contract_addr_call': to_checksum_address(log_dict['account']['address']),
        'timestamp': data['event']['data']['block']['timestamp'],
    })
    calldata_dict.update({
        'chain_db_id': chain_dict['chain_db_id'],
        'token_id': token_dict['token_db_id'],
        'token_symbol': token_dict['token_symbol'],
        # 'dst_chain_db_id': dst_chain_dict['chain_db_id'],
    })
    # print(f"tx_dict: {tx_dict}")
    # print(f"calldata_dict: {calldata_dict}")

    res_create_txl_webhook = create_txl_webhook(tx_dict,calldata_dict)
    print(f"res_create_txl_webhook: {res_create_txl_webhook}")

    res = call_fill_relay_by_calldata(calldata_dict,originChainId,depositHash)
    return res

def call_fill_relay_by_etherscan(chain_id='',limit=1, contract_type='contract_deposit'):
    tx_dicts = get_etherscan_txs(chain_id=chain_id,limit=limit,contract_type=contract_type)
    for tx_dict in tx_dicts:
        print(f"tx_dict: {tx_dict}")
        if str_to_int(tx_dict['txreceipt_status']) == 1:
            calldata = tx_dict['input']
            depositHash = get_bytes32_address(tx_dict['hash'])
            calldata_dict = get_decode_calldata(calldata)
            if calldata_dict.get('contract_type',''):

                res_create = create_txl_etherscan_txlist(chain_id=chain_id,tx_dict=tx_dict)
                print(f"create_txl_etherscan_txlist: {res_create}")

                res = call_fill_relay_by_calldata(calldata_dict,chain_id,depositHash)
                print(f"res: {res}")
            else:
                print(f"❌ contract_type不存在: {tx_dict['hash']}")

#todo FILL_RATE 来自across
def call_fill_relay_by_calldata(calldata_dict,originChainId,depositHash):
    res = None
    block_chainid = calldata_dict['destinationChainId']
    vault = to_checksum_address(calldata_dict['vault'])

    token_input_dict = get_token(chain_id=originChainId,token_address=calldata_dict['inputToken'])
    # token_symbol_input = token_input_dict['token_symbol']
    token_group_input = token_input_dict['token_group']

    outputToken = get_token(chain_id=block_chainid,token_group=token_group_input).get('token_address',None)

    input_amount_human = get_web3_human_amount(calldata_dict['inputAmount'],int(token_input_dict['decimals']))
    print(f"input_amount_human: {input_amount_human}, decimals: {int(token_input_dict['decimals'])}")
    outputAmount = get_web3_wei_amount(input_amount_human*Decimal(str(FILL_RATE)),int(outputToken['decimals']))
    print(f"outputAmount: {outputAmount}, decimals: {int(outputToken['decimals'])}")

    message = b''
    recipient = to_checksum_address(calldata_dict['recipient'])

    if not check_fill_args(vault,depositHash,originChainId,block_chainid,outputToken):
        print(f"check_fill_args 不通过")
        return res

    res = call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                            block_chainid, private_key=VAULT_PRIVATE_KEY)

    # try:
    #     res = call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
    #                             block_chainid, private_key=VAULT_PRIVATE_KEY)
    # except Exception as e:
    #     print(f"❌ call_fill_relay_by_alchemy失败: {e}")

    if res:
        print(f"time: {time.time()}, create_fill_txl_etherscan: {res}")
        create_fill_txl_etherscan_by_hash(tx_hash=res,chain_id=block_chainid)
    return res