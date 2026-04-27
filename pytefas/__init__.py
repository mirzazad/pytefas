"""pytefas — TEFAS yeni resmi API'si için modern Python istemcisi.

Hızlı başlangıç:
    >>> from pytefas import Crawler
    >>> tefas = Crawler()
    >>> df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
"""
from .client import Crawler

__version__ = "0.1.0"
__all__ = ["Crawler"]
