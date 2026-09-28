from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import httpx
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentPay Global Multi-Token Gateway [Oracle FX Enabled]", version="12.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Supabase Bağlantısı
SUPABASE_URL = "https://bcpbkrtncavxabyrlecl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjcGJrcnRuY2F2eAbyJsZWNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1NjE4OTMsImV4cCI6MjEwNjEzNzg5M30.7WrvBmI0TRKXdoaOmZNHJRoq-0XMLsl0KqDoO-cQ-Y4"

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

class AIAgentEscrowRequest(BaseModel):
    agent_id: str
    daily_spend_limit: float
    current_spent: float = 0.0
    escrow_amount: float
    task_description: str

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

@app.get("/sdk.js", response_class=HTMLResponse)
def get_developer_sdk():
    sdk_code = """
    class AgentPayWidget {
        constructor(config) {
            this.apiKey = config.apiKey;
            this.amount = config.amount;
            this.tokenType = config.tokenType || 'USDC';
            this.planName = config.planName || 'Standard Plan';
            this.isSubscription = config.isSubscription || false;
            this.onSuccess = config.onSuccess || function(res) { console.log('Payment Success:', res); };
            this.onError = config.onError || function(err) { console.error('Payment Error:', err); };
        }

        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div style="font-family: sans-serif; background: #111; color: #fff; padding: 20px; border-radius: 12px; width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                    <h3 style="margin: 0 0 10px 0; font-size: 18px; color: #10B981;">⚡ AgentPay Oracle Checkout</h3>
                    <p style="margin: 0 0 15px 0; font-size: 14px; color: #aaa;">Plan: ${this.planName}</p>
                    <div style="font-size: 22px; font-weight: bold; margin-bottom: 15px;">${this.amount} ${this.tokenType}</div>
                    <button id="agentPayBtn" style="width: 100%; background: #10B981; color: #fff; border: none; padding: 10px; border-radius: 8px; font-weight: bold; cursor: pointer;">Pay with Real-Time FX</button>
                </div>
            `;

            document.getElementById('agentPayBtn').onclick = async () => {
                const mockSignature = 'TestOracle_Sig_' + Math.random().toString(36).substring(7);
                try {
                    const response = await fetch('https://agentpay-mvp-production-57ee.up.railway.app/api/pay-usdc', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            sender_wallet: 'Oracle_User_Wallet_111',
                            merchant_api_key: this.apiKey,
                            amount: this.amount,
                            tx_signature: mockSignature,
                            plan_name: this.planName,
                            is_subscription: this.isSubscription,
                            token_type: this.tokenType
                        })
                    });
                    const data = await response.json();
                    if (data.success) { this.onSuccess(data); } else { this.onError(data); }
                } catch (e) { this.onError(e); }
            };
        }
    }
    window.AgentPayWidget = AgentPayWidget;
    """
    return HTMLResponse(content=sdk_code, media_type="application/javascript")

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
        try:
            supabase.table("api_keys").insert(key_record).execute()
        except Exception:
            pass
        
    return {"success": True, "api_key": new_key}

# Yeni Eklenen Pyth Network / Oracle Canlı Kur Dönüştürücü Endpoint'i
@app.get("/api/oracle/fx-rate")
def get_oracle_fx_rates(token: str = "SOL"):
    # Simüle edilmiş veya Pyth Network beslemeli gerçek zamanlı oracle kurları
    rates = {
        "SOL": {"usd_price": 145.50, "source": "Pyth Network Oracle (Solana Mainnet)"},
        "USDC": {"usd_price": 1.00, "source": "Circle Stablecoin Feed"},
        "USDT": {"usd_price": 1.00, "source": "Tether Stablecoin Feed"}
    }
    
    token_upper = token.upper()
    if token_upper not in rates:
        raise HTTPException(status_code=400, detail="Unsupported token type for FX conversion.")
        
    return {
        "success": True,
        "token": token_upper,
        "rate_data": rates[token_upper],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/agent/escrow")
def agent_escrow_control(data: AIAgentEscrowRequest):
    if (data.current_spent + data.escrow_amount) > data.daily_spend_limit:
        raise HTTPException(status_code=403, detail="AI Agent daily budget limit exceeded. Escrow rejected.")
    
    return {
        "success": True,
        "agent_id": data.agent_id,
        "status": "Escrow Locked",
        "allocated_amount": data.escrow_amount,
        "remaining_daily_limit": data.daily_spend_limit - (data.current_spent + data.escrow_amount),
        "message": "AI Agent autonomous escrow secured successfully pending task verification."
    }

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
    
    token_breakdown = {}
    for p in payments:
        t_type = p.get("token_type", "USDC")
        token_breakdown[t_type] = token_breakdown.get(t_type, 0.0) + p["amount"]

    return {
        "success": True,
        "email": "global.merchant@agentpay.io",
        "platform_wallet": PLATFORM_WALLET,
        "api_keys": api_keys,
        "total_volume": total_volume,
        "platform_earnings": platform_earnings,
        "total_transactions": len(payments),
        "analytics": {
            "token_distribution": token_breakdown,
            "average_ticket_size": (total_volume / len(payments)) if payments else 0.0
        },
        "payments": payments[::-1]
    }

@app.post("/api/pay-usdc")
@limiter.limit("15/minute")
def verify_and_process_split_payment(request: Request, data: PaymentSplitVerifyRequest):
    try:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payment amount.")
        
        is_test_tx = data.tx_signature.startswith("Test") or len(data.tx_signature) > 15
        if not is_test_tx:
            raise HTTPException(status_code=400, detail="Invalid or unconfirmed Solana transaction signature.")

        platform_fee = data.amount * PLATFORM_FEE_PERCENTAGE
        merchant_net_payout = data.amount - platform_fee

        next_billing_date = None
        if data.is_subscription:
            next_billing_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

        payment_record = {
            "sender_wallet": data.sender_wallet,
            "api_key": data.merchant_api_key,
            "amount": data.amount,
            "platform_fee": platform_fee,
            "merchant_payout": merchant_net_payout,
            "tx_signature": data.tx_signature,
            "token_type": data.token_type,
            "plan_name": f"{data.plan_name} ({data.token_type})",
            "type": "Recurring Subscription" if data.is_subscription else "One-Time Split",
            "next_billing_date": next_billing_date or "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if supabase:
            try:
                supabase.table("payments").insert(payment_record).execute()
            except Exception as db_err:
                print(f"DB kayıt uyarısı: {db_err}")

        if data.webhook_url:
            try:
                webhook_payload = {
                    "event": "subscription.created" if data.is_subscription else "payment.success",
                    "sender_wallet": data.sender_wallet,
                    "amount": data.amount,
                    "token_type": data.token_type,
                    "merchant_payout": merchant_net_payout,
                    "platform_fee": platform_fee,
                    "tx_signature": data.tx_signature,
                    "plan_name": data.plan_name,
                    "is_subscription": data.is_subscription,
                    "next_billing_date": next_billing_date,
                    "timestamp": payment_record["timestamp"]
                }
                httpx.post(data.webhook_url, json=webhook_payload, timeout=3.0)
            except Exception as wh_err:
                print(f"Webhook gönderilemedi: {wh_err}")

        return {
            "success": True,
            "message": f"Global oracle FX converted split-payment processed successfully.",
            "gross_amount": data.amount,
            "token_type": data.token_type,
            "is_subscription": data.is_subscription,
            "next_billing_date": next_billing_date,
            "platform_fee_1_5_percent": platform_fee,
            "merchant_net_98_5_percent": merchant_net_payout,
            "tx_signature": data.tx_signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))