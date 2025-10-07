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

from my_private_conf import *
