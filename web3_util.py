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

    is_mainnet = True
    if DEBUG_MODE:
        is_mainnet = False

    w3 = get_w3(chain_id=block_chainid,is_mainnet=is_mainnet)
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
    
    tx_params = {
        'from': account_address,
        'gas': 300000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': get_safe_nonce(w3, account_address),
    }
    
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
    contract_address = get_chain(chain_id=block_chainid,is_mainnet=is_mainnet)['contract_fillRelay']

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
    tx_params = {
        'from': account_address,
        'gas': 300000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': get_safe_nonce(w3, account_address),
    }
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