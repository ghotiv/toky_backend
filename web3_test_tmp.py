from web3 import Web3

try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except Exception as e:
    from web3.middleware import geth_poa_middleware

from eth_abi import decode
from eth_utils import to_checksum_address, decode_hex, keccak, is_address, to_bytes

from my_conf import *

from web3_util import *

def test_get_decode_calldata():
    calldata = '0x000000000000000000000000d45f62ae86e01da43a162aa3cd320fca3c1b178d00000000000000000000000000000000000000000000000000005af3107a40000000000000000000000000000000000000000000000000000000000000014a3400000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000068bff7d0000000000000000000000000000000000000000000000000000000000000000568656c6c6f000000000000000000000000000000000000000000000000000000'
    res_decode_calldata = get_decode_calldata(calldata)
    print(res_decode_calldata)

def test_call_deposit():
    chain_id = 11155111
    w3 = get_w3(chain_id=chain_id)
    inputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    inputAmount = get_wei_amount(0.0001)
    # inputAmount = get_wei_amount(1000)
    destinationChainId = 84532
    message = b'hello'
    recipient_bytes32 = get_bytes32_address(client)
    contract_address = '0x5bD6e85cD235d4c01E04344897Fc97DBd9011155'
    call_deposit(vault, recipient_bytes32, inputToken, inputAmount, 
                    destinationChainId, message, contract_address, 
                    w3, private_key=client_private_key)

def test_call_fill_replay():
    chain_id = 84532
    w3 = get_w3(chain_id=chain_id)
    outputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    outputAmount = get_wei_amount(0.0001*0.9)
    # inputAmount = get_wei_amount(1000)
    originChainId = 11155111
    message = b'hello'
    recipient = to_checksum_address(client)
    contract_address = to_checksum_address('0x707ac01d82c3f38e513675c26f487499280d84b8')
    depositHash = get_bytes32_address('0x505972ce768406f4b58c25f49439c91664e4e8e5cb51ccfb13f192f5308accc3')
    call_fill_replay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        contract_address, w3, private_key=vault_private_key)


if __name__ == '__main__':
    test_call_deposit()
    # test_get_decode_calldata()
    # test_call_fill_replay()