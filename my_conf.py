# TZ = 'Asia/Shanghai'
TZ = 'UTC'

FILL_RATE = 0.9
L1_CHAIN_IDS = [11155111, 1, 97, 56, 59141, 59144]  # Ethereum, BSC, Linea (gas行为类似L1)
NOT_EIP1599_IDS = [2442]  # Metis Sepolia、Polygon zkEVM Cardona不支持EIP-1559
# 注意：BSC网络现在已经支持EIP-1559了

CMD_PATH = '~/project/my_token'

POA_CHAIN_IDS = [
        97,      # BSC Testnet
        56,      # BSC Mainnet 
        80002,   # Polygon Amoy (POA特性)
    ]

DEPLOY_PATH_MAP = {
    'deposit': 'script/DeployToky.s.sol:DeployTokyScript',
    'deposit_zksync': 'script/DeployTokyZkSync.s.sol:DeployTokyZkSyncScript',
    'fill_relay': 'script/DeployTokyFillRelay.s.sol:DeployTokyFillRelayScript',
    'fill_relay_zksync': 'script/DeployTokyFillRelayZkSync.s.sol:DeployTokyFillRelayZkSyncScript',
    'token': 'script/Deploy.s.sol:DeployScript',
    'token_zksync': 'script/DeployZkSync.s.sol:DeployZkSyncScript',
}

VERIFY_PATH_MAP = {
    'deposit': 'src/TokyDeposit.sol:Depositor',
    'fill_relay': 'src/TokyFillRelay.sol:TokyFillRelay',
}

DEPOSIT_ABI = [
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

FILL_RELAY_ABI = [
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

CHECK_RELAY_FILLED_ABI = [
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

#not use
alchemy_network_chain_testnet = {
    'ETH_SEPOLIA': 11155111,
    'ARBITRUM_SEPOLIA': 421614,
    'OPT_SEPOLIA': 11155420,
    'BASE_SEPOLIA': 84532,
    'POLYGON_AMOY': 80002,
    'BNB_TESTNET': 97,
    'ZKSYNC_SEPOLIA': 300,
    'POLYGON_ZK_SEPOLIA': 2442,
    'LINEA_SEPOLIA': 59141,
    'SCROLL_SEPOLIA': 534351,
    'MANTLE_SEPOLIA': 5003,
    'ARBITRUM_NOVA_SEPOLIA': 421614,
    'BLAST_SEPOLIA': 168587773,
    'MODE_SEPOLIA': 919,
    'ZORA_SEPOLIA': 999999999,
    'METIS_SEPOLIA': 59902
}

alchemy_network_chain_mainnet = {
    'ETH_MAINNET': 1,
    'ARBITRUM_MAINNET': 42161,
    'OPT_MAINNET': 10,
    'BASE_MAINNET': 8453,
    'POLYGON_MAINNET': 137,
    'BNB_MAINNET': 56,
    'ZKSYNC_MAINNET': 324,
    'POLYGON_ZK_MAINNET': 1101,
    'LINEA_MAINNET': 59144,
    'SCROLL_MAINNET': 534352,
    'MANTLE_MAINNET': 5000,
    'ARBITRUM_NOVA_MAINNET': 42170,
    'BLAST_MAINNET': 81457,
    'MODE_MAINNET': 34443,
    'ZORA_MAINNET': 7777777,
    'METIS_MAINNET': 1088
}

#override my_private_conf
'''
VAULT_PRIVATE_KEY = ''
DEPLOYER_PRIVATE_KEY = ''
CLIENT_PRIVATE_KEY = ''

DEPLOYER = ''
VAULT = ''
CLIENT = ''

DB_HOST=''
DB_DB=''
DB_USER=''
DB_PWD=''

REDIS_HOST=''
REDIS_PORT=6379
REDIS_PASSWORD=''
REDIS_DB = 0

VAULTS = [VAULT]

ETHERSCAN_API_KEY = 'YM1XSQ331HZD62TK6PW4IZDRVINNDIH9B3'

ETHERSCAN_API_KEYS = [
    'YM1XSQ331HZD62TK6PW4IZDRVINNDIH9B3',
    'G62JZX8M6CZ4HZTGVVIQ3EJ791C5AYJA6M',
    'CBH1URUV4XSS7JNE87UNAIKADF56HEPF13',
    'FMVF7A51HQA965IGR9V85I4C2HMR4224VF',
    '72UP122PWHRWNS2IPTYC8JHMS29D3828J4',
    '6KTNCFXV13K8QSQ7EIYARGVR8WS857JESS',
    'QFDHGSR93MJR9IFH2D3WY2U7CR7XENGPZ8',
    'T18DR119IU6YS573CBHWPW89YA2W4I4S4X',
    'QMFAAZPKW95HYPH7SF4ED4Z4BFUKJZT8GQ',
    '16HSJ6Z5C7MKDU8IMC9RHB4HQRV3WAVX9V',
]
'''

from my_private_conf import *
