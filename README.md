uvicorn main:app --host 0.0.0.0 --port 9000

测试环境webhook
uvicorn main:app --port 8168
https://wh.ghoti.finance/webhook

pip install -r requirements.txt

#createdb
sudo -u postgres psql
postgres=# CREATE USER ghoti WITH PASSWORD '';
postgres=# ALTER USER ghoti WITH SUPERUSER;
<!-- postgres=# alter user ghoti with password ''; -->
postgres=# create database bridge;
postgres=# \c bridge;
postgres=# GRANT ALL PRIVILEGES ON DATABASE bridge TO ghoti;

<!-- CREATE USER ghoti WITH PASSWORD '*#$dTDN!'; -->
<!-- ALTER USER ghoti WITH SUPERUSER; -->
<!-- alter user ghoti with password '*#$dTDN!'; -->
<!-- create database bridge; -->
<!-- GRANT ALL PRIVILEGES ON DATABASE bridge TO ghoti; -->

#jwt
暂时没用
#partner 
partner_dict = {
    'name':'admin',
    'password':'123',
    'note':'',
    'is_active': True
}

CREATE TABLE partner(
    id  SERIAL PRIMARY KEY,
    name varchar(50) NULL,
    password varchar(200) NULL,
    note varchar(20) NULL,
    is_active boolean default true
);

#table chain 节点信息
{
    'chain_name':'Arbitrum One',
    'alias_name':'arb',
    'is_mainnet':1,
    'rpc_url':'https://patient-misty-breeze.arbitrum-mainnet.quiknode.pro/c4c7d373826e5de7e77fe587cef2e5c80d2b6531',
    'rpc_url_bak':'https://nova.arbitrum.io/rpc',
    'chainid':42161,
    'contract_deposit':'0x5bD6e85cD235d4c01E04344897Fc97DBd9011155',
    'contract_fillrelay':'0xd9ACf96764781c6a0891734226E7Cb824e2017E2',
    'block_explorer':'https://arbiscan.io',
    'chain_logo_url': 'https://owlto.finance/icon/chain/Ethereum.png',
    "alchemy_network": "BASE_SEPOLIA",
    'chain_note': 'Arbitrum One'
},

#rpc_url  付费节点
#rpc_url_bak  官方或者备用节点

CREATE TABLE chain(
    id SERIAL PRIMARY KEY,
    chain_name varchar(50) NULL,
    alias_name varchar(20) NULL,
    is_mainnet BOOLEAN NOT NULL DEFAULT true,
    rpc_url varchar(500) NULL,
    rpc_url_bak varchar(500) NULL,
    chain_id INTEGER NULL,
    contract_deposit varchar(200) NULL,
    contract_fillrelay varchar(200) NULL,
    block_explorer varchar(500) NOT NULL,
    chain_logo_url varchar(500) NOT NULL,
    alchemy_network varchar(200) NULL,
    chain_note TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    create_time TIMESTAMP DEFAULT NOW() NOT NULL,
    update_time TIMESTAMP DEFAULT NULL
);

CREATE INDEX idx_chain_is_mainnet ON chain(is_mainnet);
CREATE INDEX idx_chain_is_active ON chain(is_active);
CREATE INDEX idx_chain_chain_id ON chain(chain_id);

CREATE UNIQUE INDEX idx_unique_chain_id 
ON chain (chain_id) 
WHERE chain_id IS NOT NULL;

#不同链的最小最大值

#table token 代币
{
    'chain_db_id':'1',
    'is_native_token':0,
    'token_name':'USDT',
    'token_group':'1',
    'token_note':'',
    'token_address':'0x997bF3db364cA8A15931e9a61dAde670328196d7',
    'decimals':18, 
    'min_num':10, 
    'max_num':100,
    'token_logo_url':'https://owlto.finance/icon/token/USDC.png'
},

#is_native_token gas token
CREATE TABLE token(
    id  SERIAL PRIMARY KEY,
    chain_db_id integer NOT NULL,
    is_native_token boolean DEFAULT FALSE,
    token_name varchar(50) NULL,
    token_symbol VARCHAR(20) NULL,
    token_group varchar(50) NULL,
    token_address varchar(200) NULL,
    decimals varchar(20) NOT NULL,
    min_num decimal DEFAULT NULL,
    max_num decimal DEFAULT NULL,
    token_logo_url varchar(500) NULL,
    token_note TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    create_time TIMESTAMP DEFAULT NOW() NOT NULL,
    update_time TIMESTAMP DEFAULT NULL
);

CREATE INDEX idx_token_chain_id ON token(chain_db_id);
CREATE INDEX idx_token_is_native ON token(is_native_token);
CREATE INDEX idx_token_name ON token(token_name);
CREATE INDEX idx_token_symbol ON token(token_symbol);
CREATE INDEX idx_token_group ON token(token_group);
CREATE INDEX idx_token_is_active ON token(is_active);
CREATE INDEX idx_token_token_address ON token(token_address);

#转账明细
#status
null(初始)--1(成功)
0(不处理) 黑名单用户转入或者粉层攻击
#tx_status
来自接口
{
    'tx_hash':'0x5cdace5465cdc1689600e8b25982a76f6f09c27c60266c04fd99f2b371563784', webhook transaction.hash  scan_hash hash
    'status':1
    #deposit fillRelay
    'contract_addr_call': '0x9AA8668E11B1e9670B4DC8e81add17751bA1a4Ea',    webhook logs0.account.address  transaction.to 
    'txl_related_id':,
    'tx_status': 1,   txlist txreceipt_status  webhook transaction.status
    'is_refund': 0,
    'create_time': '',
    'update_time': '',
    'tx_time': '',  #1758451689 to  txlist timestamp   webhook block.timestamp
    'addr_from': '0xd45f62ae86e01da43a162aa3cd320fca3c1b178d',  txlist from  webhook.from.address scan_hash from
    'addr_to': '0xbA37D7ed1cFF3dDab5f23ee99525291dcA00999D',   calldata  
    'recipient': '' calldata
    'chain_db_id': 3,          calldata 
    'dst_chain_db_id':''       calldata
    'token_id': 10,            calldata 
    'num': 1000000000000000,   calldata 
    'tx_fee': 2309350000000,   25000000*92374  txlist gas    webhook.effectiveGasPrice*gasUsed
    'nonce': 99,  txlist nonce    webhook transaction.nonce  scan_hash nonce
    'gas_used': 92374,   txlist gasUsed    webhook transaction.gasUsed 
    'gas_price': 25000000,  txlist gasPrice   webhook transaction.effectiveGasPrice /gasPrice  
    'estimate_gas_limit': 415185,  tx_params.gas -- txlist gas    webhook transaction.gas  scan_hash gas
    'estimate_gas_price': ,   eip1559 没这个值
    #EIP-1559 
    'eip_type': '0x2',  eth_getTransactionReceipt.type
    'max_fee_per_gas': 38500000,          tx_params.maxFeePerGas     webhook transaction.maxFeePerGas scan_hash maxFeePerGas
    'max_priority_fee_per_gas': 1000000,   tx_params.maxPriorityFeePerGas   webhook transaction.maxPriorityFeePerGas scan_hash maxPriorityFeePerGas
    'note': ''
}

#主要是在合约里面控制,  txline只是日志记录
deposit client -- vault
fillRelay vault -- client

#退款
dst_chain == orgin_chain

一主，多从
#从单关联主单id
txl_related_id 为判断标志

#status
判断成功标志
1.有子单 (正常转/退回)
2.子单数量足够

CREATE TABLE txline(
    id  SERIAL PRIMARY KEY,
    tx_hash varchar(200) UNIQUE NOT NULL,
    status INTEGER DEFAULT NULL,
    contract_addr_call VARCHAR(200) DEFAULT NULL,
    txl_related_id INTEGER DEFAULT NULL, 
    tx_status INTEGER DEFAULT NULL,
    is_refund INTEGER DEFAULT 0,
    tx_time TIMESTAMP DEFAULT NULL,
    addr_from VARCHAR(200) DEFAULT NULL,
    addr_to VARCHAR(200) DEFAULT NULL,
    recipient VARCHAR(200) DEFAULT NULL,
    chain_db_id INTEGER DEFAULT NULL,
    dst_chain_db_id INTEGER DEFAULT NULL,
    token_id INTEGER NOT NULL,
    num NUMERIC(78,0) DEFAULT NULL,
    tx_fee NUMERIC(78,0) DEFAULT NULL,
    nonce BIGINT DEFAULT NULL,
    gas_used BIGINT DEFAULT NULL,  
    gas_price BIGINT DEFAULT NULL,
    estimate_gas_limit BIGINT DEFAULT NULL, 
    estimate_gas_price BIGINT DEFAULT NULL,  
    eip_type VARCHAR(50) DEFAULT NULL,  
    max_fee_per_gas BIGINT DEFAULT NULL,
    max_priority_fee_per_gas BIGINT DEFAULT NULL,
    note TEXT,
    create_time TIMESTAMP DEFAULT NOW() NOT NULL,
    update_time TIMESTAMP DEFAULT NULL
);

CREATE INDEX idx_txline_addr_from ON txline(addr_from);
CREATE INDEX idx_txline_addr_to ON txline(addr_to);
CREATE INDEX idx_txline_recipient ON txline(recipient);
CREATE INDEX idx_txline_chain_db_id ON txline(chain_db_id);
CREATE INDEX idx_txline_chain_db_id ON txline(dst_chain_db_id);
CREATE INDEX idx_txline_token_id ON txline(token_id);
CREATE INDEX idx_txline_status ON txline(status);
CREATE INDEX idx_txline_tx_status ON txline(tx_status);
CREATE INDEX idx_txline_tx_time ON txline(tx_time);
CREATE INDEX idx_txline_create_time ON txline(create_time);