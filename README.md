# AI-Powered Indonesian Stock Prediction & Scalping Assistant (BEI / IDX)

Sistem analitik kuantitatif, screening pasar, prediksi Deep Learning (LSTM & BiLSTM), penghasil sinyal scalping, manajemen risiko mikrostruktur, backtesting walk-forward, dan simulasi paper trading untuk saham Bursa Efek Indonesia (BEI).

---

## 📌 Fitur Utama

1. **Full IDX Stock Coverage & Market Explorer**:
   - Cakupan master data lengkap seluruh emiten Bursa Efek Indonesia (BEI) berbasis **12 Sektor Resmi IDX-IC** (*Energy, Basic Materials, Industrials, Consumer Non-Cyclicals, Consumer Cyclicals, Healthcare, Financials, Properties & Real Estate, Technology, Infrastructures, Transportation & Logistic, Listed Investment Products*).
   - Klasifikasi papan pencatatan: *Utama (Main), Pengembangan (Development), Akselerasi (Acceleration), Ekonomi Baru (New Economy)*.
   - Pemisahan status emiten secara tegas: *Active, Suspended, Newly Listed, Delisted*.
   - **Market Explorer**: Halaman penjelajah emiten dengan pencarian ticker/nama perusahaan, multi-filter sektor & status, pengurutan, pagination (25, 50, 100 baris), watchlist, dan ekspor CSV.
2. **Full Market Scanner & AI Ranking**:
   - Pemindaian masal seluruh saham BEI atau per sektor IDX-IC dengan komputasi teknikal vektor berkecepatan tinggi.
   - Hasil pemindaian disimpan ke basis data (`MarketScanResult`) untuk kueri instan tanpa latensi berulang.
   - Integrasi ranking AI otomatis: saham momentum terbaik, akumulasi volume, tren bullish, dan peringatan saham berisiko tinggi.
3. **Market Data Provider Abstraction Layer**:
   - Mendukung integrasi mulus dengan **Invezgo API**, **Api.co.id**, **Yahoo Finance (.JK)**, dan **High-Fidelity Mock Simulator**.
   - Manajemen dinamis universe emiten BEI dengan sinkronisasi otomatis.
4. **Technical Analysis Engine**:
   - Perhitungan terverifikasi untuk RSI 14, MACD (12, 26, 9), EMA (9, 20, 50), VWAP intraday, ATR 14, Bollinger Bands, Volume MA 20, Relative Volume, Golden Cross & Death Cross, Crossovers.
5. **Machine Learning & Deep Learning (PyTorch)**:
   - **LSTM Regressor**: Memprediksi estimasi return dan volatilitas periode berikutnya.
   - **BiLSTM Classifier**: Mempelajari representasi pola sekuensial window masa lalu untuk memprediksi probabilitas kenaikan harga secara terkalibrasi tanpa data leakage.
   - Evaluasi walk-forward: MAE, RMSE, Directional Accuracy, Precision, Recall, dan F1-Score.
6. **AI Trading Decision Assistant (LLM Layer - Bagian R)**:
   - Integrasi fleksibel dengan **Google Gemini API**, **OpenAI API**, **Anthropic Claude API**, serta **High-Fidelity Mock LLM** (offline mode).
   - Menginterpretasikan data indikator teknikal, prediksi return LSTM, probabilitas BiLSTM, dan likuiditas.
   - **Rule-Based Validator Gatekeeper**: Menolak rekomendasi yang melanggar batas fraksi harga BEI, ARA/ARB, atau tidak menutup friksi biaya transaksi bursa (~0.48%).
   - **Multi-Stock AI Ranking**: Mengidentifikasi saham dengan momentum terbaik, lonjakan volume, tren bullish, dan saham berisiko tinggi.
   - **Context-Aware AI Chat Assistant**: Chatbot interaktif untuk menjawab pertanyaan seputar alasan rekomendasi, estimasi risiko, dan waktu entry.
   - **Google Colab Notebook**: Notebook khusus di `notebooks/ai_trading_decision_assistant.ipynb` dengan dukungan Colab Secrets (`userdata`).
7. **Multi-Factor Stock Screener**:
   - Filter likuiditas nilai transaksi (> Rp 1 Miliar), volume lonjakan (Relative Volume $\ge 1.2\times$), batasan spread bid-ask ($\le 2$ tick), dan pemeringkatan skor peluang scalping (0–100).
8. **Scalping Signal Engine (Decision Support)**:
   - Menghasilkan 4 status sinyal transparan: **BUY, SELL, HOLD, WATCHLIST**.
   - Dilengkapi area Entry, Stop Loss, Take Profit, Risk/Reward Ratio ($\ge 1.5$), estimasi biaya transaksi, serta kriteria pembatalan (*invalidation criteria*).
   - Deteksi keamanan batas ARA/ARB (memblokir sinyal BUY jika $< 2$ tick dari ARA).
9. **Risk Management & IDX Microstructure**:
   - Position sizing dinamis per lot (1 Lot = 100 lembar saham).
   - Penyesuaian presisi terhadap 5 kelompok fraksi harga resmi BEI (<Rp200: Rp1, Rp200–Rp500: Rp2, Rp500–Rp2000: Rp5, Rp2000–Rp5000: Rp10, $\ge$Rp5000: Rp25).
   - Pemodelan friksi biaya transaksi riil: Beli ~0.19% (broker + PPN + levy), Jual ~0.29% (broker + PPN + levy + PPh final 0.1%).
   - Circuit breaker kerugian harian (*Maximum Daily Loss Limit*).
10. **Walk-Forward Backtesting Engine**:
    - Pengujian intraday candle demi candle tanpa look-ahead bias (sinyal candle $t$, eksekusi candle $t+1$).
    - Menghitung Win Rate, Net Profit, Profit Factor, Max Drawdown, Sharpe Ratio, dan kurva ekuitas.
11. **Virtual Paper Trading Simulator**:
    - Akun portofolio virtual mandiri dengan eksekusi berbasis fraksi tick, potongan fee bursa, dan pencatatan realized/unrealized P&L.
12. **Modern SaaS Interactive Dashboard (Streamlit & Plotly)**:
    - 11 Halaman terintegrasi: *Market Overview, Market Explorer (Full IDX), Stock Screener, Full Market Scanner & AI Ranking, Stock Detail & Chart, Scalping Signals, AI Decision & Chatbot, Portfolio, Backtesting, Model Performance, Settings*.
    - Dukungan Light Mode & Dark Mode dengan semantic trading colors (BUY Hijau, SELL Merah, HOLD Kuning).
13. **FastAPI REST Backend**:
    - Endpoints untuk quotes, screening, market explorer, coverage statistics, full market scan, signal generation, dan order eksekusi paper trading.

---

## 📂 Struktur Proyek

```
Screener Saham/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                 # REST API FastAPI Endpoints
│   └── dashboard/
│       ├── __init__.py
│       └── app.py                  # Streamlit Multi-Page Interactive Dashboard
├── config/
│   ├── __init__.py
│   ├── idx_constants.py            # Aturan Fraksi Harga, ARA/ARB, Jam Bursa, Biaya Fee
│   └── settings.py                 # Pengaturan Aplikasi & Konfigurasi .env
├── database/
│   ├── __init__.py
│   ├── connection.py               # Engine SQLAlchemy & Session Factory (SQLite/PostgreSQL)
│   └── models.py                   # Skema Tabel Relasional ORM
├── src/
│   ├── data_collection/            # Ingestion Data & Provider Layer
│   │   ├── base_provider.py        # Abstract Interface Provider
│   │   ├── idx_master_data.py      # Master Universe 12 Sektor Resmi IDX-IC
│   │   ├── invezgo_provider.py     # Integrasi Invezgo API
│   │   ├── apicoid_provider.py     # Integrasi Api.co.id
│   │   ├── yfinance_provider.py    # Fallback Yahoo Finance (.JK)
│   │   ├── mock_provider.py        # Mock Simulator Data Pasar BEI
│   │   └── universe_manager.py     # Sinkronisasi Universe Emiten Aktif/Suspend
│   ├── technical_analysis/
│   │   ├── __init__.py
│   │   └── indicators.py           # Perhitungan Indikator Vektorisasi
│   ├── machine_learning/
│   │   ├── __init__.py
│   │   ├── feature_engineering.py  # Sequence Creator & Normalizer
│   │   ├── models.py               # PyTorch LSTM Regressor & BiLSTM Classifier
│   │   └── trainer.py              # Walk-Forward Trainer & Inference Engine
│   ├── ai_assistant/               # AI LLM Layer (Gemini, Claude, OpenAI, Mock)
│   │   ├── __init__.py
│   │   ├── llm_provider.py         # Multi-provider LLM Adapter
│   │   ├── prompts.py              # System & Context-Aware Prompt Templates
│   │   ├── validator.py            # Quantitative Rule-Based Gatekeeper
│   │   ├── decision_engine.py      # AI Decision Engine & Multi-Stock Ranking
│   │   └── chat_assistant.py       # Conversational Market Assistant
│   ├── stock_screener/
│   │   ├── __init__.py
│   │   ├── screener.py             # Multi-factor Stock Screener & Scoring
│   │   └── full_market_scanner.py  # Full Market & Sector Scanner + Caching
│   ├── signal_engine/
│   │   ├── __init__.py
│   │   └── engine.py               # Ensemble Scalping Signal Generator
│   ├── risk_management/
│   │   ├── __init__.py
│   │   └── risk_manager.py         # Position Sizing & Fee Calculation
│   ├── backtesting/
│   │   ├── __init__.py
│   │   └── engine.py               # Event-Driven Walk-Forward Backtest
│   └── paper_trading/
│       ├── __init__.py
│       └── account.py              # Portofolio Virtual & Order Execution
├── notebooks/
│   └── ai_trading_decision_assistant.ipynb  # Google Colab Notebook Interaktif
├── tests/
│   ├── test_idx_constants.py       # Pengujian Fraksi Harga & Batas ARA/ARB
│   ├── test_technical_analysis.py  # Pengujian Indikator Teknikal
│   ├── test_risk_management.py     # Pengujian Sizing & Friksi Komisi
│   ├── test_paper_trading.py       # Pengujian Simulasi Transaksi Virtual
│   ├── test_ai_assistant.py        # Pengujian AI Validator, Decision & Chatbot
│   └── test_full_idx_coverage.py   # Pengujian Full Master DB, Explorer & Scanner
├── .env.example
├── requirements.txt
├── run_tests.py
└── README.md
```

---

## 🚀 Panduan Instalasi dan Menjalankan Aplikasi

### 1. Instalasi Dependensi
Pastikan Python 3.10+ telah terpasang, kemudian jalankan:
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Environment
Salin file `.env.example` menjadi `.env`:
```bash
copy .env.example .env
```
Isi konfigurasi sesuai kebutuhan Anda (misal `DEFAULT_DATA_PROVIDER=mock` atau `yfinance`, atau masukkan API Key Invezgo / Api.co.id jika tersedia).

### 3. Menjalankan Unit & Integration Test
Untuk memverifikasi seluruh komponen bekerja sempurna:
```bash
python run_tests.py
```

### 4. Menjalankan Streamlit Dashboard
Jalankan dashboard interaktif di peramban Anda:
```bash
streamlit run app/dashboard/app.py
```
Dashboard akan otomatis terbuka pada `http://localhost:8501`.

### 5. Menjalankan FastAPI REST Backend
Untuk menjalankan REST API server:
```bash
uvicorn app.api.main:app --reload --port 8000
```
Akses dokumentasi interaktif Swagger API pada `http://localhost:8000/docs`.

---

## ⚖️ Penafian Risiko (Risk Disclaimer)

Sistem ini dirancang semata-mata sebagai **Decision Support System** dan sarana simulasi **Paper Trading**. Sistem tidak memberikan jaminan keuntungan pasti dalam perdagangan saham. Setiap keputusan transaksi saham nyata di Bursa Efek Indonesia sepenuhnya merupakan tanggung jawab pengguna.
