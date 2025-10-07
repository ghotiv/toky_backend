import shlex
import subprocess
import json
from eth_utils import is_checksum_address

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
    res = run_cmd(cmd_str)

    # # # print(res.stdout)

    for line in res.stdout.strip().split('\n'):
        try:
            line_dict = json.loads(line)
        except:
            continue
        if {'tx_hash', 'contract_address'}.issubset(line_dict.keys()) and \
                line_dict['status'] == 'success' and is_checksum_address(line_dict['contract_address']):
            return line_dict['contract_address']
    return None


def verify_contract(chain_id, contract_address, contract_type, etherscan_api_key=ETHERSCAN_API_KEY, is_eip1559=True):
    contract_path = VERIFY_PATH_MAP[contract_type]
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f"forge verify-contract --chain-id {chain_id} --verifier etherscan --etherscan-api-key {etherscan_api_key} --compiler-version 0.8.18 {contract_address} {contract_path} {legacy_flag}"
    print(cmd_str)
    run_cmd(cmd_str)
    return 

def deposit_add_whitelist(contract_address, rpc_url, private_key=DEPLOYER_PRIVATE_KEY, vault=VAULT, is_eip1559=True):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f'cast send {contract_address} "addVaultToWhitelist(address)" {vault} --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return 

# cast send $TOKEN_ADDRESS "approve(address,uint256)" $DEPOSITOR_ADDRESS "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" --private-key $CLIENT_PRIVATE_KEY --rpc-url $RPC_URL

def approve_token(token_address, contract_address, rpc_url, private_key=VAULT_PRIVATE_KEY, is_eip1559=True):
    legacy_flag = '--legacy' if not is_eip1559 else ''
    cmd_str = f'cast send {token_address} "approve(address,uint256)" {contract_address} "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" --private-key {private_key} --rpc-url {rpc_url} {legacy_flag}'
    print(cmd_str)
    run_cmd(cmd_str)
    return 