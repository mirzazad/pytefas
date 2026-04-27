"""pytefas için temel testler.

Network'e gerçek bir istek atar - TEFAS canlı olmalı. Offline testler için
mock ekleyebiliriz ileride.
"""
import pandas as pd
import pytest

from pytefas import Crawler


@pytest.fixture(scope="module")
def crawler():
    return Crawler()


def test_fetch_info_yat(crawler):
    df = crawler.fetch("2026-04-24", columns="info", kind="YAT")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # Beklenen sütunlar
    for col in ("date", "kind", "fund_code", "fund_name", "price", "portfolio_size"):
        assert col in df.columns, f"Eksik sütun: {col}"
    # Sağlık kontrolü
    assert df["kind"].unique().tolist() == ["YAT"]
    assert df["fund_code"].nunique() == len(df)
    # Fiyatlar 0 olabilir (yeni kurulmuş fon, kapanmış vs.) ama negatif olmamalı
    assert (df["price"].fillna(0) >= 0).all()
    assert (df["price"] > 0).any()


def test_fetch_breakdown_yat(crawler):
    df = crawler.fetch("2026-04-24", columns="breakdown", kind="YAT")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # Yüzde toplamı ~100 olmalı
    pct_cols = [c for c in df.columns if c.endswith("_pct")]
    totals = df[pct_cols].fillna(0).sum(axis=1)
    assert ((totals >= 95) & (totals <= 105)).all(), \
        f"Toplam yüzde 100 değil: min={totals.min()}, max={totals.max()}"


def test_fetch_holiday_returns_empty(crawler):
    # Pazar günü
    df = crawler.fetch("2026-04-26", columns="info", kind="YAT")
    assert df.empty


def test_fetch_many_combines_kinds(crawler):
    df = crawler.fetch_many("2026-04-24", columns="info")
    assert not df.empty
    kinds = set(df["kind"].unique())
    assert kinds == {"YAT", "EMK", "BYF"}


def test_invalid_kind_raises(crawler):
    with pytest.raises(ValueError):
        crawler.fetch("2026-04-24", kind="INVALID")


def test_invalid_columns_raises(crawler):
    with pytest.raises(ValueError):
        crawler.fetch("2026-04-24", columns="INVALID")


def test_fetch_long_range_chunks_automatically(crawler):
    """60 günlük aralık otomatik chunklanır (TEFAS API'si 1 ay sınırı uygular)."""
    df = crawler.fetch("2026-02-23", "2026-04-24", columns="info", kind="YAT")
    assert not df.empty
    # 60 gün içinde ~40+ iş günü olmalı
    assert df["date"].nunique() >= 30
    # AAK gibi köklü bir fon her gün olmalı
    aak = df[df["fund_code"] == "AAK"]
    assert len(aak) >= 30


def test_split_range_helper():
    """_split_range helper birim testi."""
    from datetime import datetime
    from pytefas.client import _split_range

    # Tek gün
    chunks = _split_range(datetime(2026, 4, 24), datetime(2026, 4, 24), 28)
    assert chunks == [(datetime(2026, 4, 24), datetime(2026, 4, 24))]

    # Tam 28 gün
    chunks = _split_range(datetime(2026, 4, 1), datetime(2026, 4, 28), 28)
    assert len(chunks) == 1

    # 29 gün -> 2 chunk
    chunks = _split_range(datetime(2026, 4, 1), datetime(2026, 4, 29), 28)
    assert len(chunks) == 2
    assert chunks[0] == (datetime(2026, 4, 1), datetime(2026, 4, 28))
    assert chunks[1] == (datetime(2026, 4, 29), datetime(2026, 4, 29))


def test_fetch_start_after_end_raises(crawler):
    from pytefas import TefasInvalidParameterError
    with pytest.raises(TefasInvalidParameterError):
        crawler.fetch("2026-04-24", "2026-04-20")
