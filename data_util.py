from my_conf import *
from eth_utils import to_checksum_address

#todo:数据来自数据库
def get_chain(chain_id=None,alchemy_network=None,all_chain=False):
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
            'contract_fillRelay': '0x622201610744D2D2ec62fbb1bc9D8C16723B5330',
            'alchemy_network': 'BASE_SEPOLIA',
            'is_mainnet': False,
        },
        #zksync sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/zksync_era_sepolia',
            'chain_id': 300,
            'contract_deposit': '0x9AA8668E11B1e9670B4DC8e81add17751bA1a4Ea',
            'contract_fillRelay': '0x706a1b5D991ea32c7D60C7063d6f005da05c0cB5',
            'alchemy_network': 'ZKSYNC_SEPOLIA',
            'is_mainnet': False,
        },
        #Polygon Amoy
        {
            'rpc_url': 'https://rpc-amoy.polygon.technology',
            'chain_id': 80002,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'POLYGON_AMOY',
            'is_mainnet': False,
        },
        #arbitrum sepolia
        {
            'rpc_url': 'https://sepolia-rollup.arbitrum.io/rpc',
            'chain_id': 421614,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'ARBITRUM_SEPOLIA',
            'is_mainnet': False,
        },
        #optimism sepolia
        {
            'rpc_url': 'https://sepolia.optimism.io',
            'chain_id': 11155420,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'OPT_SEPOLIA',
            'is_mainnet': False,
        },
        #bsc testnet
        {
            'rpc_url': 'https://bsc-testnet.public.blastapi.io',
            'chain_id': 97,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'BNB_TESTNET',
            'is_mainnet': False,
        },
        #blast sepolia
        {
            'rpc_url': 'https://rpc.ankr.com/blast_testnet_sepolia',
            'chain_id': 168587773,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x72254a6Bc561aBF70167eD155451b58C82c0b5Ad',
            'alchemy_network': 'BLAST_SEPOLIA',
            'is_mainnet': False,
        },
        #scroll sepolia
        {
            'rpc_url': 'https://scroll-sepolia.drpc.org',
            'chain_id': 534351,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0xeFA84c418CB370474bf082027635261A5a79262c',
            'alchemy_network': 'SCROLL_SEPOLIA',
            'is_mainnet': False,
        },
        #linea sepolia
        {
            'rpc_url': 'https://linea-sepolia-rpc.publicnode.com',
            'chain_id': 59141,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'LINEA_SEPOLIA',
            'is_mainnet': False,
        },
        #mantle sepolia
        {
            'rpc_url': 'https://rpc.sepolia.mantle.xyz',
            'chain_id': 5003,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'MANTLE_SEPOLIA',
            'is_mainnet': False,
        },
        #polygon zkevm cardona testnet
        {
            'rpc_url': 'https://rpc.cardona.zkevm-rpc.com',
            'chain_id': 2442,
            'contract_deposit': '0xe13D60316ce2Aa7bd2C680E3BF20a0347E0fa5bE',
            'contract_fillRelay': '0x707aC01D82C3F38e513675C26F487499280D84B8',
            'alchemy_network': 'CARDONA_ZKEVM',
            'is_mainnet': False,
        },
        #mode sepolia
        {
            'rpc_url': 'https://sepolia.mode.network',
            'chain_id': 919,
            'contract_deposit': '0x62d105b659184cf82fe0e2f021397821ac5dca77',
            'contract_fillRelay': '0xC4489dD6Fb5032BAD5bbF66583B2D6532Bc97293',
            'alchemy_network': 'MODE_SEPOLIA',
            'is_mainnet': False,
        },
        #zora sepolia
        {
            'rpc_url': 'https://sepolia.rpc.zora.energy',
            'chain_id': 999999999,
            'contract_deposit': '0xe13d60316ce2aa7bd2c680e3bf20a0347e0fa5be',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'ZORA_SEPOLIA',
            'is_mainnet': False,
        },
        #manta sepolia
        {
            'rpc_url': 'https://pacific-rpc.sepolia-testnet.manta.network/http',
            'chain_id': 3441006,
            'contract_deposit': '0xe13d60316ce2aa7bd2c680e3bf20a0347e0fa5be',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'MANTA_SEPOLIA',
            'is_mainnet': False,
        },
        #taiko hekla
        {
            'rpc_url': 'https://rpc.hekla.taiko.xyz',
            'chain_id': 167009,
            'contract_deposit': '0xe13d60316ce2aa7bd2c680e3bf20a0347e0fa5be',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'TAIKO_HEKLA',
            'is_mainnet': False,
        },
        #opbnb testnet
        {
            'rpc_url': 'https://opbnb-testnet-rpc.bnbchain.org',
            'chain_id': 5611,
            'contract_deposit': '0xe13d60316ce2aa7bd2c680e3bf20a0347e0fa5be',
            'contract_fillRelay': '0xEF6242FC3a8c3C7216E4F594271086BbbdaF3ac2',
            'alchemy_network': 'OPBNB_TESTNET',
            'is_mainnet': False,
        },
    ]
    if all_chain:
        return res_dicts
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
        {
            'chain_id': 80002,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 80002,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 421614,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 421614,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 11155420,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 11155420,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 97,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 97,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        {
            'chain_id': 168587773,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 168587773,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Scroll Sepolia
        {
            'chain_id': 534351,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 534351,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Linea Sepolia
        {
            'chain_id': 59141,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 59141,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Mantle Sepolia
        {
            'chain_id': 5003,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 5003,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Polygon zkEVM Cardona
        {
            'chain_id': 2442,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 2442,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Mode Sepolia
        {
            'chain_id': 919,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 919,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Zora Sepolia
        {
            'chain_id': 999999999,
            'token_name': 'MBT',
            'token_address': '0xc4C5896a32e75ed3b59C48620E3b0833D0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 999999999,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Manta Sepolia
        {
            'chain_id': 3441006,
            'token_name': 'MBT',
            'token_address': '0xc4c5896a32e75ed3b59c48620e3b0833d0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 3441006,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # Taiko Hekla
        {
            'chain_id': 167009,
            'token_name': 'MBT',
            'token_address': '0xc4c5896a32e75ed3b59c48620e3b0833d0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 167009,
            'token_name': 'ETH',
            'token_address': '0x0000000000000000000000000000000000000000',
            'is_mainnet': False,
        },
        # opBNB Testnet
        {
            'chain_id': 5611,
            'token_name': 'MBT',
            'token_address': '0xc4c5896a32e75ed3b59c48620e3b0833d0f98820',
            'is_mainnet': False,
        },
        {
            'chain_id': 5611,
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