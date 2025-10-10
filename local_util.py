import json

from eth_utils.units import units
from eth_utils import to_checksum_address, keccak, decode_hex, \
    is_address, to_bytes
from eth_abi import decode
from web3 import Web3
import arrow

from pg_util import Postgresql
from redis_util import Redis

from my_conf import DB_HOST,DB_DB,DB_USER,DB_PWD,TZ

DECIMALS_WEI_DICT = {len(str(v))-1:k for k,v in units.items()}
# support decimals
# 0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60
# 18 -- ether

redis_obj = Redis()

def get_pg_obj(host=DB_HOST,db=DB_DB,user=DB_USER,pwd=DB_PWD):
    if not host:
        return None
    pg_obj = Postgresql(host,db,user,pwd)
    return pg_obj

pg_obj = get_pg_obj()

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
        return None

def str_to_int(num):
    '''
        '0xf3c9e' -> 998558
        998558 -> 998558
    '''
    num = str(num)
    res = None
    if num.startswith('0x'):
        res = int(num, 16)
    elif num.isdigit():
        res = int(num)
    return res

def get_time_now(str_format=False):
    time_now = arrow.utcnow().to(TZ)
    if str_format:
        time_now = time_now.format('YYYY-MM-DD HH:mm:ss')
    return time_now

def format_time(time_at):
    return arrow.get(time_at).to(TZ).format('YYYY-MM-DD HH:mm:ss')

def get_tx_url(block_explorer,tx_hash,explorer_template='{domain}/tx/{hash}'):
    tx_url = explorer_template.format(domain=block_explorer, hash=tx_hash)
    return tx_url

def get_address_url(block_explorer,address,explorer_template='{domain}/address/{address}'):
    address_url = explorer_template.format(domain=block_explorer, address=address)
    return address_url

def set_tmp_key(k,v,ex=None):
    return redis_obj.set(k,v,ex)

def get_tmp_key(k):
    return redis_obj.get(k)

def get_web3_wei_amount(human_amount,decimals):
    '''
        return int
    '''
    res = Web3.to_wei(human_amount,DECIMALS_WEI_DICT[decimals])
    return res

def get_web3_human_amount(human_amount,decimals):
    '''
        return decimal
    '''
    res = Web3.from_wei(human_amount, DECIMALS_WEI_DICT[decimals])
    return res

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

def get_decode_calldata(calldata):
    res = {}
    method_id_transfer_deposit = get_method_id("deposit(address,bytes32,address,uint256,uint256,bytes)")
    method_id_fill_relay = get_method_id("fillRelay(address,address,uint256,uint256,bytes32,bytes)")
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
            'message':message,
            'contract_type':'contract_deposit',
            'calldata':calldata,
        }
    if method_id == method_id_fill_relay:
        function_abi = [
            {"type": "address", "name": "recipient"},
            {"type": "address", "name": "outputToken"},
            {"type": "uint256", "name": "outputAmount"},
            {"type": "uint256", "name": "originChainId"},
            {"type": "bytes32", "name": "depositHash"},
            {"type": "bytes", "name": "message"},
        ]
        abi_types = [item["type"] for item in function_abi]
        decoded_data = decode(abi_types, decode_hex(encoded_data))
        recipient,outputToken,outputAmount,originChainId,depositHash,message = decoded_data
        res = {
            'recipient':to_checksum_address(recipient),
            'outputToken':to_checksum_address(outputToken),
            'outputAmount':outputAmount,
            'originChainId':originChainId,
            'depositHash':depositHash.hex(),
            'message':message,
            'contract_type':'contract_fillrelay',
            'calldata':calldata,
        }
    return res

def get_w3(rpc_url='',chain_id=''):
    if chain_id:
        sql = f'select rpc_url from chain where chain_id = {chain_id}'
        res_pg = pg_obj.query(sql)
        if res_pg:
            rpc_url = res_pg[0]['rpc_url']
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