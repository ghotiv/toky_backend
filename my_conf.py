# TZ = 'Asia/Shanghai'
TZ = 'UTC'

FILL_RATE = 0.9995
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

ERROR_SELECTORS = {
    '0x813dc85d': 'NotOwnerError()',
    '0x5e874202': 'LengthError()',
    '0x0f74927f': 'ZeroAddressError()',
    '0x4ff64a9f': 'AmountError()',
    '0x62787609': 'RecipientError()',
    '0x6c9d47e8': 'CallError()',
    '0xe55de02a': 'VaultNotWhitelistedError()',
    '0x67b45f5a': 'VaultAlreadyWhitelistedError()',
    '0x33ff682c': 'VaultNotFoundError()',
    '0x3a1a1b5f': 'InvalidDestinationChainIdError()',
    '0x7a2c8890': 'RelayAlreadyFilled()',
    '0xea8e4eb5': 'NotAuthorized()',
    '0x5b67e2c6': 'InsufficientBalance()',
    '0x8c379a00': 'Error(string)',
    '0x4e487b71': 'Panic(uint256)',
    '0x08c379a0': 'Error(string)',
    '0x1e4fbdf7': 'OwnableUnauthorizedAccount(address)',
    '0x49df728c': 'OwnableInvalidOwner(address)',
    '0x118cdaa7': 'AddressEmptyCode(address)',
    '0x5274afe7': 'AddressInsufficientBalance(address)',
    '0x7939f424': 'SafeERC20FailedOperation(address)',
    '0xa9059cbb': 'transfer(address,uint256)',
    '0x095ea7b3': 'approve(address,uint256)',
}

ACROSS_ETH_MAP = {
    1:      '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # Ethereum Mainnet (WETH)
    42161:  '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # Arbitrum One (WETH)
    8453:   '0x4200000000000000000000000000000000000006',  # Base Mainnet (WETH)
    10:     '0x4200000000000000000000000000000000000006',  # Optimism Mainnet (WETH)
    137:    '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',  # Polygon PoS (WETH)
    56:     '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',  # BNB Chain (ETH - wrapped)
    59144:  '0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f',  # Linea (WETH)
    534352: '0x5300000000000000000000000000000000000004',  # Scroll (WETH)
    324:    '0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91',  # zkSync Era (WETH)
    5000:   '0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111',  # Mantle (ETH token)
    34443:  '0x4200000000000000000000000000000000000006',  # Mode (WETH)
    81457:  '0x4300000000000000000000000000000000000004',  # Blast (WETH)
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

from abi_conf import *
from my_private_conf import *
