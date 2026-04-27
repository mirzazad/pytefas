"""TEFAS API'sinin döndürdüğü kısa kodları okunabilir alan adlarına eşler."""

# Portföy dağılımı (dagilimSiraliGetirT) - yüzde alanları
DIST_FIELDS = {
    "fonKodu":  "fund_code",
    "fonUnvan": "fund_name",
    "tarih":    "date",
    # Borçlanma araçları
    "hs":    "stock_pct",
    "dt":    "government_bond_pct",
    "hb":    "treasury_bill_pct",
    "fb":    "financing_bill_pct",
    "ost":   "private_sector_bond_pct",
    "bb":    "bank_bill_pct",
    "vdm":   "asset_backed_securities_pct",
    "eut":   "eurobond_pct",
    "kibd":  "government_external_debt_pct",
    "osdb":  "private_sector_external_debt_pct",
    "kba":   "fx_government_internal_debt_pct",
    "dot":   "fx_payable_bill_pct",
    "db":    "fx_payable_bond_pct",
    # Para piyasası
    "tpp":   "takasbank_money_market_pct",
    "bpp":   "bist_money_market_pct",
    "btaa":  "bist_committed_buy_pct",
    "btas":  "bist_committed_sell_pct",
    "r":     "repo_pct",
    "tr":    "reverse_repo_pct",
    # Mevduat
    "vm":    "term_deposit_pct",
    "vmtl":  "deposit_tl_pct",
    "vmd":   "deposit_fx_pct",
    "vmau":  "deposit_gold_pct",
    "kh":    "participation_account_pct",
    "khtl":  "participation_account_tl_pct",
    "khd":   "participation_account_fx_pct",
    "khau":  "participation_account_gold_pct",
    # Kira sertifikaları
    "kks":   "government_lease_certificate_pct",
    "kkstl": "government_lease_certificate_tl_pct",
    "kksd":  "government_lease_certificate_fx_pct",
    "kksyd": "government_foreign_lease_certificate_pct",
    "osks":  "private_sector_lease_certificate_pct",
    "oksyd": "private_sector_foreign_lease_certificate_pct",
    # Kıymetli madenler
    "km":    "precious_metals_pct",
    "kmbyf": "precious_metals_etf_pct",
    "kmkba": "precious_metals_government_debt_pct",
    "kmkks": "precious_metals_lease_certificate_pct",
    # Yabancı menkul kıymetler
    "ymk":   "foreign_security_pct",
    "yba":   "foreign_debt_security_pct",
    "ybkb":  "foreign_government_debt_pct",
    "ybosb": "foreign_private_sector_debt_pct",
    "yhs":   "foreign_stock_pct",
    "ybyf":  "foreign_etf_pct",
    # Fon katılma payları
    "fkb":   "fund_participation_certificate_pct",
    "yyf":   "investment_fund_pct",
    "byf":   "etf_pct",
    "gykb":  "real_estate_fund_pct",
    "gyy":   "real_estate_investment_pct",
    "gsykb": "venture_capital_fund_pct",
    "gsyy":  "venture_capital_investment_pct",
    # Diğer
    "t":     "derivative_pct",
    "vint":  "futures_cash_collateral_pct",
    "gas":   "real_estate_certificate_pct",
    "d":     "other_pct",
}

# Fon genel bilgi (fonGnlBlgSiraliGetir)
INFO_FIELDS = {
    "fonKodu":         "fund_code",
    "fonUnvan":        "fund_name",
    "tarih":           "date",
    "fiyat":           "price",
    "tedPaySayisi":    "shares_outstanding",
    "kisiSayisi":      "investor_count",
    "portfoyBuyukluk": "portfolio_size",
    "borsaBultenFiyat": "exchange_bulletin_price",
}

# Geçerli fon tipleri
FUND_KINDS = ("YAT", "EMK", "BYF")
