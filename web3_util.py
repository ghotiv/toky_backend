from web3 import Web3

try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except Exception as e:
    from web3.middleware import geth_poa_middleware

from eth_abi import decode
from eth_utils import to_checksum_address, decode_hex, keccak, is_address, to_bytes

from my_conf import client_private_key,deployer_private_key,deployer,vault,client

def get_bytes32_address(address):
    #暂时支持evm
    #有没'0x'都支持
    res = to_bytes(hexstr=address).rjust(32, b'\0')
    return res

def get_method_id(func_sign):
    return '0x'+keccak(text=func_sign).hex()[:8]

#just test
def get_chain(chain_id):
    res_dicts = [
        #sepolia
        {
            'rpc_url': 'https://ethereum-sepolia-rpc.publicnode.com',
            'chain_id': 11155111,
        },
        #base sepolia
        {
            'rpc_url': 'https://sepolia.base.org',
            'chain_id': 84532,
        },
        #zksync sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/zksync_era_sepolia',
            'chain_id': 300,
        },
    ]
    return next((item for item in res_dicts if item['chain_id'] == chain_id), None)

def get_w3(rpc_url='',chain_id=''):
    if chain_id:
        rpc_url = get_chain(chain_id).get('rpc_url','')
    if not rpc_url:
        return
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    # print(w3.isConnected())
    return w3

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

def call_deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message, deposit_address, w3, private_key):
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
    contract = w3.eth.contract(address=deposit_address, abi=deposit_abi)
    account = w3.eth.account.from_key(private_key)
    account_address = account.address
    
    # 构建交易，添加必要参数
    tx_params = {
        'from': account_address,
        'gas': 300000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(account_address),
    }
    
    # 如果inputToken是0x0000...（ETH），需要添加value
    if inputToken == '0x0000000000000000000000000000000000000000':
        tx_params['value'] = inputAmount
    
    try:
        tx = contract.functions.deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message).build_transaction(tx_params)
        # print(f"交易参数: {tx}")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"交易已发送，哈希: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"交易确认，状态: {receipt.status}")
        return receipt
        
    except Exception as e:
        print(f"交易失败: {e}")
        # 尝试调用查看可能的错误
        try:
            contract.functions.deposit(vault, recipient, inputToken, inputAmount, destinationChainId, message).call(tx_params)
        except Exception as call_error:
            print(f"Call 错误: {call_error}")
        raise

def call_fill_replay(vault, recipient, inputToken, inputAmount, destinationChainId, message, deposit_address, w3, private_key):
    pass