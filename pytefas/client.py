"""TEFAS yeni API'si için Crawler sınıfı."""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Literal, Optional, Union

import pandas as pd

from ._ratelimit import RateLimitedClient
from .exceptions import (
    TefasAPIError,
    TefasInvalidParameterError,
    TefasRateLimitError,
)
from .schema import DIST_FIELDS, FUND_KINDS, INFO_FIELDS

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

DateLike = Union[str, date, datetime, pd.Timestamp]
Kind = Literal["YAT", "EMK", "BYF"]
Columns = Literal["info", "breakdown"]


def _to_yyyymmdd(d: DateLike) -> str:
    """Tarihi 'YYYYMMDD' formatına çevirir.

    Parameters
    ----------
    d : str, date, datetime veya pd.Timestamp
        Çevrilecek tarih. String için 'YYYY-MM-DD' veya 'YYYYMMDD' kabul edilir.

    Raises
    ------
    TefasInvalidParameterError
        Tarih formatı tanınmazsa.
    """
    if isinstance(d, str):
        if len(d) == 8 and d.isdigit():
            return d
        try:
            return pd.to_datetime(d).strftime("%Y%m%d")
        except (ValueError, TypeError) as e:
            raise TefasInvalidParameterError(f"Tarih formatı anlaşılmadı: {d!r}") from e
    if isinstance(d, (datetime, pd.Timestamp)):
        return d.strftime("%Y%m%d")
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    raise TefasInvalidParameterError(f"Tarih formatı anlaşılmadı: {d!r}")


class Crawler:
    """TEFAS resmi API'si için Python istemcisi.

    Yeni TEFAS sitesinin (https://www.tefas.gov.tr/tr/fon-verileri) doğrudan
    API endpoint'lerini kullanır. Authorization gerektirmez.

    Parameters
    ----------
    timeout : int, default 60
        HTTP istekleri için saniye cinsinden zaman aşımı.
    max_retry : int, default 5
        Rate-limit veya geçici hatalarda maksimum yeniden deneme sayısı.

    Examples
    --------
    >>> from pytefas import Crawler
    >>> tefas = Crawler()
    >>> df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
    >>> df.head()
    """

    def __init__(self, timeout: int = 60, max_retry: int = 5) -> None:
        self._client = RateLimitedClient(timeout=timeout, max_retry=max_retry)

    def fetch(
        self,
        start: DateLike,
        end: Optional[DateLike] = None,
        kind: Kind = "YAT",
        columns: Columns = "info",
    ) -> pd.DataFrame:
        """Belirli bir tarih (veya tarih aralığı) için TEFAS verisini çeker.

        Parameters
        ----------
        start : str, date, datetime veya pd.Timestamp
            Başlangıç tarihi. String için 'YYYY-MM-DD' formatı önerilir.
        end : str, date, datetime, pd.Timestamp veya None, default None
            Bitiş tarihi. None ise sadece `start` günü çekilir.
        kind : {"YAT", "EMK", "BYF"}, default "YAT"
            Fon tipi:

            - ``"YAT"`` - Yatırım Fonları
            - ``"EMK"`` - Emeklilik Fonları
            - ``"BYF"`` - Borsa Yatırım Fonları

        columns : {"info", "breakdown"}, default "info"
            Hangi veri görünümü:

            - ``"info"`` - fiyat, pay sayısı, yatırımcı sayısı, portföy büyüklüğü
            - ``"breakdown"`` - portföy varlık dağılımı (50+ yüzde sütunu)

        Returns
        -------
        pandas.DataFrame
            Her satır bir fonu temsil eder. Sütunlar `columns` parametresine
            bağlıdır. Veri yoksa (tatil/hafta sonu) boş DataFrame döner.

        Raises
        ------
        TefasInvalidParameterError
            `kind` veya `columns` geçersiz; tarih formatı tanınmıyor.
        TefasAPIError
            TEFAS API'si hata yanıtı döndürdü.
        TefasRateLimitError
            Rate-limit aşıldı ve `max_retry` denemeleri tükendi.

        Examples
        --------
        Tek günün fon bilgileri:

        >>> tefas = Crawler()
        >>> df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
        >>> df[["fund_code", "price", "portfolio_size"]].head()

        Tarih aralığı, varlık dağılımı:

        >>> df = tefas.fetch("2026-04-22", "2026-04-24", columns="breakdown")
        """
        if kind not in FUND_KINDS:
            raise TefasInvalidParameterError(
                f"kind must be one of {FUND_KINDS}, got {kind!r}"
            )
        if columns not in ("info", "breakdown"):
            raise TefasInvalidParameterError(
                f"columns must be 'info' or 'breakdown', got {columns!r}"
            )

        bas = _to_yyyymmdd(start)
        bit = _to_yyyymmdd(end if end is not None else start)
        if bas > bit:
            raise TefasInvalidParameterError(
                f"start ({bas}) bitTarih'ten sonra olamaz ({bit})"
            )

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

        try:
            data = self._client.post_json(url, body, DEFAULT_HEADERS)
        except RuntimeError as e:
            # _ratelimit modülü retry tükendiğinde RuntimeError fırlatır
            raise TefasRateLimitError(str(e)) from e

        if data.get("errorCode"):
            raise TefasAPIError(
                f"TEFAS API error: {data.get('errorMessage')} "
                f"(code: {data.get('errorCode')})"
            )

        rows = data.get("resultList") or []
        if not rows:
            return pd.DataFrame()

        records = []
        for row in rows:
            rec: dict = {"kind": kind}
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
        sort_cols = [c for c in ("date", "fund_code") if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)
        return df

    def fetch_many(
        self,
        start: DateLike,
        end: Optional[DateLike] = None,
        kinds: Iterable[Kind] = FUND_KINDS,
        columns: Columns = "info",
    ) -> pd.DataFrame:
        """Birden fazla fon tipini tek seferde çeker, tek DataFrame döndürür.

        Parameters
        ----------
        start : str, date, datetime veya pd.Timestamp
            Başlangıç tarihi.
        end : str, date, datetime, pd.Timestamp veya None, default None
            Bitiş tarihi. None ise sadece `start` günü çekilir.
        kinds : iterable of {"YAT", "EMK", "BYF"}, default ("YAT", "EMK", "BYF")
            Hangi fon tiplerinin çekileceği.
        columns : {"info", "breakdown"}, default "info"
            Hangi veri görünümü çekilecek.

        Returns
        -------
        pandas.DataFrame
            Tüm fon tiplerinin birleştirilmiş tablosu. `kind` sütunu hangi
            fon tipi olduğunu belirtir. Hiçbir tipten veri gelmezse boş.

        Raises
        ------
        TefasInvalidParameterError
            Geçersiz parametre.
        TefasAPIError, TefasRateLimitError
            `fetch` ile aynı.

        Examples
        --------
        >>> tefas = Crawler()
        >>> df = tefas.fetch_many("2026-04-24", columns="info")
        >>> df.groupby("kind").size()
        kind
        BYF      30
        EMK     392
        YAT    2001
        """
        frames = []
        for k in kinds:
            df = self.fetch(start=start, end=end, kind=k, columns=columns)
            if not df.empty:
                frames.append(df)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
