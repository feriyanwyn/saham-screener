"""IDX Market Constants and Regulations.
Defines tick size rules, ARA/ARB limits, trading hours, and fee structures.
"""
from dataclasses import dataclass
from datetime import time
from typing import Tuple


@dataclass(frozen=True)
class IDXTradingHours:
    """Official IDX Regular Market Trading Hours (WIB / UTC+7)."""
    # Pre-opening
    PRE_OPEN_START: time = time(8, 45)
    PRE_OPEN_END: time = time(8, 59)
    
    # Session 1 (Monday - Thursday)
    SESSI_1_START: time = time(9, 0)
    SESSI_1_END_REGULAR: time = time(12, 0)
    # Session 1 (Friday)
    SESSI_1_END_FRIDAY: time = time(11, 30)
    
    # Session 2 (Monday - Thursday)
    SESSI_2_START_REGULAR: time = time(13, 30)
    SESSI_2_END: time = time(15, 49)
    # Session 2 (Friday)
    SESSI_2_START_FRIDAY: time = time(14, 0)
    
    # Pre-closing & Post-trading
    PRE_CLOSE_START: time = time(15, 50)
    PRE_CLOSE_END: time = time(16, 0)
    POST_TRADE_END: time = time(16, 15)


def get_tick_size(price: float) -> int:
    """Mengembalikan fraksi harga (tick size) resmi BEI berdasarkan kelompok harga.
    
    Kelompok Harga:
    - < Rp200: Fraksi Rp1 (Maksimum lompatan Rp10)
    - Rp200 - < Rp500: Fraksi Rp2 (Maksimum lompatan Rp20)
    - Rp500 - < Rp2.000: Fraksi Rp5 (Maksimum lompatan Rp50)
    - Rp2.000 - < Rp5.000: Fraksi Rp10 (Maksimum lompatan Rp100)
    - >= Rp5.000: Fraksi Rp25 (Maksimum lompatan Rp250)
    """
    if price < 200:
        return 1
    elif price < 500:
        return 2
    elif price < 2000:
        return 5
    elif price < 5000:
        return 10
    else:
        return 25


def align_to_tick(price: float, round_up: bool = False) -> int:
    """Membulatkan harga ke fraksi harga resmi BEI terdekat.
    
    Args:
        price: Nilai harga teoritis.
        round_up: Jika True dibulatkan ke atas, jika False dibulatkan ke bawah.
    """
    if price <= 0:
        return 1
    
    tick = get_tick_size(price)
    remainder = price % tick
    if remainder == 0:
        return int(price)
    
    if round_up:
        aligned = price + (tick - remainder)
    else:
        aligned = price - remainder
    return max(1, int(aligned))


def get_ara_arb_limits(prev_close: float) -> Tuple[int, int]:
    """Menghitung batas Auto Rejection Atas (ARA) dan Auto Rejection Bawah (ARB) Simetris BEI.
    
    Batas Persentase:
    - Rp50 - Rp200: ±35%
    - >Rp200 - Rp5.000: ±25%
    - >Rp5.000: ±20%
    """
    if prev_close <= 0:
        return 1, 1
    
    if prev_close < 200:
        limit_pct = 0.35
    elif prev_close <= 5000:
        limit_pct = 0.25
    else:
        limit_pct = 0.20
        
    raw_ara = prev_close * (1 + limit_pct)
    raw_arb = prev_close * (1 - limit_pct)
    
    # Batas bawah bursa reguler adalah Rp50
    arb_price = max(50, align_to_tick(raw_arb, round_up=True))
    ara_price = align_to_tick(raw_ara, round_up=False)
    
    return ara_price, arb_price


# Satuan Lot Saham BEI
LOT_SIZE = 100

# Default Friction Fees
DEFAULT_BROKER_BUY_FEE_PCT = 0.0019   # 0.15% broker + PPN 11% + Levy 0.043%
DEFAULT_BROKER_SELL_FEE_PCT = 0.0029  # 0.25% broker + PPN 11% + Levy 0.043% + PPh 0.10%

# Official IDX-IC (IDX Industrial Classification) Sectors
IDX_SECTORS = {
    "ENERGY": {"code": "A", "name_id": "Energi", "name_en": "Energy"},
    "BASIC_MATERIALS": {"code": "B", "name_id": "Barang Baku", "name_en": "Basic Materials"},
    "INDUSTRIALS": {"code": "C", "name_id": "Perindustrian", "name_en": "Industrials"},
    "CONSUMER_NON_CYCLICALS": {"code": "D", "name_id": "Barang Konsumen Primer", "name_en": "Consumer Non-Cyclicals"},
    "CONSUMER_CYCLICALS": {"code": "E", "name_id": "Barang Konsumen Non-Primer", "name_en": "Consumer Cyclicals"},
    "HEALTHCARE": {"code": "F", "name_id": "Kesehatan", "name_en": "Healthcare"},
    "FINANCIALS": {"code": "G", "name_id": "Keuangan", "name_en": "Financials"},
    "PROPERTIES": {"code": "H", "name_id": "Properti & Real Estat", "name_en": "Properties & Real Estate"},
    "TECHNOLOGY": {"code": "I", "name_id": "Teknologi", "name_en": "Technology"},
    "INFRASTRUCTURES": {"code": "J", "name_id": "Infrastruktur", "name_en": "Infrastructures"},
    "TRANSPORTATION": {"code": "K", "name_id": "Transportasi & Logistik", "name_en": "Transportation & Logistic"},
    "LISTED_INVESTMENT": {"code": "L", "name_id": "Produk Investasi Tercatat", "name_en": "Listed Investment Products"},
}

# Listing Boards in IDX
IDX_BOARDS = ["Utama", "Pengembangan", "Akselerasi", "Pemantauan Khusus"]

# Listing Statuses
IDX_STATUSES = ["ACTIVE", "SUSPENDED", "NEWLY_LISTED", "DELISTED"]

