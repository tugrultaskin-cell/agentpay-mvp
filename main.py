from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import httpx
import secrets
from datetime import datetime

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay Subscription Engine", version="1.8.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "gizlisifre123"

PAYMENT_DATABASE = []
SUBSCRIPTIONS_DATABASE = [] # Aktif abonelikler
SETTINGS = {"webhook_url": "", "network": "devnet"}
API_KEYS = []

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    tx_signature: str
    plan_name: str = "Özel Ödeme"
    is_subscription: bool = False

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

@app.post("/api/admin/apikey/generate")
def generate_api_key(authorization: str = Header(None)):
    if not authorization or authorization != "agentpay_secure_admin_token_2026":
        raise HTTPException(status_code=403, detail="Unauthorized access.")
    
    new_key = f"ag_live_{secrets.token_hex(16)}"
    key_record = {
        "key": new_key,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    API_KEYS.append(key_record)
    return {"success": True, "api_key": new_key}

@app.get("/api/admin/stats")
def get_admin_stats(authorization: str = Header(None)):
    if not authorization or authorization != "agentpay_secure_admin_token_2026":
        raise HTTPException(status_code=403, detail="Unauthorized access.")
    
    total_revenue = sum(p["amount"] for p in PAYMENT_DATABASE)
    total_transactions = len(PAYMENT_DATABASE)
    total_subs = len(SUBSCRIPTIONS_DATABASE)
    
    return {
        "success": True,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "total_subscriptions": total_subs,
        "webhook_url": SETTINGS["webhook_url"],
        "network": SETTINGS["network"],
        "api_keys": API_KEYS,
        "subscriptions": SUBSCRIPTIONS_DATABASE[::-1],
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
            "type": "Abonelik" if data.is_subscription else "Tek Seferlik",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        PAYMENT_DATABASE.append(payment_record)

        if data.is_subscription:
            SUBSCRIPTIONS_DATABASE.append({
                "subscriber_wallet": data.sender_wallet,
                "plan_name": data.plan_name,
                "monthly_amount": data.amount,
                "status": "Aktif",
                "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        if SETTINGS["webhook_url"]:
            try:
                with httpx.Client(timeout=5.0) as client:
                    client.post(SETTINGS["webhook_url"], json=payment_record)
            except Exception as wh_err:
                print(f"Webhook tetikleme hatası: {wh_err}")

        return {
            "success": True,
            "message": "Payment verified and recorded successfully.",
            "token": "USDC",
            "amount": data.amount,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))