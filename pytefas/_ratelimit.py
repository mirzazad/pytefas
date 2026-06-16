"""TEFAS API'si dakikada 6 istek sınırına sahiptir.

Bu modül 429 ve boş response durumlarını otomatik handle eder, kalan kotayı
takip ederek bir sonraki çağrıyı geciktirir.
"""
from __future__ import annotations

import time
from typing import Any, Dict

import requests


class RateLimitedClient:
    """Rate-limit bilincine sahip basit POST istemcisi."""

    def __init__(self, timeout: int = 60, max_retry: int = 5):
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retry = max_retry

    def post_json(self, url: str, body: dict, headers: Dict[str, str]) -> Dict[str, Any]:
        """JSON body POST eder. 429, boş response ve ağ hatalarında yeniden dener.

        Yeniden denenen durumlar:
        - HTTP 429 (rate-limit)
        - HTTP 200 boş gövde
        - JSON parse hatası
        - ``requests.ConnectionError`` (örn. RemoteDisconnected)
        - ``requests.Timeout`` (ReadTimeout / ConnectTimeout)
        - ``requests.ChunkedEncodingError``
        """
        last_exc: Exception | None = None
        for attempt in range(self.max_retry):
            try:
                r = self.session.post(url, headers=headers, json=body, timeout=self.timeout)
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.ChunkedEncodingError,
            ) as exc:
                # Ağ kopması / timeout - exponential backoff ile yeniden dene
                last_exc = exc
                time.sleep(min(2 ** attempt, 30))
                continue

            remaining = r.headers.get("ratelimit-remaining")
            reset = r.headers.get("ratelimit-reset")

            # Rate limit hit
            if r.status_code == 429:
                wait = int(reset) + 1 if (reset and reset.isdigit()) else 30
                time.sleep(wait)
                continue

            # Boş response (rate-limit bypass denemeleri sonrası bazen olur)
            if r.status_code == 200 and not r.text.strip():
                wait = int(reset) + 1 if (reset and reset.isdigit()) else 15
                time.sleep(wait)
                continue

            r.raise_for_status()
            try:
                data = r.json()
            except ValueError:
                wait = int(reset) + 1 if (reset and reset.isdigit()) else 15
                time.sleep(wait)
                continue

            # Kalan kota azsa bir sonraki çağrı için koruma
            if (
                remaining is not None and remaining.isdigit() and int(remaining) <= 1
                and reset and reset.isdigit()
            ):
                time.sleep(int(reset) + 1)

            return data

        msg = f"{self.max_retry} denemeden sonra başarısız ({url})"
        if last_exc is not None:
            msg += f" - son hata: {type(last_exc).__name__}: {last_exc}"
        raise RuntimeError(msg)
