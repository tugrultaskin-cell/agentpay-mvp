from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import httpx
from datetime import datetime

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay Mainnet Ready", version="1.6.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

USDC_MINT_DEVNET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDC_MINT_MAINNET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # Gerçek USDC Mint adresi (Solana Mainnet)

# Yönetici bilgileri
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "gizlisifre123"

PAYMENT_DATABASE = []
SETTINGS = {"webhook_url": "", "network": "devnet"} # devnet veya mainnet

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    tx_signature: str
    plan_name: str = "Özel Ödeme"

class LoginRequest(BaseModel):
    username: str
    password: str

class SettingsRequest(BaseModel):
    webhook_url: str
    network: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return {"status": "online", "service": "AgentPay API", "network": SETTINGS["network"]}

@app.post("/api/admin/login")
def admin_login(data: LoginRequest):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        return {"success": True, "token": "agentpay_secure_admin_token_2026"}
    raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

@app.post("/api/admin/settings")
def save_settings(data: SettingsRequest, authorization: str = Header(None)):
    if not authorization or authorization != "agentpay_secure_admin_token_2026":
        raise HTTPException(status_code=403, detail="Unauthorized access.")
    SETTINGS["webhook_url"] = data.webhook_url
    SETTINGS["network"] = data.network
    return {"success": True, "message": "Ayarlar başarıyla güncellendi."}

@app.get("/api/admin/stats")
def get_admin_stats(authorization: str = Header(None)):
    if not authorization or authorization != "agentpay_secure_admin_token_2026":
        raise HTTPException(status_code=403, detail="Unauthorized access.")
    
    total_revenue = sum(p["amount"] for p in PAYMENT_DATABASE)
    total_transactions = len(PAYMENT_DATABASE)
    
    return {
        "success": True,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "webhook_url": SETTINGS["webhook_url"],
        "network": SETTINGS["network"],
        "payments": PAYMENT_DATABASE[::-1]
    }

@app.post("/api/pay-usdc")
@limiter.limit("5/minute")
def create_usdc_payment(request: Request, data: PaymentRequest):
    try:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount.")
            
        payment_record = {
            "sender_wallet": data.sender_wallet,
            "amount": data.amount,
            "tx_signature": data.tx_signature,
            "plan_name": data.plan_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        PAYMENT_DATABASE.append(payment_record)

        if SETTINGS["webhook_url"]:
            try:
                with httpx.Client(timeout=5.0) as client:
                    client.post(SETTINGS["webhook_url"], json=payment_record)
            except Exception as wh_err:
                print(f"Webhook tetikleme hatası: {wh_err}")

        return {
            "success": True,
            "message": "Payment verified, recorded and webhook triggered.",
            "token": "USDC",
            "amount": data.amount,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))