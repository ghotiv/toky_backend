import json
import re
import arrow
import random
import requests

from eth_utils import to_checksum_address,add_0x_prefix

from util import func_left_join,to_tztime
from pg_util import Postgresql
from redis_util import Redis

from web3_util import get_decode_calldata

from my_conf import *

redis_obj = Redis()

def get_pg_obj(host=DB_HOST,db=DB_DB,user=DB_USER,pwd=DB_PWD):
    if not host:
        return None
    pg_obj = Postgresql(host,db,user,pwd)
    return pg_obj

pg_obj = get_pg_obj()

#not used
def decorator_res(func):
    def wrapper(*args, **kwargs):
        try:
            res_func = func(*args, **kwargs)
            return {'data':res_func}
        except Exception as e:
            print(str(e))
            #to do message 给用户看
            return {'errorCode':500,'message':str(e)}
    return wrapper

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

def get_human_amount(num,decimals=18):
    return num/10**decimals

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

def get_etherscan_apikey():
    return random.choice(ETHERSCAN_API_KEYS)

def get_chain(chain_id=None,alchemy_network=None):
    res = None
    sql = ''
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
        res = chain_dicts[0]
    return res

def get_chains(chain_ids=None):
    res = None
    sql = 'select * from chain'
    if chain_ids:
        sql = f'select * from chain where id in ({','.join(map(str,chain_ids))})'
    chain_dicts = pg_obj.query(sql)
    chain_dicts = [i for i in chain_dicts if i['is_active']]
    [i.update({'chain_db_id': i['id']}) for i in chain_dicts]
    [i.update({'is_eip1559': i['chain_id'] not in NOT_EIP1599_IDS}) for i in chain_dicts]
    [i.update({'is_l2': i['chain_id'] not in L1_CHAIN_IDS}) for i in chain_dicts]
    res = chain_dicts
    return res

def get_token(chain_id=None,token_symbol=None,token_address=None,token_group=None):
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
    if token_group:
        sql = f"select * from token where token_group = '{token_group}' and chain_db_id = {chain_db_id}"
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

def get_tokens(token_symbol=None,token_address=None,token_group=None):
    res = {}
    sql = 'select * from token'
    if token_symbol:
        token_symbol = token_symbol.upper()
        sql = f"select * from token where token_symbol = '{token_symbol}'"
    if token_address:
        token_address = to_checksum_address(token_address)
        sql = f"select * from token where token_address = '{token_address}'"
    if token_group:
        sql = f"select * from token where token_group = '{token_group}'"
    # if not sql:
    #     return res
    token_dicts = pg_obj.query(sql)
    token_dicts = [i for i in token_dicts if i['is_active']]
    [i.update({'token_db_id': i['id']}) for i in token_dicts]
    res = token_dicts
    return res

def get_tokens_with_chains(token_symbol=None,token_address=None,token_group=None):
    res_tokens = get_tokens(token_symbol=token_symbol,token_address=token_address,token_group=token_group)
    res_chains = get_chains()
    res = func_left_join(res_tokens,res_chains,['chain_db_id'])
    return res

def get_vault_address():
    return VAULT

def get_token_set():
    res_pg = pg_obj.query('select distinct token_group from token')
    res = [i['token_group'] for i in res_pg]
    return res

def get_chains_by_token_group(token_group):
    res_tokens = get_tokens(token_group=token_group)
    chain_db_ids = [i['chain_db_id'] for i in res_tokens]
    res = get_chains(chain_ids=chain_db_ids)
    return res

def get_txl(tx_hash):
    sql = f"select * from txline where tx_hash = '{tx_hash}'"
    res = pg_obj.query(sql)
    return res[0] if res else {}

def get_txls(addr):
    sql_from = f"select * from txline where addr_from = '{addr}'"
    res_from = pg_obj.query(sql_from)
    sql_to = f"select * from txline where addr_to = '{addr}'"
    res_to = pg_obj.query(sql_to)
    res = res_from + res_to
    return res

def get_txls_pair(addr='',status=None, limit=50, offset=0):
    res = []
    sql_from = f'''
        select txline.id as txl_related_id,num as num_from,chain.chain_id as chain_id_from,
               token_id as token_db_id,addr_from,tx_hash as tx_hash_from,tx_time,status,
                chain.alias_name as chain_alias_name_from,chain.block_explorer as block_explorer_from,
                chain.explorer_template as explorer_template_from,chain.chain_logo_url as chain_logo_url_from,
                token.decimals as decimals_from,
                token.token_group
        from txline
            left join chain on txline.chain_db_id = chain.id
            left join token on txline.token_id = token.id
        where addr_from= '{addr}'
        {f'and status = {status}' if status!=None else ''}
        order by txline.id DESC
        limit {limit} OFFSET {offset}
    '''
    # print(f"sql_from: {sql_from}")
    res_from = pg_obj.query(sql_from)
    if not res_from:
        return res
    [i.update({
        'num_human_from': get_human_amount(i['num_from'],decimals=i['decimals_from']),
        'tx_url_from': get_tx_url(i["block_explorer_from"],i["tx_hash_from"],explorer_template=i["explorer_template_from"])
        }) 
        for i in res_from if i['num_from']]
    txl_related_ids = [i['txl_related_id'] for i in res_from]
    sql_to = f'''
        select txl_related_id,num as num_to,chain.chain_id as chain_id_to,
               token_id as token_db_id,addr_to,tx_hash as tx_hash_to,
                chain.alias_name as chain_alias_name_to,chain.block_explorer as block_explorer_to,
                chain.explorer_template as explorer_template_to,
                chain.chain_logo_url as chain_logo_url_to,
                token.decimals as decimals_to
        from txline
            left join chain on txline.chain_db_id = chain.id
            left join token on txline.token_id = token.id
        where 
            addr_to= '{addr}' 
            and txl_related_id in ({','.join(map(str,txl_related_ids))})
    '''
    res_to = pg_obj.query(sql_to)
    [i.update({
        'num_human_to': get_human_amount(i['num_to'],decimals=i['decimals_to']),
        'tx_url_to': get_tx_url(i["block_explorer_to"],i["tx_hash_to"],explorer_template=i["explorer_template_to"])
        }) 
        for i in res_to if i['num_to']]
    res = func_left_join(res_from,res_to,['txl_related_id'])
    res_sorted = sorted(res,key=lambda x: x['tx_time'],reverse=True)
    return res_sorted


#for api
def api_get_token_groups():
    res = [
        {
            'token_group': 'ETH',
            'token_logo_url': 'https://owlto.finance/icon/token/ETH.png',
        },
        {
            'token_group': 'MBT',
            'token_logo_url': 'https://owlto.finance/icon/token/USDT.png',
        },
    ]
    return res

def api_get_chains_by_token_group(token_group):
    res = []
    res_chains = get_chains_by_token_group(token_group)
    if res_chains:
        res = [{
            'chain_id': i['chain_id'],
            'contract_deposit': i['contract_deposit'],
            # 'contract_fillrelay': i['contract_fillrelay'],
            'alias_name': i['alias_name'],
            'rpc_url': i['rpc_url'],
            'chain_logo_url': i['chain_logo_url'],
        } for i in res_chains]
    return res

def api_get_txls(addr):
    res = get_txls(addr)
    return res

def get_etherscan_txs(chain_id='',limit=2,contract_type='contract_deposit'):
    res = []
    api_key = get_etherscan_apikey()
    address = ''
    if contract_type == 'contract_deposit':
        address = to_checksum_address(get_chain(chain_id=chain_id).get('contract_deposit',''))
    if contract_type == 'contract_fillrelay':
        address = to_checksum_address(get_chain(chain_id=chain_id).get('contract_fillrelay',''))
    if address:
        url = f'https://api.etherscan.io/v2/api?chainid={chain_id}&module=account&action=txlist&address={address}&page=1&offset={limit}&sort=desc&apikey={api_key}'
        response = requests.get(url)
        res = response.json()['result']
    return res

def get_etherscan_tx_by_hash(chain_id='',tx_hash=''):
    api_key = get_etherscan_apikey()
    url = f'https://api.etherscan.io/v2/api?chainid={chain_id}&module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={api_key}'
    print(f"get_etherscan_tx_by_hash url: {url}")
    response = requests.get(url)
    res = response.json()['result']
    return res
    
#eth_getTransactionReceipt    
def get_etherscan_tx_receipt(chain_id='',tx_hash=''):
    api_key = get_etherscan_apikey()
    url = f'https://api.etherscan.io/v2/api?chainid={chain_id}&module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}&apikey={api_key}'
    print(f"get_etherscan_tx_receipt url: {url}")
    response = requests.get(url)
    res = response.json()['result']
    return res

def create_txl_webhook(tx_dict,calldata_dict):

    # print(f"tx_dict: {tx_dict}")

    gas_price = str_to_int(tx_dict['effectiveGasPrice'])
    gas_used = tx_dict['gasUsed']
    tx_fee = gas_price*gas_used
    txl_dict = {
        'tx_hash': add_0x_prefix(tx_dict['hash']),
        'status': 0,
        'contract_addr_call': tx_dict['contract_addr_call'],
        # 'txl_related_id': '',
        'tx_status': tx_dict['status'],
        # 'is_refund': '',
        # 'create_time': '',
        # 'update_time': '',
        'tx_time': to_tztime(tx_dict['timestamp']),
        'addr_from': to_checksum_address(tx_dict['from']['address']),
        'addr_to': to_checksum_address(calldata_dict['vault']),
        'recipient': to_checksum_address(calldata_dict['recipient']),
        'chain_db_id': calldata_dict['chain_db_id'],
        # 'dst_chain_db_id': calldata_dict['dst_chain_db_id'],
        'token_id': calldata_dict['token_id'],
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
        'calldata': calldata_dict['calldata'],
        'note': ''
    }
    if tx_dict.get('type',None):
        txl_dict.update({
            'eip_type': str_to_int(tx_dict['type']),
        })
    res = pg_obj.insert('txline',txl_dict)
    return res

def create_fill_txl_etherscan_by_hash(tx_hash,chain_id):
    tx_dict = get_etherscan_tx_by_hash(chain_id=chain_id,tx_hash=tx_hash)
    print('create_fill_txl_etherscan_by_hash tx_dict : ',tx_dict)
    calldata_dict = get_decode_calldata(tx_dict['input'])

    chain_dict = get_chain(chain_id=chain_id)
    chain_db_id = chain_dict['chain_db_id']
    token_dict = get_token(chain_id=chain_id,token_address=calldata_dict['outputToken'])
    token_id = token_dict['token_db_id']
    depositHash = add_0x_prefix(calldata_dict['depositHash'])
    txl_related_dict = get_txl(tx_hash=depositHash)
    txl_related_id = txl_related_dict['id']

    txl_dict = {
        'tx_hash': add_0x_prefix(tx_dict['hash']),
        # 'status': '',#todo
        'contract_addr_call': to_checksum_address(tx_dict['to']),
        'txl_related_id': txl_related_id,
        # 'tx_status': '', #todo
        # 'is_refund': '',
        # 'create_time': '',
        # 'update_time': '',
        # 'tx_time': '', #todo
        'addr_from': to_checksum_address(tx_dict['from']),
        'addr_to': to_checksum_address(calldata_dict['recipient']),
        'recipient': to_checksum_address(calldata_dict['recipient']),
        'chain_db_id': chain_db_id,
        # 'dst_chain_db_id': '',
        'token_id': token_id,
        'num': calldata_dict['outputAmount'],
        # 'tx_fee': '', #todo
        'nonce': str_to_int(tx_dict['nonce']),
        # 'gas_used': '', #todo
        # 'gas_price': '', #todo
        'estimate_gas_limit': str_to_int(tx_dict['gas']),
        # 'estimate_gas_price': '',
        'eip_type': str_to_int(tx_dict['type']),
        'max_fee_per_gas': str_to_int(tx_dict['maxFeePerGas']),
        'max_priority_fee_per_gas': str_to_int(tx_dict['maxPriorityFeePerGas']),
        'calldata': calldata_dict['calldata'],
        'note': ''
    }

    tx_receipt_dict = get_etherscan_tx_receipt(chain_id=chain_id,tx_hash=tx_hash)
    if str_to_int(tx_receipt_dict['status']) == 1:
        gas_used = str_to_int(tx_receipt_dict['gasUsed'])
        gas_price = str_to_int(tx_receipt_dict['effectiveGasPrice'])
        tx_fee = gas_used*gas_price
        tx_fee += str_to_int(tx_receipt_dict.get('l1Fee',0))
        print('tx_receipt_dict logs[0] : ',tx_receipt_dict['logs'][0])
        txl_dict.update({
            'status': 1,
            'tx_status': 1,
            # 'tx_time': to_tztime(time_stamp),
            'tx_fee': tx_fee,
            'gas_used': gas_used,
            'gas_price': gas_price,
        })
        blockTimestamp = tx_receipt_dict.get('blockTimestamp','')
        if blockTimestamp:
            txl_dict.update({
                'tx_time': to_tztime(str_to_int(blockTimestamp)),
            })
        #更新from单状态
        update_sql = f'''
            UPDATE txline
            SET status = 1
            WHERE id IN (
                SELECT id FROM txline WHERE id = {txl_related_id} ORDER BY id LIMIT 1
            );
        '''
        pg_obj.execute(update_sql)

    res = pg_obj.insert('txline',txl_dict)
    return res

def create_txl_etherscan_txlist(chain_id,tx_dict):
    tx_hash = add_0x_prefix(tx_dict['hash'])
    tx_status = str_to_int(tx_dict['txreceipt_status'])
    txl_dict_search = get_txl(tx_hash=tx_hash)

    res_create = None

    if not txl_dict_search:
        calldata_dict = get_decode_calldata(tx_dict['input'])
        contract_type = calldata_dict['contract_type']
        gas_used = str_to_int(tx_dict['gasUsed'])
        gas_price = str_to_int(tx_dict['gasPrice'])
        tx_fee = gas_used*gas_price
        tx_fee += str_to_int(tx_dict.get('L1FeesPaid',0))
        txl_dict = {
            'tx_hash': tx_hash,
            # 'status': 0,  #todo
            'contract_addr_call': to_checksum_address(tx_dict['to']),
            # 'txl_related_id': '',
            'tx_status': tx_status,
            # 'is_refund': '',
            # 'create_time': '',
            # 'update_time': '',
            'tx_time': to_tztime(tx_dict['timeStamp']),
            'addr_from': to_checksum_address(tx_dict['from']),
            # 'addr_to': '',     #todo
            # 'recipient': '',   #todo
            # 'chain_db_id': '',  #todo
            # 'dst_chain_db_id': '',  #todo
            # 'token_id': '',  #todo
            # 'num': '',  #todo
            'tx_fee': tx_fee,
            'nonce': str_to_int(tx_dict['nonce']),
            'gas_used': gas_used,
            'gas_price': gas_price,
            # 'estimate_gas_limit': '',  #todo
            # 'estimate_gas_price': '',
            # 'eip_type': '0x2',
            # 'max_fee_per_gas': '',  #todo
            # 'max_priority_fee_per_gas': '',  #todo
            'calldata': calldata_dict['calldata'],
            'note': ''
        }
        chain_dict = get_chain(chain_id=chain_id)
        if contract_type == 'contract_deposit':
            # dst_chain_dict = get_chain(chain_id=calldata_dict['destinationChainId'])
            token_dict = get_token(chain_id=chain_id,token_address=calldata_dict['inputToken'])
            txl_dict.update({
                'addr_to': to_checksum_address(calldata_dict['vault']),
                'recipient': to_checksum_address(calldata_dict['recipient']),
                'chain_db_id': chain_dict['chain_db_id'],
                # 'dst_chain_db_id': dst_chain_dict['chain_db_id'],
                'token_id': token_dict['token_db_id'],
                'num': calldata_dict['inputAmount'],
            })
        if contract_type == 'contract_fillrelay':
            token_dict = get_token(chain_id=chain_id,token_address=calldata_dict['outputToken'])
            txl_dict.update({
                'addr_to': to_checksum_address(calldata_dict['recipient']),
                'recipient': to_checksum_address(calldata_dict['recipient']),
                'chain_db_id': chain_dict['chain_db_id'],
                'token_id': token_dict['token_db_id'],
                'num': calldata_dict['outputAmount'],
            })
            depositHash = add_0x_prefix(calldata_dict['depositHash'])
            txl_related_dict = get_txl(tx_hash=depositHash)
            txl_related_id = txl_related_dict['id']
            update_sql = f'''
                UPDATE txline
                SET status = 1
                WHERE id IN (
                    SELECT id FROM txline WHERE id = {txl_related_id} ORDER BY id LIMIT 1
                );
            '''
            pg_obj.execute(update_sql)
        res_create = pg_obj.insert('txline',txl_dict)
        print(f"res_create: {res_create}")
    else:
        print(f"tx_hash: {tx_hash} 已存在")
    return res_create

def get_create_txls_etherscan_txlist(chain_id,limit=1,contract_type=''):
    print(f"get_create_txl_etherscan chain_id: {chain_id}, limit: {limit}, contract_type: {contract_type}")
    tx_dicts = get_etherscan_txs(chain_id=chain_id,limit=limit,contract_type=contract_type)
    for tx_dict in tx_dicts:
        tx_status = str_to_int(tx_dict['txreceipt_status'])
        if tx_status == 1:
            print(f"tx_dict: {tx_dict}")

            res_create = create_txl_etherscan_txlist(chain_id=chain_id,tx_dict=tx_dict)
            print(f"res_create: {res_create}")