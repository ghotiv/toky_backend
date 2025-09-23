import json
import arrow
from eth_utils import to_checksum_address

from util import func_left_join,to_tztime
from pg_util import Postgresql
from redis_util import Redis

from my_conf import *

redis_obj = Redis()

def get_pg_obj(host=DB_HOST,db=DB_DB,user=DB_USER,pwd=DB_PWD):
    if not host:
        return None
    pg_obj = Postgresql(host,db,user,pwd)
    return pg_obj

pg_obj = get_pg_obj()

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

def set_tmp_key(k,v,ex=None):
    return redis_obj.set(k,v,ex)

def get_tmp_key(k):
    return redis_obj.get(k)

def get_time_now(str_format=False):
    time_now = arrow.utcnow().to(TZ)
    if str_format:
        time_now = time_now.format('YYYY-MM-DD HH:mm:ss')
    return time_now

def format_time(time_at):
    return arrow.get(time_at).to(TZ).format('YYYY-MM-DD HH:mm:ss')

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


def get_chain(chain_id=None,alchemy_network=None,all_chain=False):
    res = None
    sql = ''
    if all_chain:
        sql = 'select * from chain'
    if chain_id:
        sql = f'select * from chain where chain_id = {chain_id}'
    if alchemy_network:
        sql = f"select * from chain where alchemy_network = '{alchemy_network}'"
    if not sql:
        return res
    chain_dicts = pg_obj.query(sql)
    chain_dicts = [i for i in chain_dicts if i['is_active']]
    [i.update({'chain_db_id': i['id']}) for i in chain_dicts]
    [i.update({'is_eip1559': i['chain_id'] not in NOT_EIP1599_IDS}) for i in chain_dicts]
    [i.update({'is_l2': i['chain_id'] not in L1_CHAIN_IDS}) for i in chain_dicts]
    if chain_dicts:
        if all_chain:
            res = chain_dicts
        else:
            res = chain_dicts[0]
    return res


def get_token(chain_id=None,token_symbol=None,token_address=None):
    res = {}
    if not chain_id:
        return res
    chain_dict = get_chain(chain_id=chain_id)
    chain_db_id = chain_dict['chain_db_id']
    if token_symbol:
        token_symbol = token_symbol.upper()
    if token_address:
        token_address = to_checksum_address(token_address)
    sql = ''
    if token_symbol:
        sql = f"select * from token where token_symbol = '{token_symbol}' and chain_db_id = {chain_db_id}"
    if token_address:
        sql = f"select * from token where token_address = '{token_address}' and chain_db_id = {chain_db_id}"
    if not sql:
        return res
    token_dicts = pg_obj.query(sql)
    token_dicts = [i for i in token_dicts if i['is_active']]
    [i.update({'token_db_id': i['id']}) for i in token_dicts]
    if token_dicts:
        res_dicts = func_left_join(token_dicts,[chain_dict],['chain_db_id'])
        if res_dicts:
            res = res_dicts[0]
    return res

def create_txl_webhook(tx_dict,calldata_dict):
    gas_price = str_to_int(tx_dict['effectiveGasPrice'])
    gas_used = tx_dict['gasUsed']
    tx_fee = gas_price*gas_used
    txl_dict = {
        'tx_hash': tx_dict['hash'],
        'status': tx_dict['status'],
        'contract_addr_call': tx_dict['contract_addr_call'],
        # 'txl_related_id': '',
        'tx_status': tx_dict['status'],
        # 'is_refund': '',
        # 'create_time': '',
        # 'update_time': '',
        'tx_time': to_tztime(tx_dict['timestamp']),
        'addr_from': tx_dict['from']['address'],
        'addr_to': calldata_dict['vault'],
        'recipient': calldata_dict['recipient'],
        'chain_db_id': calldata_dict['chain_dict']['chain_db_id'],
        'token_id': calldata_dict['token_dict']['token_db_id'],
        'num': calldata_dict['inputAmount'],
        'tx_fee': tx_fee,
        'nonce': tx_dict['nonce'],
        'gas_used': gas_used,
        'gas_price': gas_price,
        'estimate_gas_limit': tx_dict['gas'],
        # 'estimate_gas_price': '',
        # 'eip_type': '0x2',
        'max_fee_per_gas': str_to_int(tx_dict['maxFeePerGas']),
        'max_priority_fee_per_gas': str_to_int(tx_dict['maxPriorityFeePerGas']),
        'note': ''
    }
    res = pg_obj.insert('txline',txl_dict)
    return res
