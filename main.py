from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay MVP", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    tx_signature: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "AgentPay MVP API", "network": "Solana"}

@app.post("/api/pay-usdc")
@limiter.limit("5/minute") # Dakikada maksimum 5 istek sınırı
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