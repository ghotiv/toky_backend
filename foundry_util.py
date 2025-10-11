import shlex
import subprocess
import json
from eth_utils import is_checksum_address

from local_util import get_web3_wei_amount,get_web3_human_amount,str_to_int

from my_conf import CMD_PATH,DEPLOYER_PRIVATE_KEY,ETHERSCAN_API_KEY,VAULT,DEPLOY_PATH_MAP,VERIFY_PATH_MAP,VAULT_PRIVATE_KEY

def run_cmd(cmd_str, cwd=CMD_PATH,timeout=1200):
    cmd_list = shlex.split(cmd_str)
    res = subprocess.run(cmd_list, cwd=cwd, 
                capture_output=True, text=True, timeout=timeout)
    return res

# f"/Users/ghoti/.foundry/bin/forge script {script_path} --fork-url {rpc_url} --private-key {private_key} --broadcast --zksync --json"

def deploy_contract(rpc_url, contract_type, private_key=DEPLOYER_PRIVATE_KEY, is_eip1559=True):
    deploy_path = DEPLOY_PATH_MAP[contract_type]
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f"forge script {deploy_path} --rpc-url {rpc_url} --private-key {private_key} --broadcast {legacy_flag} --json"
    print(cmd_str)
    res_cmd = run_cmd(cmd_str)

    # print(res.stdout)

    for line in res_cmd.stdout.strip().split('\n'):
        try:
            line_dict = json.loads(line)
        except:
            continue
        if {'tx_hash', 'contract_address'}.issubset(line_dict.keys()) and \
                line_dict['status'] == 'success' and is_checksum_address(line_dict['contract_address']):
            return line_dict['contract_address']

    #有的只有logs
    for line in res_cmd.stdout.strip().split('\n'):
        try:
            line_dict = json.loads(line)
        except:
            continue
        if {'logs', 'success'}.issubset(line_dict.keys()) and line_dict['success'] == True :
            for i in line_dict['logs']:
                if 'deployed to:' in i:
                    contract_address = i.split(':')[1].strip()
                    return contract_address
    return None


def verify_contract(chain_id, contract_address, contract_type, etherscan_api_key=ETHERSCAN_API_KEY, is_eip1559=True):
    contract_path = VERIFY_PATH_MAP[contract_type]
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f"forge verify-contract --chain-id {chain_id} --verifier etherscan --etherscan-api-key {etherscan_api_key} --compiler-version 0.8.18 {contract_address} {contract_path} {legacy_flag}"
    print(cmd_str)
    run_cmd(cmd_str)
    return 

def deploy_add_vault_author(contract_address, contract_type, rpc_url, private_key=DEPLOYER_PRIVATE_KEY, vault=VAULT, is_eip1559=True):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    if contract_type == 'deposit':
        func_name = 'addVaultToWhitelist'
    if contract_type == 'fill_relay':
        func_name = 'addAuthorizedRelayer'
    cmd_str = f'cast send {contract_address} "{func_name}(address)" {vault} --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return 

# cast send $TOKEN_ADDRESS "approve(address,uint256)" $DEPOSITOR_ADDRESS "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" --private-key $CLIENT_PRIVATE_KEY --rpc-url $RPC_URL

def approve_token(token_address, contract_address, rpc_url, private_key=VAULT_PRIVATE_KEY, is_eip1559=True, zero=False):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    amount = '0' if zero else '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    cmd_str = f'cast send {token_address} "approve(address,uint256)" {contract_address} {amount} --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return 

# cast send $RECIPIENT_ADDRESS --value $transfer_amount_wei --private-key $SENDER_PRIVATE_KEY --rpc-url $RPC_URL
# cast send $TRANSFER_TOKEN_ADDRESS "transfer(address,uint256)" $RECIPIENT_ADDRESS $transfer_amount_wei --private-key $SENDER_PRIVATE_KEY --rpc-url $RPC_URL

def transfer_eth(recipient_address, amount_human, rpc_url, decimals=18, private_key=VAULT_PRIVATE_KEY, is_eip1559=True):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    amount_wei = str(get_web3_wei_amount(amount_human, decimals=decimals))
    cmd_str = f'cast send {recipient_address} --value {amount_wei} --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return 

def transfer_erc(token_address, recipient_address, amount_human, rpc_url, 
        decimals=18, private_key=VAULT_PRIVATE_KEY, is_eip1559=True):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    amount_wei = str(get_web3_wei_amount(amount_human, decimals=decimals))
    cmd_str = f'cast send {token_address} "transfer(address,uint256)" {recipient_address} {amount_wei} --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return

def cast_get_eth_balance(account_address, rpc_url, is_eip1559=True, human=False, decimals=18):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f'cast balance {account_address} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    res_cmd = run_cmd(cmd_str)
    res = None
    try:
        res = str_to_int(res_cmd.stdout.strip())
    except Exception as e:
        print(e)
    if res and human and decimals:
        res = get_web3_human_amount(res, decimals=decimals)
    return res

def cast_get_erc_balance(account_address, token_address, rpc_url, is_eip1559=True, human=False, decimals=18):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f'cast call {token_address} "balanceOf(address)" {account_address} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    res_cmd = run_cmd(cmd_str)
    res = None
    try:
        res = str_to_int(res_cmd.stdout.strip())
    except Exception as e:
        print(e)
    if res and human and decimals:
        decimals_cmd = f'cast call {token_address} "decimals()" --rpc-url {rpc_url} {legacy_flag}'
        res_cmd = run_cmd(decimals_cmd)
        decimals = str_to_int(res_cmd.stdout.strip())
        res = get_web3_human_amount(res, decimals=decimals)
    return res