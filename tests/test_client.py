"""pytefas için ağ bağımsız unit testler.

Bu testler TEFAS API'sine gitmez - sadece input validation ve helper
fonksiyonlarını test eder. Her platformda hızlı ve deterministik çalışır.

API entegrasyonu testleri için bkz. `test_canary.py`.
"""
from datetime import datetime

import pytest

from pytefas import (
    Crawler,
    TefasInvalidParameterError,
)


@pytest.fixture(scope="module")
def crawler():
    return Crawler()


def test_invalid_kind_raises(crawler):
    with pytest.raises(ValueError):
        crawler.fetch("2026-04-24", kind="INVALID")


def test_invalid_columns_raises(crawler):
    with pytest.raises(ValueError):
        crawler.fetch("2026-04-24", columns="INVALID")


def test_invalid_kind_raises_typed(crawler):
    """TefasInvalidParameterError fırlamalı (ValueError'dan da türer)."""
    with pytest.raises(TefasInvalidParameterError):
        crawler.fetch("2026-04-24", kind="INVALID")


def test_fetch_start_after_end_raises(crawler):
    with pytest.raises(TefasInvalidParameterError):
        crawler.fetch("2026-04-24", "2026-04-20")


def test_invalid_date_format_raises(crawler):
    with pytest.raises(TefasInvalidParameterError):
        crawler.fetch("not-a-date")


def test_split_range_single_day():
    from pytefas.client import _split_range
    chunks = _split_range(datetime(2026, 4, 24), datetime(2026, 4, 24), 28)
    assert chunks == [(datetime(2026, 4, 24), datetime(2026, 4, 24))]


def test_split_range_exact_28_days():
    from pytefas.client import _split_range
    chunks = _split_range(datetime(2026, 4, 1), datetime(2026, 4, 28), 28)
    assert len(chunks) == 1


def test_split_range_29_days_creates_two_chunks():
    from pytefas.client import _split_range
    chunks = _split_range(datetime(2026, 4, 1), datetime(2026, 4, 29), 28)
    assert len(chunks) == 2
    assert chunks[0] == (datetime(2026, 4, 1), datetime(2026, 4, 28))
    assert chunks[1] == (datetime(2026, 4, 29), datetime(2026, 4, 29))


def test_split_range_one_year_creates_13_chunks():
    from pytefas.client import _split_range
    chunks = _split_range(datetime(2025, 4, 1), datetime(2026, 4, 1), 28)
    # 365 gun / 28 ~= 14 chunk
    assert 13 <= len(chunks) <= 14
    # Hicbir chunk 28 gunden uzun olamaz
    for s, e in chunks:
        assert (e - s).days < 28


def test_parse_date_accepts_string():
    from pytefas.client import _parse_date
    assert _parse_date("2026-04-24") == datetime(2026, 4, 24)


def test_parse_date_accepts_yyyymmdd():
    from pytefas.client import _parse_date
    assert _parse_date("20260424") == datetime(2026, 4, 24)


def test_parse_date_accepts_datetime():
    from pytefas.client import _parse_date
    d = datetime(2026, 4, 24, 15, 30)
    assert _parse_date(d) == d


def test_parse_date_rejects_garbage():
    from pytefas.client import _parse_date
    with pytest.raises(TefasInvalidParameterError):
        _parse_date("not-a-date")


def test_fetch_signature_accepts_fund_code(crawler):
    """fetch() fund_code parametresini kabul eder (signature kontrolu)."""
    import inspect
    sig = inspect.signature(crawler.fetch)
    assert "fund_code" in sig.parameters
    assert sig.parameters["fund_code"].default is None


def test_fetch_many_signature_accepts_fund_code(crawler):
    """fetch_many() de fund_code parametresini kabul eder."""
    import inspect
    sig = inspect.signature(crawler.fetch_many)
    assert "fund_code" in sig.parameters


def test_post_json_retries_on_connection_error(monkeypatch):
    """ConnectionError sonrası başarılı response gelirse retry devreye girer."""
    import requests
    from pytefas._ratelimit import RateLimitedClient

    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = RateLimitedClient(timeout=5, max_retry=3)

    calls = {"n": 0}

    class _OkResp:
        status_code = 200
        text = '{"resultList": []}'
        headers: dict = {}

        def raise_for_status(self):
            pass

        def json(self):
            return {"resultList": []}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.ConnectionError("Remote end closed connection without response")
        return _OkResp()

    monkeypatch.setattr(client.session, "post", fake_post)
    out = client.post_json("https://example/x", {}, {})
    assert out == {"resultList": []}
    assert calls["n"] == 2


def test_post_json_retries_on_read_timeout(monkeypatch):
    """ReadTimeout sonrası başarılı response gelirse retry devreye girer."""
    import requests
    from pytefas._ratelimit import RateLimitedClient

    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = RateLimitedClient(timeout=5, max_retry=3)

    calls = {"n": 0}

    class _OkResp:
        status_code = 200
        text = '{"ok": 1}'
        headers: dict = {}

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": 1}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise requests.Timeout("Read timed out")
        return _OkResp()

    monkeypatch.setattr(client.session, "post", fake_post)
    out = client.post_json("https://example/x", {}, {})
    assert out == {"ok": 1}
    assert calls["n"] == 3


def test_post_json_raises_after_max_retries_exhausted(monkeypatch):
    """Sürekli ağ hatası → max_retry'dan sonra RuntimeError, son hata mesajda."""
    import requests
    from pytefas._ratelimit import RateLimitedClient

    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = RateLimitedClient(timeout=5, max_retry=2)

    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(client.session, "post", fake_post)
    with pytest.raises(RuntimeError, match="ConnectionError"):
        client.post_json("https://example/x", {}, {})
