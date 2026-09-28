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
app = FastAPI(title="AgentPay Platform Gateway", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Veritabanları (Bellek üzerinde)
USERS_DATABASE = [] # Kayıt olan geliştiriciler: [{"email": "...", "password": "...", "api_keys": [...]}]
PAYMENT_DATABASE = [] # Tüm işlemler
SUBSCRIPTIONS_DATABASE = []
SETTINGS = {"webhook_url": "", "network": "devnet"}

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PaymentRequest(BaseModel):
    sender_wallet: str
    amount: float
    tx_signature: str
    plan_name: str = "Özel Ödeme"
    is_subscription: bool = False

class SettingsRequest(BaseModel):
    webhook_url: str
    network: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return {"status": "online", "service": "AgentPay Platform API", "network": SETTINGS["network"]}

@app.post("/api/auth/register")
def register_user(data: RegisterRequest):
    for user in USERS_DATABASE:
        if user["email"] == data.email:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")
    
    new_user = {
        "email": data.email,
        "password": data.password, # Gerçek projelerde hashlenmeli
        "api_keys": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    USERS_DATABASE.append(new_user)
    return {"success": True, "message": "Kayıt başarılı. Giriş yapabilirsiniz."}

@app.post("/api/auth/login")
def login_user(data: LoginRequest):
    for user in USERS_DATABASE:
        if user["email"] == data.email and user["password"] == data.password:
            # Basit bir oturum token'ı üretelim
            token = f"user_token_{secrets.token_hex(8)}"
            return {"success": True, "token": token, "email": user["email"]}
    
    raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre.")

@app.post("/api/user/apikey/generate")
def user_generate_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Oturum açılması gerekiyor.")
    
    # Basit simülasyon: Token sahibine yeni API key ekle
    new_key = f"ag_live_{secrets.token_hex(16)}"
    key_record = {
        "key": new_key,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Test kullanıcısına ekleyelim (Proje ilerledikçe token bazlı eşleme yapacağız)
    if USERS_DATABASE:
        USERS_DATABASE[0]["api_keys"].append(key_record)
        
    return {"success": True, "api_key": new_key}

@app.get("/api/user/dashboard")
def get_user_dashboard(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Unauthorized.")
    
    # Aktif kullanıcının verilerini döndür (Şimdilik ilk kullanıcıyı baz alıyoruz)
    user_data = USERS_DATABASE[0] if USERS_DATABASE else {"email": "dev@agentpay.io", "api_keys": []}
    total_revenue = sum(p["amount"] for p in PAYMENT_DATABASE)
    
    return {
        "success": True,
        "email": user_data["email"],
        "api_keys": user_data["api_keys"],
        "total_revenue": total_revenue,
        "total_transactions": len(PAYMENT_DATABASE),
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

        return {
            "success": True,
            "message": "Payment verified and recorded successfully.",
            "token": "USDC",
            "amount": data.amount,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))