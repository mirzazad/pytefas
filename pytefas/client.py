"""TEFAS yeni API'si için Crawler sınıfı."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

from ._ratelimit import RateLimitedClient
from .schema import DIST_FIELDS, INFO_FIELDS, FUND_KINDS

INFO_URL = "https://www.tefas.gov.tr/api/funds/fonGnlBlgSiraliGetir"
DIST_URL = "https://www.tefas.gov.tr/api/funds/dagilimSiraliGetirT"

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://www.tefas.gov.tr",
    "Referer": "https://www.tefas.gov.tr/tr/fon-verileri",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    ),
}


def _to_yyyymmdd(d) -> str:
    if isinstance(d, str):
        # Hem 'YYYY-MM-DD' hem 'YYYYMMDD' destekle
        if len(d) == 8 and d.isdigit():
            return d
        return pd.to_datetime(d).strftime("%Y%m%d")
    if isinstance(d, datetime):
        return d.strftime("%Y%m%d")
    if isinstance(d, pd.Timestamp):
        return d.strftime("%Y%m%d")
    raise ValueError(f"Tarih formatı anlaşılmadı: {d!r}")


class Crawler:
    """TEFAS resmi API'si için Python istemcisi.

    Yeni TEFAS sitesinin (https://www.tefas.gov.tr/tr/fon-verileri) doğrudan
    API endpoint'lerini kullanır. Authorization gerektirmez.

    Örnek
    -----
    >>> from pytefas import Crawler
    >>> tefas = Crawler()
    >>> df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
    >>> df.head()
    """

    def __init__(self, timeout: int = 60, max_retry: int = 5):
        self._client = RateLimitedClient(timeout=timeout, max_retry=max_retry)

    def fetch(
        self,
        start: str,
        end: Optional[str] = None,
        kind: str = "YAT",
        columns: str = "info",
    ) -> pd.DataFrame:
        """Belirli bir tarih (veya tarih aralığı) için TEFAS verisini çeker.

        Parameters
        ----------
        start : str | datetime
            Başlangıç tarihi ('YYYY-MM-DD' veya datetime).
        end : str | datetime | None
            Bitiş tarihi (varsayılan: start ile aynı).
        kind : {"YAT", "EMK", "BYF"}
            Fon tipi: Yatırım / Emeklilik / Borsa Yatırım Fonu.
        columns : {"info", "breakdown"}
            "info"      = fiyat, pay sayısı, yatırımcı sayısı, portföy büyüklüğü
            "breakdown" = portföy varlık dağılımı (yüzdeler)

        Returns
        -------
        pandas.DataFrame
            Her satır bir fonu temsil eder. Tarih + Fon Kodu + alanlar.
            Veri yoksa (tatil/hafta sonu) boş DataFrame döner.
        """
        if kind not in FUND_KINDS:
            raise ValueError(f"kind must be one of {FUND_KINDS}, got {kind!r}")
        if columns not in ("info", "breakdown"):
            raise ValueError("columns must be 'info' or 'breakdown'")

        bas = _to_yyyymmdd(start)
        bit = _to_yyyymmdd(end if end is not None else start)

        body = {
            "fonTipi": kind,
            "fonKodu": None,
            "aramaMetni": None,
            "fonTurKod": None,
            "fonGrubu": None,
            "sfonTurKod": None,
            "fonTurAciklama": None,
            "kurucuKod": None,
            "basTarih": bas,
            "bitTarih": bit,
            "basSira": 1,
            "bitSira": 5000,
            "dil": "TR",
            "sFonTurKod": "",
            "fonKod": "",
            "fonGrup": "",
            "fonUnvanTip": "",
        }

        url = INFO_URL if columns == "info" else DIST_URL
        field_map = INFO_FIELDS if columns == "info" else DIST_FIELDS
        data = self._client.post_json(url, body, DEFAULT_HEADERS)

        if data.get("errorCode"):
            raise RuntimeError(f"TEFAS API error: {data.get('errorMessage')}")

        rows = data.get("resultList") or []
        if not rows:
            return pd.DataFrame()

        records = []
        for row in rows:
            rec = {"kind": kind}
            for short, target in field_map.items():
                v = row.get(short)
                # Yüzde sütunları için None -> 0.0 (boş = sıfır mantıklı)
                if v is None and target.endswith("_pct"):
                    v = 0.0
                rec[target] = v
            records.append(rec)

        df = pd.DataFrame(records)
        # Önemli sütunları başa al
        priority = [c for c in ("date", "kind", "fund_code", "fund_name") if c in df.columns]
        rest = [c for c in df.columns if c not in priority]
        df = df[priority + rest]
        df = df.sort_values([c for c in ("date", "fund_code") if c in df.columns]).reset_index(drop=True)
        return df

    def fetch_many(
        self,
        start: str,
        end: Optional[str] = None,
        kinds: Iterable[str] = FUND_KINDS,
        columns: str = "info",
    ) -> pd.DataFrame:
        """Birden fazla fon tipini tek seferde çeker, tek DataFrame döndürür.

        Parameters
        ----------
        start, end, columns : `fetch` ile aynı.
        kinds : iterable of {"YAT", "EMK", "BYF"}
            Hangi fon tiplerinin çekileceği. Varsayılan: hepsi.
        """
        frames = []
        for k in kinds:
            df = self.fetch(start=start, end=end, kind=k, columns=columns)
            if not df.empty:
                frames.append(df)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
