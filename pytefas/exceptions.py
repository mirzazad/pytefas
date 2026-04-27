"""pytefas exception hierarchy.

Tüm pytefas hataları `TefasError`'dan türer. Kullanıcılar genel hatalar
için `TefasError` yakalayabilir, spesifik durumlar için alt sınıfları:

>>> from pytefas import Crawler
>>> from pytefas.exceptions import TefasInvalidParameterError, TefasRateLimitError
>>>
>>> tefas = Crawler()
>>> try:
...     df = tefas.fetch("2026-04-24", kind="INVALID")
... except TefasInvalidParameterError as e:
...     print(f"Parametre hatası: {e}")
... except TefasRateLimitError as e:
...     print(f"Rate limit aşıldı: {e}")
"""
from __future__ import annotations


class TefasError(Exception):
    """pytefas hatalarının baz sınıfı.

    Tüm pytefas-spesifik hatalar bu sınıftan türer. Kütüphanenin attığı
    her hatayı yakalamak için bunu kullanın.
    """


class TefasAPIError(TefasError):
    """TEFAS API'si bir hata yanıtı döndürdüğünde fırlatılır.

    Örnek: API `errorCode != null` döner veya HTTP 4xx/5xx döner.
    """


class TefasRateLimitError(TefasAPIError):
    """Rate limit aşıldı ve maksimum yeniden deneme sayısı bitti.

    TEFAS API'si dakikada 6 istek sınırına sahiptir. `Crawler` otomatik
    olarak bekleyip tekrar dener; tüm denemeler tükenince bu hata fırlar.
    """


class TefasInvalidParameterError(TefasError, ValueError):
    """Geçersiz bir parametre verildi.

    Örnek: `kind="INVALID"`, `columns="xyz"`, geçersiz tarih formatı,
    `start > end`, vs.

    `ValueError`'dan da türer; eski kodlar `except ValueError` ile
    yakalamaya devam edebilir.
    """
