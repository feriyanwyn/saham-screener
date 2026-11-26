"""Dynamic Universe Manager for Indonesian Stock Exchange (IDX).
Mengelola sinkronisasi daftar emiten, status suspend, delisting, dan ketersediaan data.
Mendukung pencarian, filter 12 sektor IDX-IC, status pencatatan, dan backend pagination.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from config.idx_constants import IDX_SECTORS, IDX_BOARDS, IDX_STATUSES
from database.connection import SessionLocal
from database.models import Instrument
from src.data_collection.base_provider import BaseDataProvider
from src.data_collection.idx_master_data import seed_idx_master_database, get_idx_coverage_stats


class UniverseManager:
    """Manages full IDX stock universe lifecycle, explorer queries, and pagination."""

    def __init__(self, provider: Optional[BaseDataProvider] = None, db_session: Optional[Session] = None):
        self.provider = provider
        self.db = db_session or SessionLocal()

    def sync_instruments(self, force_seed: bool = False) -> int:
        """Sinkronisasi master data BEI ke database lokal."""
        # 1. Jalankan master seeder terlebih dahulu jika tabel kosong atau force_seed
        total_in_db = self.db.query(Instrument).count()
        if total_in_db == 0 or force_seed:
            seeded = seed_idx_master_database(self.db, force_refresh=force_seed)
        
        # 2. Jika provider eksternal tersedia, sinkronkan tambahan emiten
        if self.provider:
            raw_instruments = self.provider.get_instruments()
            for item in raw_instruments:
                ticker = item["ticker"].upper().strip()
                existing = self.db.query(Instrument).filter(Instrument.ticker == ticker).first()
                if existing:
                    existing.has_daily_data = True
                    existing.has_intraday_data = True
                    existing.last_synced_at = datetime.utcnow()
                else:
                    new_inst = Instrument(
                        ticker=ticker,
                        name=item.get("name", ticker),
                        sector=item.get("sector", "General"),
                        subsector=item.get("subsector", "General"),
                        industry=item.get("industry", "General"),
                        board=item.get("board", "Utama"),
                        status="ACTIVE",
                        is_active=True,
                        is_suspended=False,
                        has_daily_data=True,
                        has_intraday_data=True,
                        last_synced_at=datetime.utcnow()
                    )
                    self.db.add(new_inst)
            self.db.commit()

        return self.db.query(Instrument).count()

    def get_active_tickers(self) -> List[str]:
        """Mengembalikan seluruh ticker saham yang aktif diperdagangkan."""
        records = (
            self.db.query(Instrument.ticker)
            .filter(Instrument.is_active == True, Instrument.is_suspended == False)
            .order_by(Instrument.ticker.asc())
            .all()
        )
        return [r[0] for r in records]

    def get_all_tickers(self) -> List[str]:
        """Mengembalikan seluruh ticker tanpa memandang status."""
        records = self.db.query(Instrument.ticker).order_by(Instrument.ticker.asc()).all()
        return [r[0] for r in records]

    def get_explorer_stocks(
        self,
        search: Optional[str] = None,
        sector: Optional[str] = None,
        board: Optional[str] = None,
        status: Optional[str] = "ALL", # ALL, ACTIVE, SUSPENDED, NEWLY_LISTED, DELISTED
        sort_by: str = "ticker",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        """Query komprehensif Market Explorer dengan filter lengkap dan pagination backend."""
        query = self.db.query(Instrument)

        # 1. Search filter
        if search:
            term = f"%{search.strip().upper()}%"
            query = query.filter(or_(Instrument.ticker.like(term), Instrument.name.ilike(f"%{search.strip()}%")))

        # 2. Sector filter
        if sector and sector != "ALL":
            query = query.filter(Instrument.sector == sector)

        # 3. Board filter
        if board and board != "ALL":
            query = query.filter(Instrument.board == board)

        # 4. Status filter
        if status and status != "ALL":
            status_upper = status.upper().strip()
            if status_upper == "ACTIVE":
                query = query.filter(Instrument.status.in_(["ACTIVE", "NEWLY_LISTED"]))
            elif status_upper == "SUSPENDED":
                query = query.filter(Instrument.status == "SUSPENDED")
            elif status_upper == "NEWLY_LISTED":
                query = query.filter(Instrument.status == "NEWLY_LISTED")
            elif status_upper == "DELISTED":
                query = query.filter(Instrument.status == "DELISTED")

        # Total count sebelum pagination
        total_items = query.count()

        # 5. Sorting
        sort_column = getattr(Instrument, sort_by, Instrument.ticker)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # 6. Pagination
        p = max(1, page)
        ps = max(5, min(page_size, 100)) # batas 100 per halaman
        offset = (p - 1) * ps

        items = query.offset(offset).limit(ps).all()
        total_pages = max(1, (total_items + ps - 1) // ps)

        results = []
        for inst in items:
            results.append({
                "ticker": inst.ticker,
                "name": inst.name,
                "sector": inst.sector,
                "subsector": inst.subsector or inst.industry,
                "board": inst.board,
                "status": inst.status,
                "listing_date": inst.listing_date.strftime("%Y-%m-%d") if inst.listing_date else "-",
                "has_daily_data": inst.has_daily_data,
                "has_intraday_data": inst.has_intraday_data,
                "last_synced_at": inst.last_synced_at.strftime("%Y-%m-%d %H:%M") if inst.last_synced_at else "-"
            })

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": p,
            "page_size": ps,
            "items": results
        }

    def mark_status(self, ticker: str, new_status: str):
        """Memperbarui status emiten (ACTIVE, SUSPENDED, DELISTED, NEWLY_LISTED)."""
        inst = self.db.query(Instrument).filter(Instrument.ticker == ticker.upper()).first()
        if inst:
            status_clean = new_status.upper().strip()
            inst.status = status_clean
            inst.is_active = (status_clean in ["ACTIVE", "NEWLY_LISTED"])
            inst.is_suspended = (status_clean == "SUSPENDED")
            if status_clean == "DELISTED":
                inst.delisting_date = datetime.utcnow().date()
            inst.updated_at = datetime.utcnow()
            self.db.commit()

    def get_coverage_statistics(self) -> Dict[str, Any]:
        return get_idx_coverage_stats(self.db)
