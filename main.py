
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
def webhook(request: Request):
    data = request.json()
    print(data)
    return "success"