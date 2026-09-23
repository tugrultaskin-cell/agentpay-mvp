from cdp import Cdp, Wallet

# Coinbase Developer Platform (CDP) API anahtarları ile yapılandırma
# (CDP Portalından alınacak API Key ve Private Key buraya tanımlanır)
# Cdp.configure("YOUR_API_KEY_NAME", "YOUR_API_PRIVATE_KEY")

def create_agent_wallet():
    """
    Yapay zeka ajanı için Base Sepolia ağında otonom cüzdan oluşturur.
    """
    wallet = Wallet.create("base-sepolia")
    print(f"🤖 Ajan Cüzdanı Başarıyla Oluşturuldu: {wallet.default_address.address_id}")
    return wallet

def fund_and_pay_service(wallet, recipient_address: str, amount_usdc: float):
    """
    Ajanın cüzdanından hedef satıcı adresine USDC mikro ödemesi gerçekleştirir.
    """
    print(f"💧 Ajan cüzdanına test USDC faucet talep ediliyor...")
    faucet_tx = wallet.faucet("usdc")
    faucet_tx.wait()
    
    print(f"💸 {amount_usdc} USDC Otonom Olarak Transfer Ediliyor...")
    # Gasless (ücretsiz gaz) transfer desteği ile USDC gönderimi
    transfer = wallet.transfer(amount_usdc, "usdc", recipient_address, gasless=True).wait()
    
    print(f"✅ Transfer Tamamlandı! İşlem Hash: {transfer.transaction_hash}")
    return transfer.transaction_hash