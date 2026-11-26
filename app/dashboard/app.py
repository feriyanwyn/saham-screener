"""AI-Powered Indonesian Stock Prediction & Scalping Assistant - Streamlit Dashboard.
Menampilkan 8 Halaman:
1. Market Overview
2. Stock Screener
3. Stock Detail & Interactive Chart
4. Scalping Signals
5. Portfolio & Paper Trading
6. Walk-Forward Backtesting
7. Model Performance (LSTM & BiLSTM)
8. Settings & Risk Configuration
"""
import os
import json
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Setup page configuration
st.set_page_config(
    page_title="AI Stock Analyzer | IDX Scalper",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Fintech SaaS CSS Styling
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }
    
    /* Metric cards styling */
    div[data-testid="stMetric"] {
        background-color: var(--background-color, rgba(120, 140, 180, 0.05));
        border: 1px solid rgba(120, 140, 180, 0.15);
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Semantic Badges */
    .badge-buy {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 9999px;
        padding: 2px 10px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 9999px;
        padding: 2px 10px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-hold {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 9999px;
        padding: 2px 10px;
        font-weight: 700;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

from config.settings import settings
from config.idx_constants import (
    LOT_SIZE, align_to_tick, get_tick_size, get_ara_arb_limits,
    IDX_SECTORS, IDX_BOARDS, IDX_STATUSES
)
from database.connection import init_db, SessionLocal
from database.models import Instrument, MLModelMeta, MarketScanResult
from src.data_collection import get_data_provider, UniverseManager
from src.data_collection.idx_master_data import seed_idx_master_database, get_idx_coverage_stats
from src.technical_analysis.indicators import TechnicalAnalysisEngine
from src.machine_learning.trainer import ModelPipeline
from src.stock_screener import StockScreener, FullMarketScanner
from src.signal_engine.engine import ScalpingSignalEngine
from src.risk_management.risk_manager import RiskManager
from src.paper_trading.account import PaperTradingSimulator
from src.backtesting.engine import BacktestEngine
from src.ai_assistant import (
    AITradingDecisionEngine,
    AIChatAssistant,
    get_llm_provider
)

# Inisialisasi DB saat startup
init_db()


# -----------------------------------------------------------------------------
# Helpers & Caching
# -----------------------------------------------------------------------------
@st.cache_resource
def get_provider_instance(provider_name: str):
    return get_data_provider(provider_name)


@st.cache_resource
def get_ml_pipeline_instance():
    return ModelPipeline()


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("🇮🇩 IDX AI Scalper")
st.sidebar.caption("AI-Powered Stock Prediction & Scalping Assistant")

active_provider_name = st.sidebar.selectbox(
    "Data Provider",
    ["mock", "yfinance", "invezgo", "apicoid"],
    index=0 if settings.DEFAULT_DATA_PROVIDER == "mock" else 1
)
provider = get_provider_instance(active_provider_name)
ml_pipe = get_ml_pipeline_instance()
signal_engine = ScalpingSignalEngine(ml_pipeline=ml_pipe)
paper_sim = PaperTradingSimulator("STREAMLIT_USER", initial_balance=settings.INITIAL_CAPITAL_IDR)

# Sinkronkan universe
universe_mgr = UniverseManager(provider)
active_tickers = universe_mgr.get_active_tickers()
if not active_tickers:
    universe_mgr.sync_instruments()
    active_tickers = universe_mgr.get_active_tickers()

if not active_tickers:
    active_tickers = ["BBCA", "BBRI", "BMRI", "TLKM", "ASII", "AMMN", "ADRO", "BREN", "GOTO", "BRIS"]

menu = st.sidebar.radio(
    "Navigasi Modul",
    [
        "Market Overview",
        "Market Explorer (Full IDX)",
        "Stock Screener",
        "Full Market Scanner & AI Ranking",
        "Stock Detail & Chart",
        "Scalping Signals",
        "AI Decision & Chatbot",
        "Portfolio & Paper Trading",
        "Strategy Backtesting",
        "Model Performance",
        "Settings & Risk"
    ]
)

st.sidebar.divider()
acc_summary = paper_sim.get_portfolio_summary()
st.sidebar.metric("Virtual Equity", f"Rp {acc_summary['equity']:,.0f}", f"{acc_summary['unrealized_pnl']:+,.0f}")
st.sidebar.metric("Available Cash", f"Rp {acc_summary['cash']:,.0f}")


# -----------------------------------------------------------------------------
# Halaman 1: Market Overview
# -----------------------------------------------------------------------------
if menu == "Market Overview":
    st.title("📊 Market Overview - Bursa Efek Indonesia")
    st.caption(f"Provider Aktif: **{active_provider_name.upper()}** | Mode: Intraday Decision Support")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status Pasar", "OPEN REGULER", "Sesi Berjalan")
    with col2:
        st.metric("Total Emiten Dipantau", len(active_tickers))
    with col3:
        st.metric("Batas ARA / ARB", "±20% s/d ±35%", "Simetris")
    with col4:
        st.metric("Estimasi Biaya Transaksi", "0.48%", "Round-Trip Friction")

    st.subheader("Ringkasan Saham Unggulan (Watchlist Terkini)")
    quotes = []
    for t in active_tickers[:10]:
        q = provider.get_live_quote(t)
        if q:
            quotes.append(q)

    if quotes:
        df_quotes = pd.DataFrame(quotes)
        st.dataframe(
            df_quotes[["ticker", "last_price", "change", "change_pct", "volume", "value"]].style.format({
                "last_price": "Rp {:,.0f}",
                "change": "{:+,.0f}",
                "change_pct": "{:+.2f}%",
                "volume": "{:,.0f}",
                "value": "Rp {:,.0f}"
            }),
            use_container_width=True
        )
    else:
        st.info("Sedang memuat data pasar...")


# -----------------------------------------------------------------------------
# Halaman Baru: Market Explorer (Full IDX Stock Database)
# -----------------------------------------------------------------------------
elif menu == "Market Explorer (Full IDX)":
    st.title("🏛️ Market Explorer - Seluruh Emiten Terdaftar BEI")
    st.caption("Eksplorasi master database seluruh emiten Bursa Efek Indonesia berdasarkan klasifikasi 12 sektor IDX-IC resmi.")

    # 1. Metrik Cakupan Data Pasar BEI
    cov = universe_mgr.get_coverage_statistics()
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Total Emiten BEI", cov["total_listed_idx"])
    with m2:
        st.metric("Emiten Aktif", cov["active_stocks"])
    with m3:
        st.metric("Suspensi", cov["suspended_stocks"])
    with m4:
        st.metric("Newly Listed", cov["newly_listed_stocks"])
    with m5:
        st.metric("Delisted", cov["delisted_stocks"])
    with m6:
        st.metric("Data Intraday", f"{cov['coverage_breakdown']['has_intraday_data']} Ticker")

    col_sync, col_info = st.columns([1, 3])
    with col_sync:
        if st.button("🔄 Sinkronkan Master Data BEI", type="secondary"):
            with st.spinner("Menyinkronkan master emiten..."):
                synced_total = universe_mgr.sync_instruments(force_seed=True)
                st.success(f"Berhasil menyinkronkan {synced_total} emiten BEI!")
                st.rerun()
    with col_info:
        st.caption(f"🕒 Waktu Sinkronisasi Terakhir: **{cov['last_synced_at']}**")

    st.divider()

    # 2. Filter Bar Terpadu
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        search_kw = st.text_input("🔍 Cari Ticker atau Nama Perusahaan", placeholder="Contoh: BBCA, Bank, Telkom, Tambang")
    with f2:
        sector_options = ["ALL"] + [sec["name_en"] for sec in IDX_SECTORS.values()]
        sel_sector = st.selectbox("Sektor IDX-IC", sector_options)
    with f3:
        board_options = ["ALL"] + IDX_BOARDS
        sel_board = st.selectbox("Papan Pencatatan", board_options)
    with f4:
        page_size = st.selectbox("Baris/Halaman", [25, 50, 100], index=0)

    # Status Selector Tabs
    status_tabs = st.radio(
        "Kategori Status",
        ["ALL", "ACTIVE", "SUSPENDED", "NEWLY_LISTED", "DELISTED"],
        horizontal=True
    )

    # Pagination state
    if "explorer_page" not in st.session_state:
        st.session_state["explorer_page"] = 1

    # Query ke Universe Manager dengan Backend Pagination
    res_explorer = universe_mgr.get_explorer_stocks(
        search=search_kw,
        sector=sel_sector,
        board=sel_board,
        status=status_tabs,
        page=st.session_state["explorer_page"],
        page_size=page_size
    )

    st.subheader(f"Daftar Saham ({res_explorer['total_items']} Ditemukan - Halaman {res_explorer['current_page']} dari {res_explorer['total_pages']})")

    if res_explorer["items"]:
        df_exp = pd.DataFrame(res_explorer["items"])
        st.dataframe(
            df_exp[[
                "ticker", "name", "sector", "subsector", "board", "status",
                "listing_date", "has_daily_data", "has_intraday_data", "last_synced_at"
            ]],
            use_container_width=True
        )

        # Pagination Controls & Export
        p_col1, p_col2, p_col3, p_col4 = st.columns([1, 1, 2, 1])
        with p_col1:
            if st.button("⬅️ Halaman Sebelumnya", disabled=(res_explorer["current_page"] <= 1)):
                st.session_state["explorer_page"] -= 1
                st.rerun()
        with p_col2:
            if st.button("Halaman Berikutnya ➡️", disabled=(res_explorer["current_page"] >= res_explorer["total_pages"])):
                st.session_state["explorer_page"] += 1
                st.rerun()
        with p_col4:
            csv_data = df_exp.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"idx_stocks_page_{res_explorer['current_page']}.csv",
                mime="text/csv"
            )
    else:
        st.info("Tidak ada emiten yang sesuai dengan kriteria filter yang dipilih.")


# -----------------------------------------------------------------------------
# Halaman Baru: Full Market Scanner & AI Ranking (Bagian D & E)
# -----------------------------------------------------------------------------
elif menu == "Full Market Scanner & AI Ranking":
    st.title("🌐 Full Market Scanner & AI Stock Ranking")
    st.caption("Pemindaian kuantitatif menyeluruh seluruh emiten BEI dengan scoring teknikal, evaluasi LSTM & BiLSTM, dan perankingan AI.")

    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        sector_scan_opts = ["ALL"] + [sec["name_en"] for sec in IDX_SECTORS.values()]
        target_sector = st.selectbox("Pilih Lingkup Sektor", sector_scan_opts, key="sector_scan_select")
    with col_s2:
        max_scan_stocks = st.selectbox("Maksimal Saham Dipindai", [25, 50, 100, "Semua Saham Aktif"], index=1)
        max_stocks_val = None if max_scan_stocks == "Semua Saham Aktif" else int(max_scan_stocks)
    with col_s3:
        st.write("")
        st.write("")
        run_scan_btn = st.button("🚀 Jalankan Full Scan", type="primary")

    scanner = FullMarketScanner(provider=provider, ml_pipeline=ml_pipe)

    if run_scan_btn:
        with st.spinner("Memindai seluruh pasar, menghitung indikator teknikal & inferensi Deep Learning..."):
            scan_out = scanner.run_scan(
                sector_filter=target_sector,
                max_stocks=max_stocks_val,
                timeframe="5m"
            )
        st.success(
            f"✅ Pemindaian Selesai! {scan_out['sufficient_data_count']} dari {scan_out['total_scanned']} saham memiliki data memadai "
            f"(Waktu eksekusi: {scan_out['elapsed_seconds']} detik). Hasil telah tersimpan di cache database."
        )

    st.divider()

    # Kategori AI Ranking Tabs
    rank_tab1, rank_tab2, rank_tab3, rank_tab4, rank_tab5, rank_tab6 = st.tabs([
        "🔥 Top Bullish",
        "⚡ Potential Scalping",
        "📈 Highest Volume",
        "🛡️ Lowest Risk",
        "⚠️ Top Bearish",
        "📋 Semua Hasil Scan"
    ])

    with rank_tab1:
        st.subheader("Top Bullish Momentum Stocks")
        bullish_items = scanner.get_latest_cached_scan(category="TOP_BULLISH", sector=target_sector, limit=30)
        if bullish_items:
            st.dataframe(pd.DataFrame(bullish_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk memperbarui kategori ini.")

    with rank_tab2:
        st.subheader("Potential Scalping Candidates (High R/R)")
        scalp_items = scanner.get_latest_cached_scan(category="POTENTIAL_SCALPING", sector=target_sector, limit=30)
        if scalp_items:
            st.dataframe(pd.DataFrame(scalp_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk memperbarui kategori ini.")

    with rank_tab3:
        st.subheader("Highest Volume Surge (RelVol >= 1.6x)")
        vol_items = scanner.get_latest_cached_scan(category="HIGHEST_VOLUME", sector=target_sector, limit=30)
        if vol_items:
            st.dataframe(pd.DataFrame(vol_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk memperbarui kategori ini.")

    with rank_tab4:
        st.subheader("Lowest Risk & High Liquidity Stocks")
        risk_items = scanner.get_latest_cached_scan(category="LOWEST_RISK", sector=target_sector, limit=30)
        if risk_items:
            st.dataframe(pd.DataFrame(risk_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk memperbarui kategori ini.")

    with rank_tab5:
        st.subheader("Top Bearish / Avoid Stocks")
        bear_items = scanner.get_latest_cached_scan(category="TOP_BEARISH", sector=target_sector, limit=30)
        if bear_items:
            st.dataframe(pd.DataFrame(bear_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk memperbarui kategori ini.")

    with rank_tab6:
        st.subheader("Seluruh Emiten Hasil Scan Terkini")
        all_scan_items = scanner.get_latest_cached_scan(sector=target_sector, limit=100)
        if all_scan_items:
            st.dataframe(pd.DataFrame(all_scan_items), use_container_width=True)
        else:
            st.info("Jalankan scan untuk menampilkan data.")


# -----------------------------------------------------------------------------
# Halaman 2: Stock Screener
# -----------------------------------------------------------------------------
elif menu == "Stock Screener":
    st.title("🔍 Multi-Factor Stock Screener")
    st.caption("Penyaringan kuantitatif saham BEI berdasarkan likuiditas, momentum, dan spread bid-ask.")

    col1, col2, col3 = st.columns(3)
    with col1:
        min_val = st.number_input("Min Nilai Transaksi (IDR)", value=100_000_000, step=100_000_000)
    with col2:
        min_rel_vol = st.slider("Min Relative Volume (x)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
    with col3:
        max_spread = st.slider("Maksimal Spread (Tick)", min_value=1, max_value=5, value=3)

    if st.button("🚀 Jalankan Pemindaian Pasar", type="primary"):
        with st.spinner("Memindai seluruh saham BEI..."):
            screener = StockScreener(provider)
            results = screener.screen_stocks(
                min_value_idr=float(min_val),
                min_rel_volume=float(min_rel_vol),
                max_spread_ticks=int(max_spread)
            )

        if results:
            st.success(f"Ditemukan {len(results)} saham memenuhi kriteria.")
            df_res = pd.DataFrame(results)
            st.dataframe(
                df_res[[
                    "ticker", "name", "last_price", "change_pct", "opportunity_score",
                    "trend_status", "relative_volume", "rsi_14", "spread_ticks", "value"
                ]].style.format({
                    "last_price": "Rp {:,.0f}",
                    "change_pct": "{:+.2f}%",
                    "opportunity_score": "{:.1f}",
                    "relative_volume": "{:.2f}x",
                    "rsi_14": "{:.1f}",
                    "value": "Rp {:,.0f}"
                }),
                use_container_width=True
            )
        else:
            st.warning("Tidak ada saham yang memenuhi seluruh filter saat ini.")


# -----------------------------------------------------------------------------
# Halaman 3: Stock Detail & Chart
# -----------------------------------------------------------------------------
elif menu == "Stock Detail & Chart":
    st.title("📈 Stock Detail & Interactive Technical Chart")

    col1, col2 = st.columns([1, 3])
    with col1:
        sel_ticker = st.selectbox("Pilih Kode Saham", active_tickers)
        sel_tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "daily"], index=1)
        candle_limit = st.slider("Jumlah Candle", min_value=30, max_value=200, value=90)

    if sel_tf == "daily":
        df_chart = provider.get_daily_history(sel_ticker)
    else:
        df_chart = provider.get_intraday_data(sel_ticker, timeframe=sel_tf, limit=candle_limit)

    if not df_chart.empty and len(df_chart) >= 15:
        df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_chart)

        # Plotly Candlestick Chart dengan Volume, VWAP, EMA, dan RSI
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.6, 0.2, 0.2]
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df_ta["timestamp"],
            open=df_ta["open"],
            high=df_ta["high"],
            low=df_ta["low"],
            close=df_ta["close"],
            name="OHLC"
        ), row=1, col=1)

        # Overlays: EMA 9, EMA 20, VWAP
        fig.add_trace(go.Scatter(x=df_ta["timestamp"], y=df_ta["ema_9"], line=dict(color="#3b82f6", width=1.2), name="EMA 9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ta["timestamp"], y=df_ta["ema_20"], line=dict(color="#f59e0b", width=1.5), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ta["timestamp"], y=df_ta["vwap"], line=dict(color="#ec4899", width=1.8, dash="dot"), name="VWAP"), row=1, col=1)

        # Volume
        colors = ["#22c55e" if c >= o else "#ef4444" for o, c in zip(df_ta["open"], df_ta["close"])]
        fig.add_trace(go.Bar(x=df_ta["timestamp"], y=df_ta["volume"], marker_color=colors, name="Volume"), row=2, col=1)

        # RSI 14
        fig.add_trace(go.Scatter(x=df_ta["timestamp"], y=df_ta["rsi_14"], line=dict(color="#a855f7", width=1.5), name="RSI 14"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Prediksi AI Terkini
        ml_pred = ml_pipe.predict_latest(df_ta, ticker=sel_ticker, timeframe=sel_tf.upper())
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("BiLSTM Direction Probability", f"{ml_pred['up_probability']:.1%}", "Arah Naik" if ml_pred['up_probability'] >= 0.5 else "Arah Turun")
        with c2:
            st.metric("LSTM Expected Return", f"{ml_pred['predicted_return']:+.2%}")
        with c3:
            st.metric("Calibrated AI Confidence", f"{ml_pred['calibrated_confidence']:.1%}")
    else:
        st.warning("Data chart tidak mencukupi untuk visualisasi.")


# -----------------------------------------------------------------------------
# Halaman 4: Scalping Signals
# -----------------------------------------------------------------------------
elif menu == "Scalping Signals":
    st.title("🎯 Scalping Signal Engine (Decision Support)")
    st.caption("Kombinasi analisis teknikal komprehensif, probabilitas Deep Learning, dan fraksi harga resmi BEI.")

    sel_ticker = st.selectbox("Pilih Saham untuk Analisis Sinyal", active_tickers)
    df_sig_candles = provider.get_intraday_data(sel_ticker, timeframe="5m", limit=80)

    if not df_sig_candles.empty and len(df_sig_candles) >= 25:
        sig = signal_engine.generate_signal(df_sig_candles, ticker=sel_ticker, timeframe="5M")

        # Visualisasi Status Sinyal
        status_color = {
            "BUY": "🟢",
            "SELL": "🔴",
            "HOLD": "🟡",
            "WATCHLIST": "🔵"
        }.get(sig["signal_type"], "⚪")

        st.markdown(f"### {status_color} Rekomendasi Sinyal: **{sig['signal_type']}**")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Harga Terakhir", f"Rp {sig['price_at_signal']:,.0f}")
        with c2:
            st.metric("Area Entry", f"Rp {sig['entry_price']:,.0f}")
        with c3:
            st.metric("Take Profit (TP)", f"Rp {sig['take_profit']:,.0f}", f"+{((sig['take_profit'] - sig['entry_price'])/sig['entry_price']):.2%}")
        with c4:
            st.metric("Stop Loss (SL)", f"Rp {sig['stop_loss']:,.0f}", f"-{((sig['entry_price'] - sig['stop_loss'])/sig['entry_price']):.2%}")

        st.info(f"**Alasan Sinyal:** {sig['rationale']}")
        st.warning(f"**Kondisi Pembatalan Sinyal:** {sig['invalidation_criteria']}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"- **Risk / Reward Ratio:** {sig['risk_reward_ratio']} : 1")
            st.write(f"- **Biaya Transaksi (Est. Round-Trip):** Rp {sig['estimated_fee_per_share']} per lembar")
        with col_b:
            st.write(f"- **Batas ARA Hari Ini:** Rp {sig['ara_price']:,.0f}")
            st.write(f"- **Batas ARB Hari Ini:** Rp {sig['arb_price']:,.0f}")

        # Tombol Eksekusi Cepat ke Paper Trading
        if sig["signal_type"] == "BUY":
            st.divider()
            st.subheader("⚡ Eksekusi Simulasi Paper Trading")
            lots_to_buy = st.number_input("Jumlah Lot yang Dibeli", min_value=1, max_value=500, value=2)
            if st.button("Kirim Order Beli ke Akun Virtual", type="primary"):
                exec_res = paper_sim.execute_buy(
                    ticker=sel_ticker,
                    price=sig["entry_price"],
                    lots=int(lots_to_buy),
                    stop_loss=sig["stop_loss"],
                    take_profit=sig["take_profit"]
                )
                if exec_res["status"] == "FILLED":
                    st.success(f"Order Beli {lots_to_buy} lot {sel_ticker} Berhasil Dijalankan! Total Biaya: Rp {exec_res['total_cost']:,.0f}")
                else:
                    st.error(f"Order Ditolak: {exec_res['reason']}")
    else:
        st.warning("Data candle belum cukup untuk menghasilkan sinyal yang valid.")


# -----------------------------------------------------------------------------
# Halaman Tambahan: AI Decision & Chatbot Assistant
# -----------------------------------------------------------------------------
elif menu == "AI Decision & Chatbot":
    st.title("🤖 AI Trading Decision Assistant & Chatbot")
    st.caption("Asisten analisis berbasis LLM (Gemini/OpenAI/Claude/Mock) dengan validasi kuantitatif terstruktur.")

    tab1, tab2, tab3 = st.tabs(["🎯 Analisis Keputusan Saham", "📊 Multi-Stock AI Ranking", "💬 Asisten Chat Interaktif"])

    # Tab 1: Single Stock AI Analysis
    with tab1:
        st.subheader("Analisis Keputusan Saham Terpadu")
        c1, c2 = st.columns([1, 2])
        with c1:
            ai_ticker = st.selectbox("Pilih Saham untuk Analisis LLM", active_tickers, key="ai_ticker_select")
            ai_tf = st.selectbox("Timeframe Analisis", ["1m", "5m", "15m", "1h"], index=1, key="ai_tf_select")
            run_ai_btn = st.button("🧠 Jalankan Analisis AI & Validasi", type="primary")

        if run_ai_btn:
            with st.spinner(f"Menganalisis {ai_ticker} dengan AI Decision Engine..."):
                df_c = provider.get_intraday_data(ai_ticker, timeframe=ai_tf, limit=80)
                q = provider.get_live_quote(ai_ticker)
                engine = AITradingDecisionEngine(ml_pipeline=ml_pipe)
                decision = engine.analyze_stock(ai_ticker, df_c, q, timeframe=ai_tf.upper())

            st.divider()
            dec_val = decision.get("decision", "NO TRADE")
            v_status = decision.get("validation_status", "UNKNOWN")
            
            status_badge = "🟢" if dec_val == "BUY" and v_status == "APPROVED" else ("🔴" if dec_val == "SELL" else "🟡")
            st.markdown(f"### {status_badge} Rekomendasi AI: **{dec_val}** (Validasi Kuantitatif: `{v_status}`)")

            if v_status == "REJECTED":
                st.error(f"⛔ Alasan Penolakan Validasi: {decision.get('rejection_reason')}")

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Area Entry", f"{decision.get('entry_zone', 'N/A')}")
            with col_b:
                st.metric("Stop Loss", f"Rp {decision.get('stop_loss', 0):,.0f}")
            with col_c:
                st.metric("Take Profit", f"Rp {decision.get('take_profit', 0):,.0f}")
            with col_d:
                st.metric("Risk / Reward", f"{decision.get('risk_reward_ratio', 0)}x")

            st.write(f"**Tren & Indikator:** {decision.get('trend_analysis', '')} {decision.get('technical_analysis', '')}")
            st.write(f"**Interpretasi Deep Learning:** {decision.get('ml_prediction_interpretation', '')}")
            st.warning(f"**Risiko Utama:** {decision.get('main_risks', 'N/A')}")
            st.info(f"**Penjelasan Rinci:**\n\n{decision.get('detailed_explanation', '')}")

    # Tab 2: Multi-Stock Ranking
    with tab2:
        st.subheader("Pemeringkatan Kualitas Peluang Multi-Saham")
        if st.button("Jalankan Pemeringkatan Multi-Saham AI"):
            with st.spinner("Memindai dan menyusun ranking peluang..."):
                screener = StockScreener(provider)
                screened = screener.screen_stocks(min_value_idr=300_000_000, min_rel_volume=0.8)
                engine = AITradingDecisionEngine(ml_pipeline=ml_pipe)
                rank_res = engine.rank_screened_stocks(screened)

            st.write(f"**Ikhtisar Pasar:** {rank_res.get('market_summary', '')}")
            if rank_res.get("ranking"):
                df_rank = pd.DataFrame(rank_res["ranking"])
                st.dataframe(df_rank, use_container_width=True)
            else:
                st.info("Tidak ada saham yang memenuhi kriteria ranking.")

    # Tab 3: Interactive Chat Assistant
    with tab3:
        st.subheader("💬 Asisten Chat AI Pasar Saham Indonesia")
        st.caption("Tanyakan kondisi pasar, alasan rekomendasi sinyal, indikator, atau risiko trading scalping.")

        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Display history
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input("Tulis pertanyaan Anda seputar saham atau analisis scalping di sini...")
        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Grounding context
            chat_assistant = AIChatAssistant()
            quote_ctx = provider.get_live_quote(active_tickers[0]) if active_tickers else {}
            response_text = chat_assistant.answer_query(
                user_input,
                current_market_context=quote_ctx,
                portfolio_summary=paper_sim.get_portfolio_summary()
            )

            st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"):
                st.write(response_text)


# -----------------------------------------------------------------------------
# Halaman 5: Portfolio & Paper Trading
# -----------------------------------------------------------------------------
elif menu == "Portfolio & Paper Trading":
    st.title("💼 Virtual Portfolio & Paper Trading")

    summary = paper_sim.get_portfolio_summary()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Equity", f"Rp {summary['equity']:,.0f}", f"{summary['unrealized_pnl']:+,.0f}")
    with c2:
        st.metric("Kas Tersedia", f"Rp {summary['cash']:,.0f}")
    with c3:
        st.metric("Nilai Portofolio Terbuka", f"Rp {summary['market_value']:,.0f}")

    st.subheader("Posisi Terbuka Saat Ini")
    if summary["open_positions"]:
        df_pos = pd.DataFrame(summary["open_positions"])
        st.dataframe(
            df_pos[["ticker", "lots", "shares", "avg_price", "current_price", "stop_loss", "take_profit", "unrealized_pnl", "unrealized_pnl_pct"]].style.format({
                "avg_price": "Rp {:,.0f}",
                "current_price": "Rp {:,.0f}",
                "stop_loss": "Rp {:,.0f}",
                "take_profit": "Rp {:,.0f}",
                "unrealized_pnl": "Rp {:+,.0f}",
                "unrealized_pnl_pct": "{:+.2f}%"
            }),
            use_container_width=True
        )

        st.subheader("Tutup Posisi (Jual)")
        pos_ticker = st.selectbox("Pilih Saham yang Akan Ditutup", [p["ticker"] for p in summary["open_positions"]])
        if st.button("Jual Seluruh Lot Saham Terpilih", type="secondary"):
            quote = provider.get_live_quote(pos_ticker)
            sell_price = quote.get("last_price", 1000)
            res_sell = paper_sim.execute_sell(pos_ticker, price=sell_price)
            if res_sell["status"] == "FILLED":
                st.success(f"Posisi {pos_ticker} berhasil ditutup! Realized P&L: Rp {res_sell['realized_pnl']:+,.0f} ({res_sell['realized_pnl_pct']:+.2f}%)")
                st.rerun()
            else:
                st.error(f"Gagal menutup posisi: {res_sell['reason']}")
    else:
        st.info("Belum ada posisi terbuka di portofolio.")

    st.subheader("Riwayat Transaksi (Trade Log)")
    history = paper_sim.get_trade_history()
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True)


# -----------------------------------------------------------------------------
# Halaman 6: Walk-Forward Backtesting
# -----------------------------------------------------------------------------
elif menu == "Strategy Backtesting":
    st.title("🧪 Walk-Forward Strategy Backtesting")
    st.caption("Pengujian strategi intraday tanpa lookahead bias dengan simulasi friksi fee dan slippage.")

    col1, col2, col3 = st.columns(3)
    with col1:
        bt_ticker = st.selectbox("Pilih Saham", active_tickers, index=0)
    with col2:
        bt_capital = st.number_input("Modal Awal (IDR)", value=10_000_000, step=1_000_000)
    with col3:
        bt_slippage = st.slider("Simulasi Slippage (Tick)", min_value=0, max_value=3, value=1)

    if st.button("Mulai Walk-Forward Backtest", type="primary"):
        with st.spinner("Menjalankan simulasi candle per candle..."):
            bt_engine = BacktestEngine(initial_capital=float(bt_capital), slippage_ticks=int(bt_slippage))
            df_hist = provider.get_intraday_data(bt_ticker, timeframe="5m", limit=150)
            bt_results = bt_engine.run_backtest(df_hist, ticker=bt_ticker)

        if "error" not in bt_results:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Win Rate", f"{bt_results['win_rate']:.1f}%")
            with m2:
                st.metric("Net Profit", f"Rp {bt_results['net_profit']:+,.0f}", f"{bt_results['net_profit_pct']:+.2f}%")
            with m3:
                st.metric("Profit Factor", f"{bt_results['profit_factor']:.2f}")
            with m4:
                st.metric("Max Drawdown", f"{bt_results['max_drawdown_pct']:.2f}%")

            # Equity Curve
            eq_curve = pd.DataFrame(bt_results["equity_curve"])
            if not eq_curve.empty:
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=eq_curve["timestamp"], y=eq_curve["equity"], mode="lines", name="Equity Curve", line=dict(color="#10b981", width=2)))
                fig_eq.update_layout(title="Simulated Portfolio Equity Curve (Net of Fees)", height=400, template="plotly_dark")
                st.plotly_chart(fig_eq, use_container_width=True)

            st.subheader("Daftar Transaksi Backtest")
            if bt_results["trades"]:
                st.dataframe(pd.DataFrame(bt_results["trades"]), use_container_width=True)
            else:
                st.info("Tidak ada transaksi yang terpicu selama periode data ini.")
        else:
            st.error(bt_results["error"])


# -----------------------------------------------------------------------------
# Halaman 7: Model Performance
# -----------------------------------------------------------------------------
elif menu == "Model Performance":
    st.title("🤖 Deep Learning Model Registry & Evaluation")
    st.caption("Perbandingan metrik evaluasi model LSTM (Regression) dan BiLSTM (Classification).")

    db = SessionLocal()
    models_meta = db.query(MLModelMeta).order_by(MLModelMeta.created_at.desc()).all()
    db.close()

    if models_meta:
        data = [
            {
                "Model ID": m.model_id,
                "Ticker": m.ticker,
                "Architecture": m.architecture,
                "Timeframe": m.timeframe,
                "Test MAE": m.test_mae,
                "Test RMSE": m.test_rmse,
                "Directional Acc": f"{(m.test_directional_accuracy or 0):.2%}",
                "Precision": m.precision_score,
                "Recall": m.recall_score,
                "F1-Score": m.f1_score,
                "Version": m.version
            }
            for m in models_meta
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("Belum ada riwayat training model yang tercatat. Jalankan training model terlebih dahulu.")

    st.subheader("Latih Ulang Model Mandiri")
    sel_train_ticker = st.selectbox("Pilih Saham untuk Dilatih Ulang", active_tickers)
    epochs = st.slider("Jumlah Epochs", min_value=5, max_value=30, value=10)
    if st.button("Latih Model LSTM & BiLSTM Sekarang"):
        with st.spinner(f"Melatih model Deep Learning untuk {sel_train_ticker}..."):
            df_train = provider.get_intraday_data(sel_train_ticker, timeframe="5m", limit=180)
            res = ml_pipe.train_and_evaluate(df_train, ticker=sel_train_ticker, timeframe="5M", epochs=epochs)
            if "error" not in res:
                st.success(f"Model berhasil dilatih! Directional Accuracy: {res['directional_accuracy']:.2%}, RMSE: {res['test_rmse']}")
                st.rerun()
            else:
                st.error(res["error"])


# -----------------------------------------------------------------------------
# Halaman 8: Settings & Risk Configuration
# -----------------------------------------------------------------------------
elif menu == "Settings & Risk":
    st.title("⚙️ System Settings & Risk Controls")
    st.caption("Konfigurasi parameter risiko, akun provider, dan biaya komisi broker.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Konfigurasi Akun & Modal")
        st.text_input("Database URL", value=settings.DATABASE_URL, disabled=True)
        st.number_input("Modal Awal Virtual (IDR)", value=settings.INITIAL_CAPITAL_IDR, disabled=True)
        st.number_input("Maksimal Posisi Terbuka", value=settings.MAX_OPEN_POSITIONS, disabled=True)

    with col2:
        st.subheader("Biaya Transaksi Resmi BEI")
        st.number_input("Broker Fee Beli (inc. PPN + Levy)", value=settings.BROKER_BUY_FEE_PCT, format="%.4f", disabled=True)
        st.number_input("Broker Fee Jual (inc. PPh + PPN + Levy)", value=settings.BROKER_SELL_FEE_PCT, format="%.4f", disabled=True)
        st.info("Untuk mengubah parameter permanen, edit file `.env` di root direktori.")
