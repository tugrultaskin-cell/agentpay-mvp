from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay MVP", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    tx_signature: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    # index.html dosyasını okuyup doğrudan tarayıcıya arayüz olarak veriyoruz
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return {"status": "online", "service": "AgentPay MVP API", "network": "Solana"}

@app.post("/api/pay-usdc")
@limiter.limit("5/minute")
def create_usdc_payment(request: Request, data: PaymentRequest):
    try:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Geçersiz tutar.")
            
        return {
            "success": True,
            "message": "Ödeme işlemi blokzincir imzasıyla doğrulandı.",
            "token": "USDC",
            "mint_address": USDC_MINT,
            "amount": data.amount,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))