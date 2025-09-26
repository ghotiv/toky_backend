import time
from datetime import datetime, timedelta

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from data_util import get_vault_addr

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


@app.get("/get_vault_addr",summary='get vault address',
        description='''
            get vault address
        ''')
def fast_get_vault_addr():
    return get_vault_addr()


#todo
def get_balances():
    return {}


@app.get("/get_chain_dicts",summary='get chain list',
        description='''
            get chain list
        ''')
def fast_get_chain_dicts():
    return get_chain_dicts()



@app.get("/get_token_dicts",summary='get token list',
        description='''
            get token list
        ''')
def fast_get_token_dicts():
    return get_token_dicts()


@app.get("/get_txls",summary='get_txls',
        description='''
            get_txls 获取转账详情
        ''')
def fast_get_txls(txl_id: str='', tx_hash: str='',
                    page: int = 1, prepage: int = 10):
    items = get_txls(txl_id,tx_hash)
    res = {"items": items[(page-1)*prepage:page*prepage],
        "total": len(items),
        }
    return res