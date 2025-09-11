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
    calldata = '0xeef40c38000000000000000000000000ba37d7ed1cff3ddab5f23ee99525291dca00999d000000000000000000000000d45f62ae86e01da43a162aa3cd320fca3c1b178d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a40000000000000000000000000000000000000000000000000000000000000014a3400000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000568656c6c6f000000000000000000000000000000000000000000000000000000'
    calldata_dict = get_decode_calldata(calldata)
    print(calldata_dict)

def test_call_deposit():
    block_chainid = 11155111

    # inputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    # inputAmount = get_wei_amount(0.0001)
    # inputAmount = get_wei_amount(1000)

    inputToken = to_checksum_address('0xf904709e8a2e0825fce724002be52dd853202750')
    inputAmount = get_wei_amount(0.0001)

    # destinationChainId = 84532
    destinationChainId = 1
    message = b'hello'
    recipient_bytes32 = get_bytes32_address(client)
    call_deposit(vault, recipient_bytes32, inputToken, inputAmount, 
                    destinationChainId, message, block_chainid, is_mainnet=False,
                    private_key=client_private_key)

def test_call_fill_relay():
    block_chainid = 84532
    # outputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    outputToken = to_checksum_address('0xc4C5896a32e75ed3b59C48620E3b0833D0f98820')
    outputAmount = get_wei_amount(1*0.9)
    # inputAmount = get_wei_amount(1000)
    originChainId = 11155111
    message = b'hello'
    recipient = to_checksum_address(client)
    # depositHash = get_bytes32_address('0x505972ce768406f4b58c25f49439c91664e4e8e5cb51ccfb13f192f5308accc3')
    depositHash = b'\xe4QowE\xbd\xb4\x8b$+\x15\xec\x12*oh\xab\xde<G\xfb\xb3\xeb\xad\x13\x13\x9a(\xad\xc1\x94\xd3'
    call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        block_chainid, private_key=vault_private_key, is_mainnet=False)

if __name__ == '__main__':
    test_call_deposit()
    # test_get_decode_calldata()
    # test_call_fill_relay()