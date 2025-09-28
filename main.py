import time
from datetime import datetime, timedelta

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from data_util import get_vault_address, api_get_token_groups, api_get_chains_by_token_group
from web3_call import get_deposit_args

app = FastAPI(title='bridge',description='bridge api')

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:9090",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://43.134.49.56",
    "http://192.168.1.76:9090",
    "*",
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

#todo
def get_balances():
    return {}

@app.get("/get_txls",summary='get_txls',
        description='''
            get_txls get transfer details
        ''')
def fast_get_txls(txl_id: str='', tx_hash: str='',
                    page: int = 1, prepage: int = 10):
    items = get_txls(txl_id,tx_hash)
    res = {"items": items[(page-1)*prepage:page*prepage],
        "total": len(items),
        }
    return res