<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentPay - Solana Tabanlı Web3 Ödeme Altyapısı</title>
    <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.js"></script>
    <style>
        :root { --bg: #0f172a; --card-bg: #1e293b; --primary: #9333ea; --primary-hover: #7e22ce; --text: #f8fafc; --muted: #94a3b8; --accent: #22c55e; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 50px; border-bottom: 1px solid #334155; }
        .logo { font-size: 24px; font-weight: bold; color: #c084fc; cursor: pointer; }
        nav a { color: var(--muted); text-decoration: none; margin-left: 20px; font-weight: 500; cursor: pointer; }
        nav a:hover { color: var(--text); }
        .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; flex: 1; width: 100%; box-sizing: border-box; }
        .hero { text-align: center; margin-bottom: 40px; }
        h1 { font-size: 38px; margin-bottom: 10px; background: linear-gradient(to right, #c084fc, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p.subtitle { color: var(--muted); font-size: 16px; max-width: 600px; margin: 0 auto; }
        
        /* Pricing Cards */
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .price-card { background: var(--card-bg); border: 1px solid #334155; border-radius: 16px; padding: 25px; text-align: center; transition: transform 0.2s, border-color 0.2s; cursor: pointer; }
        .price-card:hover { transform: translateY(-5px); border-color: #c084fc; }
        .price-card.selected { border-color: #c084fc; background: #26334d; }
        .price-card h3 { margin-top: 0; color: #c084fc; }
        .price { font-size: 28px; font-weight: bold; margin: 15px 0; }
        
        .checkout-box { background: var(--card-bg); padding: 30px; border-radius: 16px; border: 1px solid #334155; max-width: 500px; margin: 0 auto; text-align: left; }
        button { background: var(--primary); color: white; border: none; padding: 14px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 15px; transition: background 0.2s; }
        button:hover { background: var(--primary-hover); }
        .btn-success { background: var(--accent); }
        .btn-success:hover { background: #16a34a; }
        #status { margin-top: 15px; font-size: 14px; color: #38bdf8; text-align: center; word-break: break-all; }
        
        /* Dashboard Section */
        #dashboardSection { display: none; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: var(--card-bg); border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }
        th { background: #1b263b; color: #c084fc; }
        
        footer { text-align: center; padding: 20px; color: var(--muted); border-top: 1px solid #334155; font-size: 14px; }
    </style>
</head>
<body>

    <header>
        <div class="logo" onclick="switchTab('home')">⚡ AgentPay</div>
        <nav>
            <a onclick="switchTab('home')">Paketler & Ödeme</a>
            <a onclick="switchTab('dashboard')">Yönetici Paneli (Dashboard)</a>
        </nav>
    </header>

    <div class="container">
        <!-- ANA SAYFA / PAKETLER -->
        <div id="homeSection">
            <div class="hero">
                <h1>Yapay Zeka ve SaaS İçin Anında Ödeme</h1>
                <p class="subtitle">İhtiyacınıza uygun paketi seçin, Solana ağı üzerinden anında USDC ile ödemenizi gerçekleştirin.</p>
            </div>

            <div class="pricing-grid">
                <div class="price-card selected" onclick="selectPlan('Başlangıç Paketi', 5, this)">
                    <h3>Başlangıç</h3>
                    <div class="price">5 USDC</div>
                    <p style="color: var(--muted); font-size: 14px;">Bireysel geliştiriciler ve küçük testler için ideal.</p>
                </div>
                <div class="price-card" onclick="selectPlan('Pro SaaS Paketi', 25, this)">
                    <h3>Pro SaaS</h3>
                    <div class="price">25 USDC</div>
                    <p style="color: var(--muted); font-size: 14px;">Aktif projeler ve otomasyon araçları için.</p>
                </div>
                <div class="price-card" onclick="selectPlan('Kurumsal Paket', 100, this)">
                    <h3>Kurumsal</h3>
                    <div class="price">100 USDC</div>
                    <p style="color: var(--muted); font-size: 14px;">Yüksek hacimli AI ajanı ödemeleri için.</p>
                </div>
            </div>

            <div class="checkout-box">
                <h3 id="selectedPlanTitle" style="margin-top:0; color:#38bdf8;">Seçilen: Başlangıç Paketi (5 USDC)</h3>
                
                <button id="connectBtn" onclick="connectWallet()">Phantom Cüzdanı Bağla</button>
                <button id="payBtn" class="btn-success" onclick="sendUSDC()" style="display:none;">USDC ile Ödemeyi Tamamla</button>
                
                <div id="status"></div>
            </div>
        </div>

        <!-- YÖNETİCİ PANELİ (DASHBOARD) -->
        <div id="dashboardSection">
            <h2>Ödeme Yönetim Paneli</h2>
            <p style="color: var(--muted);">Sistem üzerinden gerçekleştirilen tüm USDC transferlerinin listesi:</p>
            <button onclick="loadPayments()" style="width: auto; padding: 8px 16px; margin-bottom: 15px;">Listeyi Yenile</button>
            <table>
                <thead>
                    <tr>
                        Gönderici Cüzdan
                        <th>Paket</th>
                        <th>Tutar</th>
                        <th>İşlem Hash (TX)</th>
                        <th>Zaman</th>
                    </tr>
                </thead>
                <tbody id="paymentTableBody">
                    <tr><td colspan="5" style="text-align: center; color: var(--muted);">Henüz ödeme kaydı bulunmuyor.</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        &copy; 2026 AgentPay MVP. Tüm hakları saklıdır.
    </footer>

    <script>
        let userWallet = null;
        let currentPlan = "Başlangıç Paketi";
        let currentAmount = 5;

        function selectPlan(name, amount, element) {
            document.querySelectorAll('.price-card').forEach(c => c.classList.remove('selected'));
            element.classList.add('selected');
            currentPlan = name;
            currentAmount = amount;
            document.getElementById("selectedPlanTitle").innerText = `Seçilen: ${name} (${amount} USDC)`;
        }

        function switchTab(tab) {
            if(tab === 'home') {
                document.getElementById("homeSection").style.display = "block";
                document.getElementById("dashboardSection").style.display = "none";
            } else {
                document.getElementById("homeSection").style.display = "none";
                document.getElementById("dashboardSection").style.display = "block";
                loadPayments();
            }
        }

        async function connectWallet() {
            const provider = window.phantom?.solana;
            if (provider?.isPhantom) {
                try {
                    const response = await provider.connect();
                    userWallet = response.publicKey;
                    document.getElementById("status").innerText = "Bağlandı: " + userWallet.toString().slice(0, 4) + "..." + userWallet.toString().slice(-4);
                    document.getElementById("connectBtn").style.display = "none";
                    document.getElementById("payBtn").style.display = "block";
                } catch (err) {
                    console.error(err);
                    document.getElementById("status").innerText = "Cüzdan bağlantısı reddedildi.";
                }
            } else {
                alert("Phantom cüzdanı bulunamadı!");
                window.open("https://phantom.app/", "_blank");
            }
        }

        async function sendUSDC() {
            if (!userWallet) {
                alert("Önce cüzdanınızı bağlayın!");
                return;
            }

            document.getElementById("status").innerText = "İşlem hazırlanıyor...";

            try {
                const connection = new solanaWeb3.Connection(solanaWeb3.clusterApiUrl('devnet'), 'confirmed');
                const recipientPubKey = new solanaWeb3.PublicKey("CQcfG1KKaydJEbzuTC4ULdeGtTdhq6jtcSrPQRSGTD4q");

                const transaction = new solanaWeb3.Transaction().add(
                    solanaWeb3.SystemProgram.transfer({
                        fromPubkey: userWallet,
                        toPubkey: recipientPubKey,
                        lamports: currentAmount * solanaWeb3.LAMPORTS_PER_SOL
                    })
                );

                const { blockhash } = await connection.getLatestBlockhash();
                transaction.recentBlockhash = blockhash;
                transaction.feePayer = userWallet;

                const signed = await window.phantom.solana.signTransaction(transaction);
                const signature = await connection.sendRawTransaction(signed.serialize());
                
                document.getElementById("status").innerText = "Ödeme Gönderildi! Kaydediliyor...";
                
                await fetch("/api/pay-usdc", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        sender_wallet: userWallet.toString(),
                        amount: currentAmount,
                        tx_signature: signature,
                        plan_name: currentPlan
                    })
                });

                document.getElementById("status").innerText = "Ödeme başarıyla tamamlandı!";
                alert("Ödeme başarıyla onaylandı ve sisteme işlendi!");

            } catch (error) {
                console.error(error);
                document.getElementById("status").innerText = "Hata: " + (error.message || error);
            }
        }

        async function loadPayments() {
            try {
                const res = await fetch("/api/payments");
                const data = await res.json();
                const tbody = document.getElementById("paymentTableBody");
                tbody.innerHTML = "";

                if(data.payments.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--muted);">Henüz ödeme kaydı bulunmuyor.</td></tr>`;
                    return;
                }

                data.payments.forEach(p => {
                    const row = `<tr>
                        <td>${p.sender_wallet.slice(0, 6)}...${p.sender_wallet.slice(-4)}</td>
                        <td>${p.plan_name}</td>
                        <td>${p.amount} USDC</td>
                        <td><a href="https://explorer.solana.com/tx/${p.tx_signature}?cluster=devnet" target="_blank" style="color: #38bdf8;">${p.tx_signature.slice(0, 8)}...</a></td>
                        <td>${p.timestamp}</td>
                    </tr>`;
                    tbody.innerHTML += row;
                });
            } catch(e) {
                console.error("Ödemeler yüklenemedi", e);
            }
        }
    </script>
</body>
</html>