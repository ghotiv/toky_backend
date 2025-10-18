from fastapi import FastAPI
# from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from data_util import get_vault_address, api_get_token_groups, \
    api_get_chains_by_token_group, get_txls_pair, get_deposit_args,\
    get_suggested_fees, get_price, check_create_refer, get_refer, update_refer

from web3_call import call_erc_allowance


class CreateRefer(BaseModel):
    refer_code:str = Field(..., description='refer code')
    account_address:str = Field(..., description='account address')

class UpdateRefer(BaseModel):
    account_address:str = Field(..., description='account address')
    refer_code:str = Field(..., description='refer code')

app = FastAPI(title='bridge',description='bridge api')

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3030",
    "http://localhost:3000",
    "http://localhost:9090",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://43.134.49.56",
    "http://192.168.1.76:9090",
    "https://www.toky.finance",
    "https://toky.finance",
    "https://api.toky.finance",
    # "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Credentials (Authorization headers, Cookies, etc)
    allow_credentials=True,
    # Specific HTTP methods (POST, PUT) or all of them with the wildcard "*".
    allow_methods=["*"],
    # Specific HTTP headers or all of them with the wildcard "*".
    allow_headers=["*"],
)

# @app.options("/{full_path:path}", include_in_schema=False)
# def preflight_handler(full_path: str):
#     return {}

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     # Credentials (Authorization headers, Cookies, etc)
#     allow_credentials=False,
#     # Specific HTTP methods (POST, PUT) or all of them with the wildcard "*".
#     allow_methods=["*"],
#     # Specific HTTP headers or all of them with the wildcard "*".
#     allow_headers=["*"],
# )

@app.get("/get_vault_address",summary='get vault address',
        description='''
            get vault address
        ''')
def fast_get_vault_address():
    return get_vault_address()

@app.get("/get_token_groups",summary='get token groups',
        description='''
            get token groups
        ''')
def fast_get_token_groups():
    return api_get_token_groups()

@app.get("/get_chains_by_token_group",summary='get chains by token group',
        description='''
            get chains by token group
        ''')
def fast_get_chains_by_token_group(token_group: str):
    return api_get_chains_by_token_group(token_group)

@app.get("/get_deposit_args",summary='get deposit args',
        description='''
            get deposit args
        ''')
def fast_get_deposit_args(token_group: str,from_chain_id: int,dst_chain_id: int,num_input: float,recipient: str):
    res = get_deposit_args(token_group,from_chain_id,dst_chain_id,num_input,recipient)
    return res

@app.get("/get_erc_allowance",summary='get erc allowance',
        description='''
            get erc allowance
        ''')
def fast_get_erc_allowance(chain_id: int, token_address: str, spender_address: str, 
                owner_address: str, human: bool = False):
    res = call_erc_allowance(chain_id, token_address, spender_address,
                owner_address, human=human)
    return res

@app.get("/get_suggested_fees",summary='get suggested fees',
        description='''
            get suggested fees
        ''')
def fast_get_suggested_fees(origin_chain_id: int, dst_chain_id: int, input_amount_human: float, token_group: str):
    res = get_suggested_fees(origin_chain_id, dst_chain_id, input_amount_human, token_group)
    return res


@app.get("/get_txls_pair",summary='get_txls_pair',
        description='''
            get_txls_pair get transfer details
        ''')
def fast_get_txls_pair(addr: str, status: int = None, limit: int = 50, offset: int = 0):
    res = get_txls_pair(addr=addr, status=status, limit=limit, offset=offset)
    return res

@app.get("/get_price",summary='get price',
        description='''
            get price
        ''')
def fast_get_price(currency: str):
    return get_price(currency)

@app.get("/get_refer",summary='get refer',
        description='''
            get refer
        ''')
def fast_get_refer(account_address: str):
    res = get_refer(account_address)
    return res

@app.post("/create_refer", summary='create refer',
        description='''
            create refer
        ''')
def fast_create_refer(arg:CreateRefer):
    res = check_create_refer({'refer_code':arg.refer_code,'account_address':arg.account_address})
    return res

@app.post("/update_refer", summary='update refer',
        description='''
            update refer
        ''')
def fast_update_refer(arg:UpdateRefer):
    res = update_refer(arg.account_address, arg.refer_code)
    return res