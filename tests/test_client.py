"""pytefas için temel testler.

Network'e gerçek bir istek atar — TEFAS canlı olmalı. Offline testler için
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
