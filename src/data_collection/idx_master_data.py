"""Authoritative Master Database & Universe Registry for Indonesia Stock Exchange (BEI/IDX).
Mendukung seluruh emiten BEI dengan klasifikasi 12 sektor IDX-IC resmi,
pelacakan status (ACTIVE, SUSPENDED, NEWLY_LISTED, DELISTED), papan pencatatan,
dan transparansi ketersediaan data provider.
"""
import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from config.idx_constants import IDX_SECTORS, IDX_BOARDS, IDX_STATUSES
from database.connection import SessionLocal
from database.models import Instrument


# Comprehensive Master Seed Data covering IDX-IC Sectors, Boards, and Statuses
IDX_MASTER_SEED: List[Dict[str, Any]] = [
    # 1. Financials (Keuangan)
    {"ticker": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Major Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2000-05-31"},
    {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Micro & Retail Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2003-11-10"},
    {"ticker": "BMRI", "name": "Bank Mandiri Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Corporate & Commercial Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2003-07-14"},
    {"ticker": "BBNI", "name": "Bank Negara Indonesia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Corporate Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "1996-11-25"},
    {"ticker": "BRIS", "name": "Bank Syariah Indonesia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Islamic Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2018-05-09"},
    {"ticker": "BBTN", "name": "Bank Tabungan Negara Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Mortgage Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2009-12-17"},
    {"ticker": "BDMN", "name": "Bank Danamon Indonesia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Commercial Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-12-06"},
    {"ticker": "BNGA", "name": "Bank CIMB Niaga Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Commercial Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-11-29"},
    {"ticker": "ARTO", "name": "Bank Jago Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Digital Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2016-01-12"},
    {"ticker": "MEGA", "name": "Bank Mega Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Retail Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "2000-04-17"},
    {"ticker": "BNLI", "name": "Bank Permata Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Commercial Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-01-15"},
    {"ticker": "PNBN", "name": "Bank Pan Indonesia Tbk", "sector": "Financials", "subsector": "Banks", "industry": "Commercial Banks", "board": "Utama", "status": "ACTIVE", "listing_date": "1982-12-29"},
    {"ticker": "ADMF", "name": "Adira Dinamika Multi Finance Tbk", "sector": "Financials", "subsector": "Consumer Financing", "industry": "Automotive Financing", "board": "Utama", "status": "ACTIVE", "listing_date": "2004-03-31"},
    {"ticker": "BFIN", "name": "BFI Finance Indonesia Tbk", "sector": "Financials", "subsector": "Consumer Financing", "industry": "Multi Financing", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-05-18"},

    # 2. Energy (Energi)
    {"ticker": "ADRO", "name": "Adaro Energy Indonesia Tbk", "sector": "Energy", "subsector": "Coal", "industry": "Thermal Coal", "board": "Utama", "status": "ACTIVE", "listing_date": "2008-07-16"},
    {"ticker": "PTBA", "name": "Bukit Asam Tbk", "sector": "Energy", "subsector": "Coal", "industry": "State Coal Mining", "board": "Utama", "status": "ACTIVE", "listing_date": "2002-12-23"},
    {"ticker": "PGAS", "name": "Perusahaan Gas Negara Tbk", "sector": "Energy", "subsector": "Oil & Gas", "industry": "Gas Distribution", "board": "Utama", "status": "ACTIVE", "listing_date": "2003-12-15"},
    {"ticker": "MEDC", "name": "Medco Energi Internasional Tbk", "sector": "Energy", "subsector": "Oil & Gas", "industry": "Oil & Gas Exploration", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-10-12"},
    {"ticker": "BREN", "name": "Barito Renewables Energy Tbk", "sector": "Energy", "subsector": "Renewable Energy", "industry": "Geothermal Power", "board": "Utama", "status": "ACTIVE", "listing_date": "2023-10-09"},
    {"ticker": "PGEO", "name": "Pertamina Geothermal Energy Tbk", "sector": "Energy", "subsector": "Renewable Energy", "industry": "Geothermal Power", "board": "Utama", "status": "ACTIVE", "listing_date": "2023-02-24"},
    {"ticker": "AKRA", "name": "AKR Corporindo Tbk", "sector": "Energy", "subsector": "Oil & Gas", "industry": "Fuel Distribution & Logistics", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-10-03"},
    {"ticker": "ITMG", "name": "Indo Tambangraya Megah Tbk", "sector": "Energy", "subsector": "Coal", "industry": "High-Calorie Coal", "board": "Utama", "status": "ACTIVE", "listing_date": "2007-12-18"},
    {"ticker": "INDY", "name": "Indika Energy Tbk", "sector": "Energy", "subsector": "Coal", "industry": "Diversified Energy", "board": "Utama", "status": "ACTIVE", "listing_date": "2008-06-11"},
    {"ticker": "ENRG", "name": "Energi Mega Persada Tbk", "sector": "Energy", "subsector": "Oil & Gas", "industry": "Oil & Gas Exploration", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2004-06-07"},
    {"ticker": "ELSA", "name": "Elnusa Tbk", "sector": "Energy", "subsector": "Oil & Gas Services", "industry": "Upstream Support", "board": "Utama", "status": "ACTIVE", "listing_date": "2008-02-06"},
    {"ticker": "DOID", "name": "Delta Dunia Makmur Tbk", "sector": "Energy", "subsector": "Coal Services", "industry": "Mining Contracting", "board": "Utama", "status": "ACTIVE", "listing_date": "2001-07-24"},
    {"ticker": "RAJA", "name": "Rukun Raharja Tbk", "sector": "Energy", "subsector": "Oil & Gas", "industry": "Gas Infrastructure", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2006-01-19"},

    # 3. Basic Materials (Barang Baku)
    {"ticker": "ANTM", "name": "Aneka Tambang Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Nickel, Gold & Bauxite", "board": "Utama", "status": "ACTIVE", "listing_date": "1997-11-27"},
    {"ticker": "INCO", "name": "Vale Indonesia Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Nickel Mining", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-05-16"},
    {"ticker": "MDKA", "name": "Merdeka Copper Gold Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Gold & Copper", "board": "Utama", "status": "ACTIVE", "listing_date": "2015-06-19"},
    {"ticker": "AMMN", "name": "Amman Mineral Internasional Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Copper & Gold", "board": "Utama", "status": "ACTIVE", "listing_date": "2023-07-07"},
    {"ticker": "TPIA", "name": "Chandra Asri Pacific Tbk", "sector": "Basic Materials", "subsector": "Chemicals", "industry": "Petrochemicals", "board": "Utama", "status": "ACTIVE", "listing_date": "2008-05-26"},
    {"ticker": "BRPT", "name": "Barito Pacific Tbk", "sector": "Basic Materials", "subsector": "Chemicals", "industry": "Diversified Chemicals", "board": "Utama", "status": "ACTIVE", "listing_date": "1993-10-01"},
    {"ticker": "INKP", "name": "Indah Kiat Pulp & Paper Tbk", "sector": "Basic Materials", "subsector": "Paper & Forestry", "industry": "Pulp & Paper", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-07-16"},
    {"ticker": "TKIM", "name": "Pabrik Kertas Tjiwi Kimia Tbk", "sector": "Basic Materials", "subsector": "Paper & Forestry", "industry": "Paper Production", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-04-03"},
    {"ticker": "SMGR", "name": "Semen Indonesia Tbk", "sector": "Basic Materials", "subsector": "Building Materials", "industry": "Cement", "board": "Utama", "status": "ACTIVE", "listing_date": "1991-09-09"},
    {"ticker": "INTP", "name": "Indocement Tunggal Prakarsa Tbk", "sector": "Basic Materials", "subsector": "Building Materials", "industry": "Cement", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-12-05"},
    {"ticker": "NCKL", "name": "Trimegah Bangun Persada Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Nickel Processing", "board": "Utama", "status": "ACTIVE", "listing_date": "2023-04-12"},
    {"ticker": "MBMA", "name": "Merdeka Battery Materials Tbk", "sector": "Basic Materials", "subsector": "Metals & Minerals", "industry": "Battery Minerals", "board": "Utama", "status": "ACTIVE", "listing_date": "2023-04-18"},
    {"ticker": "ESSA", "name": "Essence Indonesia Tbk", "sector": "Basic Materials", "subsector": "Chemicals", "industry": "Ammonia & LPG", "board": "Utama", "status": "ACTIVE", "listing_date": "2012-02-01"},

    # 4. Consumer Non-Cyclicals (Barang Konsumen Primer)
    {"ticker": "ICBP", "name": "Indofood CBP Sukses Makmur Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Food & Beverages", "industry": "Packaged Food", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-10-07"},
    {"ticker": "INDF", "name": "Indofood Sukses Makmur Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Food & Beverages", "industry": "Agribusiness & Food", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-07-14"},
    {"ticker": "UNVR", "name": "Unilever Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Personal Care", "industry": "Home & Personal Care", "board": "Utama", "status": "ACTIVE", "listing_date": "1982-01-11"},
    {"ticker": "MYOR", "name": "Mayora Indah Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Food & Beverages", "industry": "Confectionery & Biscuits", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-07-04"},
    {"ticker": "CPIN", "name": "Charoen Pokphand Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Agricultural Products", "industry": "Poultry & Feedmill", "board": "Utama", "status": "ACTIVE", "listing_date": "1991-01-15"},
    {"ticker": "JPFA", "name": "Japfa Comfeed Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Agricultural Products", "industry": "Poultry & Livestock", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-10-23"},
    {"ticker": "CMRY", "name": "Cisarua Mountain Dairy Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Food & Beverages", "industry": "Dairy & Premium Sausage", "board": "Utama", "status": "ACTIVE", "listing_date": "2021-12-06"},
    {"ticker": "HMSP", "name": "H.M. Sampoerna Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Tobacco", "industry": "Cigarettes", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-08-15"},
    {"ticker": "GGRM", "name": "Gudang Garam Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Tobacco", "industry": "Cigarettes", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-08-27"},
    {"ticker": "AMRT", "name": "Sumber Alfaria Trijaya Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Retail", "industry": "Minimarket Chain", "board": "Utama", "status": "ACTIVE", "listing_date": "2009-01-15"},
    {"ticker": "MIDI", "name": "Midi Utama Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Retail", "industry": "Convenience Store", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-11-30"},
    {"ticker": "AALI", "name": "Astra Agro Lestari Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Agricultural Products", "industry": "Palm Oil (CPO)", "board": "Utama", "status": "ACTIVE", "listing_date": "1997-12-09"},
    {"ticker": "TAPG", "name": "Triputra Agro Persada Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Agricultural Products", "industry": "Palm Oil (CPO)", "board": "Utama", "status": "ACTIVE", "listing_date": "2021-04-12"},

    # 5. Consumer Cyclicals (Barang Konsumen Non-Primer)
    {"ticker": "MAPI", "name": "Mitra Adiperkasa Tbk", "sector": "Consumer Cyclicals", "subsector": "Retailing", "industry": "Lifestyle Retail", "board": "Utama", "status": "ACTIVE", "listing_date": "2004-11-10"},
    {"ticker": "MAPA", "name": "MAP Aktif Adiperkasa Tbk", "sector": "Consumer Cyclicals", "subsector": "Retailing", "industry": "Sports & Kids Retail", "board": "Utama", "status": "ACTIVE", "listing_date": "2018-07-05"},
    {"ticker": "ACES", "name": "Aspirasi Hidup Indonesia Tbk (ex-Ace)", "sector": "Consumer Cyclicals", "subsector": "Retailing", "industry": "Home Improvement", "board": "Utama", "status": "ACTIVE", "listing_date": "2007-11-06"},
    {"ticker": "ERAA", "name": "Erajaya Swasembada Tbk", "sector": "Consumer Cyclicals", "subsector": "Retailing", "industry": "Gadget & Electronics", "board": "Utama", "status": "ACTIVE", "listing_date": "2011-12-14"},
    {"ticker": "AUTO", "name": "Astra Otoparts Tbk", "sector": "Consumer Cyclicals", "subsector": "Automotive Components", "industry": "Auto Parts", "board": "Utama", "status": "ACTIVE", "listing_date": "1998-06-15"},
    {"ticker": "DRMA", "name": "Dharma Polimetal Tbk", "sector": "Consumer Cyclicals", "subsector": "Automotive Components", "industry": "EV & Auto Parts", "board": "Utama", "status": "ACTIVE", "listing_date": "2021-12-20"},
    {"ticker": "SMSM", "name": "Selamat Sempurna Tbk", "sector": "Consumer Cyclicals", "subsector": "Automotive Components", "industry": "Automotive Filters", "board": "Utama", "status": "ACTIVE", "listing_date": "1996-09-09"},
    {"ticker": "GJTL", "name": "Gajah Tunggal Tbk", "sector": "Consumer Cyclicals", "subsector": "Automotive Components", "industry": "Tires", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-05-08"},
    {"ticker": "MNCN", "name": "Media Nusantara Citra Tbk", "sector": "Consumer Cyclicals", "subsector": "Media & Entertainment", "industry": "Broadcasting & Content", "board": "Utama", "status": "ACTIVE", "listing_date": "2007-06-22"},
    {"ticker": "SCMA", "name": "Surya Citra Media Tbk", "sector": "Consumer Cyclicals", "subsector": "Media & Entertainment", "industry": "Television & Streaming", "board": "Utama", "status": "ACTIVE", "listing_date": "2002-07-16"},

    # 6. Healthcare (Kesehatan)
    {"ticker": "KLBF", "name": "Kalbe Farma Tbk", "sector": "Healthcare", "subsector": "Pharmaceuticals", "industry": "Prescription & Consumer Health", "board": "Utama", "status": "ACTIVE", "listing_date": "1991-07-30"},
    {"ticker": "MIKA", "name": "Mitra Keluarga Karyasehat Tbk", "sector": "Healthcare", "subsector": "Healthcare Services", "industry": "Hospitals", "board": "Utama", "status": "ACTIVE", "listing_date": "2015-03-24"},
    {"ticker": "HEAL", "name": "Medikaloka Hermina Tbk", "sector": "Healthcare", "subsector": "Healthcare Services", "industry": "Mother & Child Hospitals", "board": "Utama", "status": "ACTIVE", "listing_date": "2018-05-16"},
    {"ticker": "SILO", "name": "Siloam International Hospitals Tbk", "sector": "Healthcare", "subsector": "Healthcare Services", "industry": "Premium Hospitals", "board": "Utama", "status": "ACTIVE", "listing_date": "2013-09-12"},
    {"ticker": "SIDO", "name": "Industri Jamu Dan Farmasi Sido Muncul Tbk", "sector": "Healthcare", "subsector": "Herbal Medicine", "industry": "Herbal Supplements", "board": "Utama", "status": "ACTIVE", "listing_date": "2013-12-18"},
    {"ticker": "PRDA", "name": "Prodia Widyahusada Tbk", "sector": "Healthcare", "subsector": "Healthcare Services", "industry": "Clinical Laboratory", "board": "Utama", "status": "ACTIVE", "listing_date": "2016-12-07"},
    {"ticker": "TSPC", "name": "Tempo Scan Pacific Tbk", "sector": "Healthcare", "subsector": "Pharmaceuticals", "industry": "Consumer Health", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-06-17"},

    # 7. Technology (Teknologi)
    {"ticker": "GOTO", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Technology", "subsector": "Online Services", "industry": "On-Demand & FinTech", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2022-04-11"},
    {"ticker": "BUKA", "name": "Bukalapak.com Tbk", "sector": "Technology", "subsector": "Online Services", "industry": "E-Commerce", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2021-08-06"},
    {"ticker": "EMTK", "name": "Elang Mahkota Teknologi Tbk", "sector": "Technology", "subsector": "Technology Conglomerate", "industry": "Tech & Media Investment", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-01-12"},
    {"ticker": "BELI", "name": "Global Digital Niaga Tbk (Blibli)", "sector": "Technology", "subsector": "Online Services", "industry": "Omnichannel Commerce", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2022-11-08"},
    {"ticker": "DCII", "name": "DCI Indonesia Tbk", "sector": "Technology", "subsector": "IT Services", "industry": "Tier-4 Data Center", "board": "Utama", "status": "ACTIVE", "listing_date": "2021-01-06"},
    {"ticker": "MTDL", "name": "Metrodata Electronics Tbk", "sector": "Technology", "subsector": "IT Hardware & Solutions", "industry": "IT Distribution & Solutions", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-04-09"},
    {"ticker": "WIRG", "name": "WIR ASIA Tbk", "sector": "Technology", "subsector": "Software & Tech", "industry": "AR & Metaverse Solutions", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2022-04-04"},
    {"ticker": "MCAS", "name": "M Cash Integrasi Tbk", "sector": "Technology", "subsector": "Digital Infrastructure", "industry": "Digital Distribution Kiosks", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "2017-11-01"},

    # 8. Infrastructures (Infrastruktur)
    {"ticker": "TLKM", "name": "Telkom Indonesia Tbk", "sector": "Infrastructures", "subsector": "Telecommunication", "industry": "Integrated Telecoms", "board": "Utama", "status": "ACTIVE", "listing_date": "1995-11-14"},
    {"ticker": "ISAT", "name": "Indosat Ooredoo Hutchison Tbk", "sector": "Infrastructures", "subsector": "Telecommunication", "industry": "Wireless Telecoms", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-10-19"},
    {"ticker": "EXCL", "name": "XL Axiata Tbk", "sector": "Infrastructures", "subsector": "Telecommunication", "industry": "Wireless Telecoms", "board": "Utama", "status": "ACTIVE", "listing_date": "2005-09-29"},
    {"ticker": "TOWR", "name": "Sarana Menara Nusantara Tbk", "sector": "Infrastructures", "subsector": "Telecom Infrastructure", "industry": "Telecom Towers & Fiber", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-03-08"},
    {"ticker": "TBIG", "name": "Tower Bersama Infrastructure Tbk", "sector": "Infrastructures", "subsector": "Telecom Infrastructure", "industry": "Telecom Towers", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-10-26"},
    {"ticker": "JSMR", "name": "Jasa Marga Tbk", "sector": "Infrastructures", "subsector": "Toll Roads", "industry": "Highway Operator", "board": "Utama", "status": "ACTIVE", "listing_date": "2007-11-12"},
    {"ticker": "MTEL", "name": "Dayamitra Telekomunikasi Tbk (Mitratel)", "sector": "Infrastructures", "subsector": "Telecom Infrastructure", "industry": "Telecom Towers", "board": "Utama", "status": "ACTIVE", "listing_date": "2021-11-22"},
    {"ticker": "PTPP", "name": "PP (Persero) Tbk", "sector": "Infrastructures", "subsector": "Construction", "industry": "Civil & Building Construction", "board": "Utama", "status": "ACTIVE", "listing_date": "2010-02-09"},
    {"ticker": "ADHI", "name": "Adhi Karya (Persero) Tbk", "sector": "Infrastructures", "subsector": "Construction", "industry": "Infrastructure Construction", "board": "Utama", "status": "ACTIVE", "listing_date": "2004-03-18"},
    {"ticker": "WIKA", "name": "Wijaya Karya (Persero) Tbk", "sector": "Infrastructures", "subsector": "Construction", "industry": "State Construction", "board": "Pemantauan Khusus", "status": "SUSPENDED", "listing_date": "2007-10-29"},

    # 9. Industrials (Perindustrian)
    {"ticker": "ASII", "name": "Astra International Tbk", "sector": "Industrials", "subsector": "Diversified Industrials", "industry": "Automotive, Heavy Machinery & Mining", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-04-04"},
    {"ticker": "UNTR", "name": "United Tractors Tbk", "sector": "Industrials", "subsector": "Heavy Machinery", "industry": "Mining Equipment & Contracting", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-09-19"},
    {"ticker": "HEXA", "name": "Hexindo Adiperkasa Tbk", "sector": "Industrials", "subsector": "Heavy Machinery", "industry": "Hitachi Equipment Distributor", "board": "Utama", "status": "ACTIVE", "listing_date": "1995-02-13"},
    {"ticker": "ARNA", "name": "Arwana Citramulia Tbk", "sector": "Industrials", "subsector": "Building Materials", "industry": "Ceramic Tiles", "board": "Utama", "status": "ACTIVE", "listing_date": "2001-07-17"},
    {"ticker": "MARK", "name": "Mark Dynamics Indonesia Tbk", "sector": "Industrials", "subsector": "Industrial Goods", "industry": "Nitrile Glove Formers", "board": "Utama", "status": "ACTIVE", "listing_date": "2017-07-12"},
    {"ticker": "BMTR", "name": "Global Mediacom Tbk", "sector": "Industrials", "subsector": "Holding Company", "industry": "Media & Telecom Holdings", "board": "Utama", "status": "ACTIVE", "listing_date": "1995-07-17"},

    # 10. Properties & Real Estate (Properti & Real Estat)
    {"ticker": "BSDE", "name": "Bumi Serpong Damai Tbk", "sector": "Properties & Real Estate", "subsector": "Real Estate Development", "industry": "Township Development", "board": "Utama", "status": "ACTIVE", "listing_date": "2008-06-06"},
    {"ticker": "CTRA", "name": "Ciputra Development Tbk", "sector": "Properties & Real Estate", "subsector": "Real Estate Development", "industry": "Residential & Commercial", "board": "Utama", "status": "ACTIVE", "listing_date": "1994-03-28"},
    {"ticker": "PWON", "name": "Pakuwon Jati Tbk", "sector": "Properties & Real Estate", "subsector": "Real Estate Development", "industry": "Retail Malls & Condominiums", "board": "Utama", "status": "ACTIVE", "listing_date": "1989-10-09"},
    {"ticker": "SMRA", "name": "Summarecon Agung Tbk", "sector": "Properties & Real Estate", "subsector": "Real Estate Development", "industry": "Integrated Townships", "board": "Utama", "status": "ACTIVE", "listing_date": "1990-05-07"},
    {"ticker": "ASRI", "name": "Alam Sutera Realty Tbk", "sector": "Properties & Real Estate", "subsector": "Real Estate Development", "industry": "Townships & High-Rise", "board": "Utama", "status": "ACTIVE", "listing_date": "2007-12-18"},
    {"ticker": "SSIA", "name": "Surya Semesta Internusa Tbk", "sector": "Properties & Real Estate", "subsector": "Industrial Estates", "industry": "Subang Smartpolitan", "board": "Utama", "status": "ACTIVE", "listing_date": "1997-03-27"},
    {"ticker": "KIJA", "name": "Kawasan Industri Jababeka Tbk", "sector": "Properties & Real Estate", "subsector": "Industrial Estates", "industry": "Industrial City", "board": "Pengembangan", "status": "ACTIVE", "listing_date": "1994-01-10"},

    # 11. Transportation & Logistic (Transportasi & Logistik)
    {"ticker": "BIRD", "name": "Blue Bird Tbk", "sector": "Transportation & Logistic", "subsector": "Passenger Transportation", "industry": "Taxi & Mobility Services", "board": "Utama", "status": "ACTIVE", "listing_date": "2014-11-05"},
    {"ticker": "SMDR", "name": "Samudera Indonesia Tbk", "sector": "Transportation & Logistic", "subsector": "Maritime Logistics", "industry": "Container Shipping", "board": "Utama", "status": "ACTIVE", "listing_date": "1999-07-05"},
    {"ticker": "ASSA", "name": "Adi Sarana Armada Tbk", "sector": "Transportation & Logistic", "subsector": "Logistics & Rental", "industry": "Anteraja & Vehicle Rental", "board": "Utama", "status": "ACTIVE", "listing_date": "2012-11-12"},
    {"ticker": "TMAS", "name": "Temas Tbk", "sector": "Transportation & Logistic", "subsector": "Maritime Logistics", "industry": "Domestic Sea Freight", "board": "Utama", "status": "ACTIVE", "listing_date": "2003-07-09"},
    {"ticker": "IPCC", "name": "Indonesia Kendaraan Terminal Tbk", "sector": "Transportation & Logistic", "subsector": "Port Services", "industry": "Car Terminal Operator", "board": "Utama", "status": "ACTIVE", "listing_date": "2018-07-09"},
    {"ticker": "GIAA", "name": "Garuda Indonesia (Persero) Tbk", "sector": "Transportation & Logistic", "subsector": "Airlines", "industry": "National Flag Carrier", "board": "Pemantauan Khusus", "status": "SUSPENDED", "listing_date": "2011-02-11"},

    # 12. Listed Investment Products & Acceleration / Newly Listed / Delisted Historical
    {"ticker": "PRAY", "name": "Fimperkasa Utama Tbk", "sector": "Listed Investment Products", "subsector": "Special Purpose", "industry": "Investment Entity", "board": "Akselerasi", "status": "ACTIVE", "listing_date": "2021-04-09"},
    {"ticker": "UVCR", "name": "Trimegah Karya Pratama Tbk", "sector": "Technology", "subsector": "Vouchers & FinTech", "industry": "Ultra Voucher", "board": "Akselerasi", "status": "ACTIVE", "listing_date": "2021-07-27"},
    {"ticker": "NSSS", "name": "Nusantara Sawit Sejahtera Tbk", "sector": "Consumer Non-Cyclicals", "subsector": "Plantations", "industry": "Palm Oil", "board": "Pengembangan", "status": "NEWLY_LISTED", "listing_date": "2024-03-10"},
    {"ticker": "BATR", "name": "Benteng Anugerah Sejahtera Tbk", "sector": "Industrials", "subsector": "Construction Supply", "industry": "Industrial Supply", "board": "Akselerasi", "status": "NEWLY_LISTED", "listing_date": "2024-05-15"},
    {"ticker": "SRIL", "name": "Sri Rejeki Isman Tbk", "sector": "Consumer Cyclicals", "subsector": "Textiles", "industry": "Garment & Military Textiles", "board": "Pemantauan Khusus", "status": "SUSPENDED", "listing_date": "2013-06-17"},
    {"ticker": "COWL", "name": "Cowell Development Tbk", "sector": "Properties & Real Estate", "subsector": "Property", "industry": "Property Developer", "board": "Pemantauan Khusus", "status": "DELISTED", "listing_date": "2007-12-19"}
]

# Dynamically load full comprehensive universe (740+ IDX emiten) if available
_full_universe_file = os.path.join(os.path.dirname(__file__), "idx_full_universe.json")
if os.path.exists(_full_universe_file):
    try:
        with open(_full_universe_file, "r", encoding="utf-8") as _f:
            _loaded_uni = json.load(_f)
            if len(_loaded_uni) > len(IDX_MASTER_SEED):
                IDX_MASTER_SEED = _loaded_uni
    except Exception:
        pass


def seed_idx_master_database(db: Optional[Session] = None, force_refresh: bool = False) -> int:
    """Mengisi atau memperbarui database instrumen dengan seluruh emiten master BEI."""
    session = db or SessionLocal()
    try:
        count = 0
        now = datetime.utcnow()
        for item in IDX_MASTER_SEED:
            ticker = item["ticker"].upper().strip()
            existing = session.query(Instrument).filter(Instrument.ticker == ticker).first()
            
            listing_d = None
            if item.get("listing_date"):
                try:
                    listing_d = datetime.strptime(item["listing_date"], "%Y-%m-%d").date()
                except Exception:
                    pass

            is_active = (item.get("status") in ["ACTIVE", "NEWLY_LISTED"])
            is_suspended = (item.get("status") == "SUSPENDED")

            if existing:
                if force_refresh:
                    existing.name = item["name"]
                    existing.sector = item.get("sector")
                    existing.subsector = item.get("subsector")
                    existing.industry = item.get("industry")
                    existing.board = item.get("board", "Utama")
                    existing.status = item.get("status", "ACTIVE")
                    existing.is_active = is_active
                    existing.is_suspended = is_suspended
                    existing.listing_date = listing_d or existing.listing_date
                    existing.last_synced_at = now
                    existing.updated_at = now
            else:
                new_inst = Instrument(
                    ticker=ticker,
                    name=item["name"],
                    sector=item.get("sector", "General"),
                    subsector=item.get("subsector", "General"),
                    industry=item.get("industry", "General"),
                    board=item.get("board", "Utama"),
                    status=item.get("status", "ACTIVE"),
                    is_active=is_active,
                    is_suspended=is_suspended,
                    listing_date=listing_d,
                    has_daily_data=True,
                    has_intraday_data=True,
                    last_synced_at=now,
                    created_at=now,
                    updated_at=now
                )
                session.add(new_inst)
            count += 1

        session.commit()
        return count
    except Exception as e:
        session.rollback()
        print(f"[IDX Master Data] Error seeding database: {e}")
        return 0
    finally:
        if not db:
            session.close()


def get_idx_coverage_stats(db: Optional[Session] = None) -> Dict[str, Any]:
    """Mengambil metrik cakupan dan statistik kelengkapan data pasar BEI."""
    session = db or SessionLocal()
    try:
        total_listed = session.query(Instrument).count()
        active_count = session.query(Instrument).filter(Instrument.status.in_(["ACTIVE", "NEWLY_LISTED"])).count()
        suspended_count = session.query(Instrument).filter(Instrument.status == "SUSPENDED").count()
        delisted_count = session.query(Instrument).filter(Instrument.status == "DELISTED").count()
        newly_listed = session.query(Instrument).filter(Instrument.status == "NEWLY_LISTED").count()

        # Grouping per 12 IDX-IC Sectors
        sector_counts = {}
        for sec_key, sec_val in IDX_SECTORS.items():
            c = session.query(Instrument).filter(Instrument.sector == sec_val["name_en"]).count()
            sector_counts[sec_val["name_en"]] = c

        # Provider data capability
        has_daily = session.query(Instrument).filter(Instrument.has_daily_data == True).count()
        has_intraday = session.query(Instrument).filter(Instrument.has_intraday_data == True).count()
        no_data = total_listed - max(has_daily, has_intraday)

        latest_sync = session.query(Instrument.last_synced_at).order_by(Instrument.last_synced_at.desc()).first()
        last_sync_time = latest_sync[0].isoformat() if latest_sync and latest_sync[0] else datetime.utcnow().isoformat()

        return {
            "total_listed_idx": total_listed,
            "active_stocks": active_count,
            "suspended_stocks": suspended_count,
            "delisted_stocks": delisted_count,
            "newly_listed_stocks": newly_listed,
            "sectors_distribution": sector_counts,
            "coverage_breakdown": {
                "available_in_provider": active_count,
                "has_sufficient_daily_data": has_daily,
                "has_intraday_data": has_intraday,
                "no_data_or_unsupported": max(0, no_data)
            },
            "last_synced_at": last_sync_time
        }
    finally:
        if not db:
            session.close()
