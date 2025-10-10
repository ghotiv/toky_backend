import concurrent.futures

from local_util import pg_obj,get_address_url
from foundry_util import deploy_contract, verify_contract, deploy_add_vault_author,\
        approve_token,transfer_eth,transfer_erc
from data_util import get_chain,get_chains,get_tokens_with_chains
from my_conf import CLIENT_PRIVATE_KEY,VAULT_PRIVATE_KEY,CLIENT,DEPLOYER_PRIVATE_KEY,VAULT

def deploy_contract_one(chain_dict,contract_type):
    is_eip1559 = chain_dict['is_eip1559']
    deploy_address = deploy_contract(rpc_url=chain_dict['rpc_url'], 
                        contract_type=contract_type, is_eip1559=is_eip1559)
    print(chain_dict['chain_name'],'deposit contract address:',deploy_address)

    contract_field = ''
    if contract_type == 'deposit':
        contract_field = 'contract_deposit'
    if contract_type == 'fill_relay':
        contract_field = 'contract_fillrelay'

    if deploy_address and contract_field:
        sql = f'''
            update chain
            set 
            {contract_field} = '{deploy_address}',
            update_time = now()
            where chain_id = {chain_dict['chain_id']}
        '''
        print(sql)
        res = pg_obj.execute(sql)
        print(chain_dict['chain_name'],'update contract_deposit:',res)

# chain_dict = get_chain(chain_id=300)
# deploy_contract_one(chain_dict, 'deposit')
# deploy_contract_one(chain_dict, 'fill_relay')

def deploy_deposits(contract_type,is_mainnet=False):
    chain_dicts = get_chains(is_mainnet=is_mainnet)
    for chain_dict in chain_dicts:
        deploy_contract_one(chain_dict, contract_type)

# deploy_deposits('deposit')
# deploy_deposits('fill_relay')

def deploy_deposits_concurrent(contract_type,is_mainnet=False):
    chain_dicts = get_chains(is_mainnet=is_mainnet)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(lambda chain_dict: deploy_contract_one(chain_dict, contract_type), chain_dicts)

# deploy_deposits_concurrent('deposit')
# deploy_deposits_concurrent('fill_relay')

def verify_contract_one(chain_dict,contract_type):
    if contract_type == 'deposit':
        contract_address = chain_dict['contract_deposit']
    if contract_type == 'fill_relay':
        contract_address = chain_dict['contract_fillrelay']
    is_eip1559 = chain_dict['is_eip1559']

    if contract_address:
        res = verify_contract(chain_dict['chain_id'], contract_address, contract_type, is_eip1559=is_eip1559)
        print(chain_dict['chain_name'],'verify deposit:',res)

# chain_dict = get_chain(chain_id=300)
# verify_contract_one(chain_dict, 'deposit')
# verify_contract_one(chain_dict, 'fill_relay')

def verify_deposits(is_mainnet=False):
    chain_dicts = get_chains(is_mainnet=is_mainnet)
    chain_dicts = [i for i in chain_dicts if i['contract_deposit'] is not None]
    for chain_dict in chain_dicts:
        verify_contract_one(chain_dict, 'deposit')
        verify_contract_one(chain_dict, 'fill_relay')

# verify_deposits()

#for test
def print_contract_deposit_url():
    chain_dicts = get_chains()
    for chain_dict in chain_dicts:
        url_contract_deposit = get_address_url(chain_dict['block_explorer'], chain_dict['contract_deposit'])
        url_contract_fillrelay = get_address_url(chain_dict['block_explorer'], chain_dict['contract_fillrelay'])
        print(url_contract_deposit)
        print(url_contract_fillrelay)

# print_contract_deposit_url()

def deploy_add_vault_author_one(chain_dict,contract_type):
    if contract_type == 'deposit':
        contract_address = chain_dict['contract_deposit']
    if contract_type == 'fill_relay':
        contract_address = chain_dict['contract_fillrelay']
    deploy_add_vault_author(contract_address, contract_type, chain_dict['rpc_url'], is_eip1559=chain_dict['is_eip1559'])

def deploy_add_vault_authors(contract_type,is_mainnet=False):
    chain_dicts = get_chains(is_mainnet=is_mainnet)
    for chain_dict in chain_dicts:
        deploy_add_vault_author_one(chain_dict,contract_type)

def deploy_add_vault_authors_concurrent(contract_type,is_mainnet=False):
    chain_dicts = get_chains(is_mainnet=is_mainnet)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(lambda chain_dict: deploy_add_vault_author_one(chain_dict, contract_type), chain_dicts)

# chain_dict = get_chain(chain_id=300)
# deploy_add_vault_author_one(chain_dict, 'deposit')
# deploy_add_vault_author_one(chain_dict, 'fill_relay')
# deploy_add_vault_authors(contract_type='deposit')
# deploy_add_vault_authors(contract_type='fill_relay')
# deploy_add_vault_authors_concurrent(contract_type='deposit')
# deploy_add_vault_authors_concurrent(contract_type='fill_relay')

def approve_token_one(chain_dict):
    approve_token(chain_dict['token_address'], chain_dict['contract_fillrelay'], chain_dict['rpc_url'], is_eip1559=chain_dict['is_eip1559'])

def approve_tokens(token_symbol=None,token_address=None,token_group=None,is_mainnet=False):
    token_dicts = get_tokens_with_chains(token_symbol=token_symbol,
                    token_address=token_address,token_group=token_group,is_mainnet=is_mainnet)
    for token_dict in token_dicts:
        approve_token_one(token_dict)

def approve_tokens_concurrent(token_symbol=None, token_address=None, token_group=None,is_mainnet=False):
    token_dicts = get_tokens_with_chains(token_symbol=token_symbol, 
                    token_address=token_address, token_group=token_group,is_mainnet=is_mainnet)
    # print([ i['chain_name'] for i in token_dicts])
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(approve_token_one, token_dicts)

#client approve 0 for MBT
# token_dicts = get_tokens_with_chains(token_symbol='MBT')
# for token_dict in token_dicts:
#     if token_dict['chain_id'] == 300:
#         approve_token(token_dict['token_address'], token_dict['contract_deposit'],token_dict['rpc_url'], 
#                         private_key=CLIENT_PRIVATE_KEY, is_eip1559=token_dict['is_eip1559'], zero=True)

# approve_tokens(token_symbol='MBT')
# approve_tokens_concurrent(token_symbol='MBT')
# chain_dict = get_chain(chain_id=300)
# approve_token(chain_dict['token_address'], chain_dict['contract_fillrelay'],chain_dict['rpc_url'], 
#                         private_key=CLIENT_PRIVATE_KEY, is_eip1559=chain_dict['is_eip1559'])

def transfer_eth_one(chain_dict,amount=0.0005):
    transfer_eth(recipient_address=CLIENT, amount_human=amount, decimals=chain_dict['native_token_decimals'],
            rpc_url=chain_dict['rpc_url'], private_key=VAULT_PRIVATE_KEY, is_eip1559=chain_dict['is_eip1559'])

def transfer_eths(amount=0.0005):
    chain_dicts = get_chains()
    for chain_dict in chain_dicts:
        transfer_eth_one(chain_dict, amount)

def transfer_eths_concurrent(amount=0.0005):
    chain_dicts = get_chains()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda chain_dict: transfer_eth_one(chain_dict, amount), chain_dicts)

# transfer_eths_concurrent()

def transfer_erc_one(token_dict,recipient_address=CLIENT,amount=100):
    transfer_erc(token_dict['token_address'], recipient_address, amount, token_dict['rpc_url'], 
                decimals=token_dict['decimals'],
                private_key=DEPLOYER_PRIVATE_KEY, is_eip1559=token_dict['is_eip1559'])

def transfer_ercs(recipient_address=CLIENT, amount=100):
    token_dicts = get_tokens_with_chains(token_symbol='MBT')
    for token_dict in token_dicts:
        transfer_erc_one(token_dict, recipient_address, amount)

def transfer_ercs_concurrent(recipient_address=CLIENT,amount=100):
    token_dicts = get_tokens_with_chains(token_symbol='MBT')
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda token_dict: transfer_erc_one(token_dict, recipient_address, amount), token_dicts)

# transfer_ercs()
# transfer_ercs_concurrent(recipient_address=VAULT, amount=100)