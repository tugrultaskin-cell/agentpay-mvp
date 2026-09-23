import requests
import json

API_URL = "http://localhost:8000/v1/agent/consume-service"

def run_client_agent():
    print("🤖 Alıcı Ajan başlatıldı: Veri arayışında...")
    
    headers = {
        "X-Agent-Wallet": "0xClientAgentWalletAddress987654321"
    }
    payload = {
        "prompt": "Get real-time market sentiment analysis for AI tokens.",
        "max_price_usdc": 0.05
    }

    # 1. Adım: Ödemesiz istek at (HTTP 402'yi tetikle)
    print("📡 Satıcı ajana istek gönderiliyor...")
    response = requests.post(API_URL, json=payload, headers=headers)
    
    if response.status_code == 200 and response.json().get("status_code") == 402:
        error_data = response.json()
        print(f"\n⚠️ [HTTP 402 Alındı]: {error_data['message']}")
        payment_info = error_data["payment_details"]
        print(f"💰 Ödenmesi Gereken: {payment_info['amount_usdc']} USDC -> Alıcı: {payment_info['recipient_address']}")
        
        # 2. Adım: Base Sepolia ağında cüzdandan otomatik transfer yapıldığı simüle ediliyor
        print("\n🔄 Base Sepolia ağı üzerinde akıllı cüzdan otomatik transferi tetikleniyor...")
        mock_tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        print(f"✅ İşlem Başarılı! Tx Hash: {mock_tx_hash}")

        # 3. Adım: Ödeme kanıtı (tx_hash) ile tekrar istek at
        headers["X-Tx-Hash"] = mock_tx_hash
        print("\n🚀 Ödeme kanıtı ile servis tekrar çağrılıyor...")
        
        final_response = requests.post(API_URL, json=payload, headers=headers)
        print("\n🎉 Sonuç (Servis Başarıyla Alındı):")
        print(json.dumps(final_response.json(), indent=4, ensure_ascii=False))

if __name__ == "__main__":
    run_client_agent()
