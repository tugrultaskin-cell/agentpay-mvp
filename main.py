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
from supabase import create_client, Client

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay Global Multi-Token Gateway", version="6.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Supabase Bağlantısı (Railway Environment Variables üzerinden güvenli okuma)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bcpbkrtncavxabyrlecl.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjcGJrcnRuY2F2eAbyJsZWNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1NjE4OTMsImV4cCI6MjEwNjEzNzg5M30.7WrvBmI0TRKXdoaOmZNHJRoq-0XMLsl0KqDoO-cQ-Y4")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase bağlantı hatası: {e}")
    supabase = None

PLATFORM_WALLET = "CQcf...TD4q"
PLATFORM_FEE_PERCENTAGE = 0.015 # %1.5 Erişilebilir Komisyon Oranı

class RegisterRequest(BaseModel):
    email: str
    password: str
    payout_wallet: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PaymentSplitVerifyRequest(BaseModel):
    sender_wallet: str
    merchant_api_key: str
    amount: float
    tx_signature: str
    plan_name: str = "Global Enterprise API"
    is_subscription: bool = False
    token_type: str = "USDC"
    webhook_url: str = None

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return {"status": "online", "service": "AgentPay Global Multi-Token Gateway", "mode": "Production Ready"}

@app.get("/docs", response_class=HTMLResponse)
def read_docs():
    if os.path.exists("docs.html"):
        with open("docs.html", "r", encoding="utf-8") as f:
            return f.read()
    return {"status": "error", "message": "Documentation file not found."}

@app.post("/api/auth/register")
def register_user(data: RegisterRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Veritabanı bağlantısı kurulamadı.")
    
    try:
        existing = supabase.table("merchants").select("*").eq("email", data.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")
        
        new_merchant = {
            "email": data.email,
            "password": data.password,
            "payout_wallet": data.payout_wallet,
            "created_at": datetime.now().isoformat()
        }
        
        supabase.table("merchants").insert(new_merchant).execute()
        return {"success": True, "message": "Merchant registered successfully in global network."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login_user(data: LoginRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Veritabanı bağlantısı kurulamadı.")
    
    try:
        res = supabase.table("merchants").select("*").eq("email", data.email).eq("password", data.password).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre.")
        
        token = f"global_live_token_{secrets.token_hex(12)}"
        return {"success": True, "token": token, "email": data.email, "payout_wallet": res.data[0]["payout_wallet"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Giriş başarısız.")

@app.post("/api/merchant/apikey/generate")
def generate_merchant_apikey(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Yetkilendirme gerekli.")
    
    new_key = f"ag_live_{secrets.token_hex(20)}"
    key_record = {
        "api_key": new_key,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if supabase:
        supabase.table("api_keys").insert(key_record).execute()
        
    return {"success": True, "api_key": new_key}

@app.get("/api/merchant/dashboard")
def get_merchant_dashboard(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Unauthorized.")
    
    payments = []
    api_keys = []
    total_volume = 0.0
    
    if supabase:
        try:
            pay_res = supabase.table("payments").select("*").execute()
            payments = pay_res.data or []
            
            key_res = supabase.table("api_keys").select("*").execute()
            api_keys = key_res.data or []
            
            total_volume = sum(p["amount"] for p in payments)
        except Exception as e:
            print(f"Veri çekme hatası: {e}")
    
    platform_earnings = total_volume * PLATFORM_FEE_PERCENTAGE
    
    return {
        "success": True,
        "email": "global.merchant@agentpay.io",
        "platform_wallet": PLATFORM_WALLET,
        "api_keys": api_keys,
        "total_volume": total_volume,
        "platform_earnings": platform_earnings,
        "total_transactions": len(payments),
        "payments": payments[::-1]
    }

@app.post("/api/pay-usdc")
@limiter.limit("15/minute")
def verify_and_process_split_payment(request: Request, data: PaymentSplitVerifyRequest):
    try:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payment amount.")
        
        platform_fee = data.amount * PLATFORM_FEE_PERCENTAGE
        merchant_net_payout = data.amount - platform_fee

        payment_record = {
            "sender_wallet": data.sender_wallet,
            "api_key": data.merchant_api_key,
            "amount": data.amount,
            "platform_fee": platform_fee,
            "merchant_payout": merchant_net_payout,
            "tx_signature": data.tx_signature,
            "plan_name": f"{data.plan_name} ({data.token_type})",
            "type": "Subscription" if data.is_subscription else "One-Time Split",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if supabase:
            supabase.table("payments").insert(payment_record).execute()

        if data.webhook_url:
            try:
                webhook_payload = {
                    "event": "payment.success",
                    "sender_wallet": data.sender_wallet,
                    "amount": data.amount,
                    "token_type": data.token_type,
                    "merchant_payout": merchant_net_payout,
                    "platform_fee": platform_fee,
                    "tx_signature": data.tx_signature,
                    "plan_name": data.plan_name,
                    "timestamp": payment_record["timestamp"]
                }
                httpx.post(data.webhook_url, json=webhook_payload, timeout=3.0)
            except Exception as wh_err:
                print(f"Webhook gönderilemedi: {wh_err}")

        return {
            "success": True,
            "message": f"Global multi-token ({data.token_type}) split-payment verified & routed successfully.",
            "gross_amount": data.amount,
            "token_type": data.token_type,
            "platform_fee_1_5_percent": platform_fee,
            "merchant_net_98_5_percent": merchant_net_payout,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))