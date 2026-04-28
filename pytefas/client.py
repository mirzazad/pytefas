"""TEFAS yeni API'si için Crawler sınıfı."""
from __future__ import annotations

from datetime import date, datetime, timedelta
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

# TEFAS API'si tek istekte 1 ay (~30 gün) sınırı uygular. 28 gün koruyucu eşik.
MAX_DAYS_PER_REQUEST = 28

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


def _parse_date(d: DateLike) -> datetime:
    """Verilen tarih girdisini `datetime`'a normalize eder.

    Parameters
    ----------
    d : str, date, datetime veya pd.Timestamp
        Çevrilecek tarih. String için 'YYYY-MM-DD' veya 'YYYYMMDD' kabul edilir.

    Returns
    -------
    datetime
        Normalize edilmiş tarih (saat 00:00:00).

    Raises
    ------
    TefasInvalidParameterError
        Tarih formatı tanınmazsa.
    """
    if isinstance(d, datetime):
        return d
    if isinstance(d, pd.Timestamp):
        return d.to_pydatetime()
    if isinstance(d, date):
        return datetime(d.year, d.month, d.day)
    if isinstance(d, str):
        try:
            return pd.to_datetime(d).to_pydatetime()
        except (ValueError, TypeError) as e:
            raise TefasInvalidParameterError(f"Tarih formatı anlaşılmadı: {d!r}") from e
    raise TefasInvalidParameterError(f"Tarih formatı anlaşılmadı: {d!r}")


def _split_range(
    start: datetime, end: datetime, max_days: int
) -> list[tuple[datetime, datetime]]:
    """[start, end] aralığını en fazla `max_days` günlük parçalara böler.

    Sınırlar dahildir; ardışık parçalar 1 gün boşluksuz birbirini takip eder.
    """
    chunks: list[tuple[datetime, datetime]] = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=max_days - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


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
        fund_code: Optional[str] = None,
    ) -> pd.DataFrame:
        """Belirli bir tarih (veya tarih aralığı) için TEFAS verisini çeker.

        TEFAS API'si tek istekte en fazla 1 ay (yaklaşık 30 gün) veri döndürür.
        Daha uzun aralıklar otomatik olarak ``MAX_DAYS_PER_REQUEST`` (28 gün)
        boyutunda parçalara bölünüp ardışık çağrılarla çekilir, tek bir
        DataFrame'de birleştirilir. Rate-limit otomatik yönetilir.

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

        fund_code : str veya None, default None
            Belirli bir fon kodu (örn. ``"AAK"``). Verilirse sadece o fon
            döndürülür - 1 yıllık geçmişi tek fon için çekmek bu sayede çok
            daha hızlıdır. None ise verilen ``kind`` tipindeki tüm fonlar
            döndürülür.

        Returns
        -------
        pandas.DataFrame
            Her satır bir (fon, tarih) çiftini temsil eder. Sütunlar `columns`
            parametresine bağlıdır. Veri yoksa (tatil/hafta sonu) boş DataFrame
            döner.

        Raises
        ------
        TefasInvalidParameterError
            `kind` veya `columns` geçersiz; tarih formatı tanınmıyor; start > end.
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

        Uzun aralık (otomatik chunklanır):

        >>> df = tefas.fetch("2025-01-01", "2026-04-01", kind="YAT")
        >>> df["date"].nunique()  # ~250 iş günü

        Tek fonun 1 yıllık fiyat geçmişi:

        >>> df = tefas.fetch("2025-04-28", "2026-04-28", fund_code="AAK")
        >>> df[["date", "price"]].set_index("date")
        """
        if kind not in FUND_KINDS:
            raise TefasInvalidParameterError(
                f"kind must be one of {FUND_KINDS}, got {kind!r}"
            )
        if columns not in ("info", "breakdown"):
            raise TefasInvalidParameterError(
                f"columns must be 'info' or 'breakdown', got {columns!r}"
            )

        # Normalize tarihler
        start_dt = _parse_date(start)
        end_dt = _parse_date(end) if end is not None else start_dt
        if start_dt > end_dt:
            raise TefasInvalidParameterError(
                f"start ({start_dt.date()}) end'den sonra olamaz ({end_dt.date()})"
            )

        # fund_code normalize
        fcode = fund_code.strip().upper() if fund_code else None

        # Chunk'lara böl
        chunks = _split_range(start_dt, end_dt, MAX_DAYS_PER_REQUEST)

        frames = []
        for chunk_start, chunk_end in chunks:
            df = self._fetch_single(chunk_start, chunk_end, kind, columns, fcode)
            if not df.empty:
                frames.append(df)

        if not frames:
            return pd.DataFrame()

        out = pd.concat(frames, ignore_index=True)
        # Aynı (date, fund_code) tekrar gelirse en sonuncu geçerli
        if "date" in out.columns and "fund_code" in out.columns:
            out = out.drop_duplicates(subset=["date", "fund_code"], keep="last")
            out = out.sort_values(["date", "fund_code"]).reset_index(drop=True)
        return out

    def _fetch_single(
        self,
        start_dt: datetime,
        end_dt: datetime,
        kind: Kind,
        columns: Columns,
        fund_code: Optional[str] = None,
    ) -> pd.DataFrame:
        """Tek bir API çağrısı (en fazla MAX_DAYS_PER_REQUEST gün)."""
        body = {
            "fonTipi": kind,
            "fonKodu": fund_code,
            "aramaMetni": None,
            "fonTurKod": None,
            "fonGrubu": None,
            "sfonTurKod": None,
            "fonTurAciklama": None,
            "kurucuKod": None,
            "basTarih": start_dt.strftime("%Y%m%d"),
            "bitTarih": end_dt.strftime("%Y%m%d"),
            "basSira": 1,
            "bitSira": 100000,
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

        # API hem errorCode hem errorMessage gönderebilir; ikisini de kontrol et.
        # Tatil/hafta sonu için TEFAS bazen "Index 0 out of bounds for length 0"
        # gibi mesajlar dönebilir - bunu boş veri olarak yorumla.
        err_code = data.get("errorCode")
        err_msg = data.get("errorMessage")
        empty_messages = ("out of bounds", "veri bulunamadı")
        is_empty_marker = err_msg and any(m in err_msg.lower() for m in empty_messages)
        if (err_code or err_msg) and not is_empty_marker:
            raise TefasAPIError(
                f"TEFAS API error: {err_msg}"
                + (f" (code: {err_code})" if err_code else "")
            )
        if is_empty_marker:
            return pd.DataFrame()

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
        fund_code: Optional[str] = None,
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
        fund_code : str veya None, default None
            Belirli bir fon kodu. Verilirse her ``kind`` için sadece o kodu
            sorgular. Hangi tipte olduğunu bilmediğinde kullanışlı:

            >>> df = tefas.fetch_many("2026-04-24", fund_code="AAK")

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
            df = self.fetch(
                start=start, end=end, kind=k, columns=columns, fund_code=fund_code
            )
            if not df.empty:
                frames.append(df)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
