from eth_utils import to_checksum_address

from my_conf import *

from data_util import get_token
from web3_util import get_wei_amount, get_bytes32_address
from web3_call import get_decode_calldata, call_deposit, call_fill_relay

def test_get_decode_calldata():
    calldata = '0xeef40c38000000000000000000000000ba37d7ed1cff3ddab5f23ee99525291dca00999d000000000000000000000000d45f62ae86e01da43a162aa3cd320fca3c1b178d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a40000000000000000000000000000000000000000000000000000000000000014a3400000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000568656c6c6f000000000000000000000000000000000000000000000000000000'
    calldata_dict = get_decode_calldata(calldata)
    print(calldata_dict)

def test_call_deposit(private_key=None,recipient=None):
    # block_chainid = 300
    # block_chainid = 11155111
    block_chainid = 11155420

    # inputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    # inputAmount = get_wei_amount(0.0001)
    # inputAmount = get_wei_amount(1000)

    # inputToken = get_token(chain_id=block_chainid,token_name='ETH')['token_address']
    # inputAmount = get_wei_amount(0.001)
    inputToken = get_token(chain_id=block_chainid,token_name='MBT')['token_address']
    inputAmount = get_wei_amount(0.001)
    # inputAmount = get_wei_amount(1)

    # destinationChainId = 11155111
    destinationChainId = 84532
    # destinationChainId = 300
    message = b'hello'
    recipient_bytes32 = get_bytes32_address(recipient)
    call_deposit(VAULT, recipient_bytes32, inputToken, inputAmount, 
                    destinationChainId, message, block_chainid,
                    private_key=private_key)

def test_call_fill_relay():
    block_chainid = 84532
    outputToken = to_checksum_address('0x0000000000000000000000000000000000000000')
    # outputToken = to_checksum_address('0xc4C5896a32e75ed3b59C48620E3b0833D0f98820')
    outputAmount = get_wei_amount(1*0.9)
    # inputAmount = get_wei_amount(1000)
    originChainId = 11155111
    message = b'hello'
    recipient = to_checksum_address(CLIENT)
    # depositHash = get_bytes32_address('0x505972ce768406f4b58c25f49439c91664e4e8e5cb51ccfb13f192f5308accc3')
    depositHash = b'\xe4QowE\xbd\xb4\x8b$+\x15\xec\x12*oh\xab\xde<G\xfb\xb3\xeb\xad\x13\x13\x9a(\xad\xc1\x94\xd3'
    call_fill_relay(recipient, outputToken, outputAmount, originChainId, depositHash, message, 
                        block_chainid, private_key=VAULT_PRIVATE_KEY)

if __name__ == '__main__':
    test_call_deposit(private_key=CLIENT_PRIVATE_KEY,recipient=CLIENT)
    # test_call_deposit(private_key=DEPLOYER_PRIVATE_KEY,recipient=DEPLOYER)
    # test_get_decode_calldata()
    # test_call_fill_relay()