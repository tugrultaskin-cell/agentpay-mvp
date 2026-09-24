from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AgentPay MVP", version="1.0.0")

# Solana Mainnet USDC Mint Adresi
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    recipient_wallet: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "AgentPay MVP API", "network": "Solana"}

@app.post("/api/pay-usdc")
def create_usdc_payment(data: PaymentRequest):
    try:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Geçersiz tutar.")
            
        return {
            "success": True,
            "message": "USDC ödeme talebi başarıyla oluşturuldu.",
            "token": "USDC",
            "mint_address": USDC_MINT,
            "recipient": data.recipient_wallet,
            "amount": data.amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))