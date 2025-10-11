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

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]
