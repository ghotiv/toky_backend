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

def simulate_transaction(contract_function, tx_params, function_name="transaction"):
    """模拟交易执行，检查是否会成功"""
    try:
        print(f"🔍 模拟执行{function_name}...")
        call_result = contract_function.call(tx_params)
        print(f"模拟执行结果: {call_result}")
        print(f"✅ 模拟执行成功，可以发送交易")
        return True
    except Exception as call_error:
        print(f"❌ 模拟执行失败: {call_error}")
        return False

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
def get_chain(chain_id=None,alchemy_network=None,is_testnet=False):
    res_dicts = [
        #sepolia
        {
            'rpc_url': 'https://ethereum-sepolia-rpc.publicnode.com',
            'chain_id': 11155111,
            'contract_deposit': '0x5bD6e85cD235d4c01E04344897Fc97DBd9011155',
            'contract_fillRelay': '0x460a94c037CD5DFAFb043F0b9F24c1867957AA5c',
            'alchemy_network': 'ETH_SEPOLIA',
            'is_testnet': True,
        },
        #base sepolia
        {
            'rpc_url': 'https://sepolia.base.org',
            'chain_id': 84532,
            'contract_deposit': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'BASE_SEPOLIA',
            'is_testnet': True,
        },
        #zksync sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/zksync_era_sepolia',
            'chain_id': 300,
            'contract_deposit': '0x9AA8668E11B1e9670B4DC8e81add17751bA1a4Ea',
            'contract_fillRelay': '0xEE89DAD29eb36835336d8A5C212FD040336B0dCb',
            'alchemy_network': 'ZKSYNC_SEPOLIA',
            'is_testnet': True,
        },
    ]
    if is_testnet:
        res_dicts = [item for item in res_dicts if item['is_testnet'] == True]
    else:
        res_dicts = [item for item in res_dicts if item['is_testnet'] == False]
    if chain_id:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id), {})
    if alchemy_network:
        res = next((item for item in res_dicts if item['alchemy_network'] == alchemy_network), {})
    return res

def get_w3(rpc_url='',chain_id=''):
    if chain_id:
        rpc_url = get_chain(chain_id).get('rpc_url','')
    if not rpc_url:
        return
    w3 = Web3(Web3.HTTPProvider(rpc_url))
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
                    contract_address, block_chainid, private_key=None):
    res = None
    w3 = get_w3(chain_id=block_chainid)
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
    contract = w3.eth.contract(address=contract_address, abi=deposit_abi)
    account = w3.eth.account.from_key(private_key)
    account_address = account.address
    
    tx_params = {
        'from': account_address,
        'gas': 300000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(account_address),
    }
    
    if inputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = inputAmount
    
    deposit_func = contract.functions.deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message)
    if not simulate_transaction(deposit_func, tx_params, "deposit"):
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
                        contract_address, block_chainid, private_key, check_before_send=True):
    res = None
    w3 = get_w3(chain_id=block_chainid)
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
        'nonce': w3.eth.get_transaction_count(account_address),
    }
    if outputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = outputAmount
    
    fillrelay_func = contract.functions.fillRelay(recipient, outputToken, outputAmount, originChainId, depositHash, message)
    if not simulate_transaction(fillrelay_func, tx_params, "fillRelay"):
        return None
    
    try:
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

#to do  contract_address map
def call_fill_relay_by_alchemy(data):
    '''
        calldata_dict = {'vault': '0xbA37D7ed1cFF3dDab5f23ee99525291dcA00999D', 
            'recipient': '0xd45F62ae86E01Da43a162AA3Cd320Fca3C1B178d', 
            'inputToken': '0x0000000000000000000000000000000000000000', 
            'inputAmount': 100000000000000, 
            'destinationChainId': 84532, 'message': b'hello'}
    '''
    res = None

    transaction_dict = data['event']['data']['block']['logs'][0]['transaction']
    alchemy_network = data['event']['network']
    calldata_dict = get_decode_calldata(transaction_dict['inputData'])
    block_chainid = calldata_dict['destinationChainId']
    outputToken = calldata_dict['inputToken']
    outputAmount = int(calldata_dict['inputAmount']*fill_rate)
    originChainId = get_chain(alchemy_network=alchemy_network,is_testnet=True)['chain_id']
    message = b''
    recipient = to_checksum_address(calldata_dict['recipient'])
    contract_address = to_checksum_address(get_chain(chain_id=block_chainid,is_testnet=True)['contract_fillRelay'])
    depositHash = get_bytes32_address(transaction_dict['hash'])
    res =call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        contract_address, block_chainid, private_key=vault_private_key)
    return res