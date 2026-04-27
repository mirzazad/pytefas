"""pytefas - TEFAS yeni resmi API'si için modern Python istemcisi.

Hızlı başlangıç:
    >>> from pytefas import Crawler
    >>> tefas = Crawler()
    >>> df = tefas.fetch("2026-04-24", columns="info", kind="YAT")

Hata yönetimi:
    >>> from pytefas import Crawler, TefasInvalidParameterError, TefasRateLimitError
    >>> try:
    ...     df = tefas.fetch("2026-04-24", kind="INVALID")
    ... except TefasInvalidParameterError as e:
    ...     print(f"Geçersiz parametre: {e}")
"""
from .client import Crawler
from .exceptions import (
    TefasAPIError,
    TefasError,
    TefasInvalidParameterError,
    TefasRateLimitError,
)

__version__ = "0.2.1"
__all__ = [
    "Crawler",
    "TefasError",
    "TefasAPIError",
    "TefasRateLimitError",
    "TefasInvalidParameterError",
]
