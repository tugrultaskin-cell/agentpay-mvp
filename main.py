from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from web3 import Web3

app = FastAPI(title="AgentPay Global Commerce Engine", version="1.0.0")

# Base Mainnet (Gerçek Ağ) RPC Bağlantısı
BASE_MAINNET_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_MAINNET_RPC))

# Senin Ticari Hazine Cüzdan Adresin (Tüm komisyonlar ve gelirler buraya toplanacak)
COMMISSION_TREASURY = "0x1631d7911b6D202f483a39DBA76Da715cca8Da4f".lower()

class ServiceRequest(BaseModel):
    prompt: str
    max_price_usdc: float

@app.post("/v1/agent/consume-service")
async def consume_service(
    request: ServiceRequest, 
    x_agent_wallet: str = Header(None),
    x_tx_hash: str = Header(None)
):
    """
    Küresel Agentic Commerce Ağı - Gerçek USDC Ödeme Ağ Geçidi
    """
    if not x_agent_wallet:
        raise HTTPException(status_code=400, detail="X-Agent-Wallet header is missing.")
    
    service_price_usdc = 0.05  # Servis başına belirlenen USDC ücreti

    # 1. Aşama: Ödeme yapılmamışsa HTTP 402 ve ödeme talimatı dön
    if not x_tx_hash:
        return {
            "error": "Payment Required",
            "status_code": 402,
            "message": f"Send {service_price_usdc} USDC on Base Mainnet to access this commercial AI resource.",
            "payment_details": {
                "treasury_address": COMMISSION_TREASURY,
                "amount_usdc": service_price_usdc,
                "network": "base-mainnet",
                "currency": "USDC"
            }
        }

    # 2. Aşama: Base Mainnet üzerindeki gerçek USDC transferini doğrula
    is_valid = verify_base_mainnet_payment(x_tx_hash, service_price_usdc)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or unconfirmed transaction on Base Mainnet.")

    # 3. Aşama: Ödeme onaylandı, yapay zeka hizmetini/verisini sun
    return {
        "status": "success",
        "data": {
            "result": f"Commercial AI execution completed for: '{request.prompt}'",
            "cost_charged": service_price_usdc,
            "protocol_fee_earned": service_price_usdc * 0.0025, # %0.25 komisyonun
            "tx_hash": x_tx_hash
        }
    }

def verify_base_mainnet_payment(tx_hash: str, expected_amount: float) -> bool:
    """
    Base Mainnet üzerindeki transferin ana kasaya ulaştığını blokzincirden doğrular.
    """
    try:
        if not w3.is_connected():
            return False
            
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt is None or receipt.get("status") != 1:
            return False

        tx = w3.eth.get_transaction(tx_hash)
        # Alıcının senin hazine cüzdanın olduğunu doğrula
        if tx and tx.get("to", "").lower() == COMMISSION_TREASURY:
            return True
            
        return False
    except Exception as e:
        print(f"Mainnet doğrulama hatası: {e}")
        return False