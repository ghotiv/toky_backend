from my_conf import *
from eth_utils import to_checksum_address

#todo:数据来自数据库
def get_chain(chain_id=None,alchemy_network=None):
    res = {}
    res_dicts = [
        #sepolia
        {
            'rpc_url': 'https://ethereum-sepolia-rpc.publicnode.com',
            'chain_id': 11155111,
            'contract_deposit': '0x5bD6e85cD235d4c01E04344897Fc97DBd9011155',
            'contract_fillRelay': '0xd9ACf96764781c6a0891734226E7Cb824e2017E2',
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
        #metis sepolia
        {
            'rpc_url': 'https://sepolia.metisdevops.link',
            'chain_id': 59902,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '',
            'alchemy_network': 'METIS_SEPOLIA',
            'is_mainnet': False,
        },
    ]
    [i.update({'is_eip1559': i['chain_id'] not in NOT_EIP1599_IDS}) for i in res_dicts]
    [i.update({'is_l2': i['chain_id'] not in L1_CHAIN_IDS}) for i in res_dicts]
    if chain_id:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id), {})
    if alchemy_network:
        res = next((item for item in res_dicts if item['alchemy_network'] == alchemy_network), {})
    return res


def get_token(chain_id=None,token_name=None,token_address=None):
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
    if chain_id and token_name:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id and item['token_name'] == token_name), {})
    if chain_id and token_address:
        res = next((item for item in res_dicts if item['chain_id'] == chain_id and item['token_address'] == token_address), {})
    return res