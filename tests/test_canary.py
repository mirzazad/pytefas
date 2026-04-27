"""
Canary testi: dinamik olarak son iş gününü kullanarak TEFAS API'sinin
çalıştığını doğrular.

Bu test sabit bir tarih kullanmaz, her zaman bugüne en yakın iş gününü
seçer, böylece TEFAS eski verileri kaldırsa bile bozulmaz.

GitHub Actions canary tarafından her pazartesi 16:00 UTC (TR 19:00)
çalıştırılır, bu saatte TEFAS günlük veriyi tamamlamış olur.
"""
from datetime import datetime, timedelta, timezone

import pytest

from pytefas import Crawler


def _last_business_day() -> str:
    """Bugünden geriye doğru gidip ilk iş gününü bulur."""
    today = datetime.now(timezone.utc).date()
    for offset in range(0, 8):
        d = today - timedelta(days=offset)
        if d.weekday() < 5:  # 0=Pazartesi, 4=Cuma
            return d.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")


@pytest.fixture(scope="module")
def crawler():
    return Crawler()


@pytest.fixture(scope="module")
def last_bd():
    return _last_business_day()


def test_api_responds_info(crawler, last_bd):
    """TEFAS info endpoint çalışıyor mu — son birkaç iş gününden birini dene."""
    last = datetime.strptime(last_bd, "%Y-%m-%d")
    df = None
    for back in range(0, 5):
        d = (last - timedelta(days=back)).strftime("%Y-%m-%d")
        df = crawler.fetch(d, columns="info", kind="YAT")
        if not df.empty:
            break
    assert df is not None and not df.empty, "Son 5 iş gününde de TEFAS info çekilemedi"
    assert len(df) > 100, f"Çok az fon döndü: {len(df)} (en az 100 olmalı)"


def test_api_responds_breakdown(crawler, last_bd):
    """TEFAS breakdown endpoint çalışıyor mu — yüzde toplamları ~100 olmalı."""
    last = datetime.strptime(last_bd, "%Y-%m-%d")
    df = None
    for back in range(0, 5):
        d = (last - timedelta(days=back)).strftime("%Y-%m-%d")
        df = crawler.fetch(d, columns="breakdown", kind="YAT")
        if not df.empty:
            break
    assert df is not None and not df.empty
    pct_cols = [c for c in df.columns if c.endswith("_pct")]
    assert pct_cols, "Hiç yüzde sütunu yok — schema bozulmuş olabilir"
    totals = df[pct_cols].fillna(0).sum(axis=1)
    valid_count = ((totals >= 95) & (totals <= 105)).sum()
    assert valid_count > len(df) * 0.95, \
        f"Fonların %95'inden azı geçerli yüzde toplamına sahip ({valid_count}/{len(df)})"
