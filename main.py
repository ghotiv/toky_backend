
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.post("/webhook")
def webhook(data: Dict[str, Any]):
    print(data)
    return "success"