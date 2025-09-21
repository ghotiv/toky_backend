import json

from util import func_left_join

from data_util import pg_obj,read_json_file

# token_infos = read_json_file('chain_token.json')
token_infos = read_json_file('chain_token_testnet.json')

token_infos_gas = [i for i in token_infos if i['token_address'] == '0x0000000000000000000000000000000000000000']
for i in token_infos_gas:
    rpc_url = i.get('rpc_url','') or i['official_rpc']
    insert_dict = {
        'chain_name':i['chain_name'],
        'alias_name':i['alias_name'],
        # 'is_mainnet':1,
        'is_mainnet':0,
        'rpc_url':rpc_url,
        'rpc_url_bak':i.get('official_rpc',''),
        'chain_id':i['chain_id'],
        'block_explorer':i['explorer_url'],
        'chain_logo_url': i['icon'],
        'contract_deposit': i['contract_deposit'],
        'contract_fillRelay': i['contract_fillRelay'],
        'alchemy_network': i['alchemy_network'],
        'chain_note': '',
    }
    print(i['chain_name'],rpc_url)
    pg_obj.insert('chain',insert_dict)

sql_chain = '''
    select id as chain_db_id,chain_name from chain
'''
res_chain = pg_obj.query(sql_chain)
# print(res_chain)

res_join = func_left_join(token_infos,res_chain,['chain_name'])
print(res_join[0])

for i in res_join:
    is_native_token = 1 if i['token_address'] == '0x0000000000000000000000000000000000000000' else 0
    insert_dict = {
        'chain_db_id':i['chain_db_id'],
        'is_native_token':is_native_token,
        'token_symbol':i['token_name'],
        'token_name':i['token_name'],
        'token_group':'',
        'token_note':'',
        'token_address':i['token_address'],
        'decimals':i['decimals'], 
        # 'min_num':'', 
        # 'max_num':'',
        'token_logo_url':i['token_logo_url']
    }
    pg_obj.insert('token',insert_dict)
