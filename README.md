# pytefas

[![PyPI version](https://img.shields.io/pypi/v/pytefas.svg)](https://pypi.org/project/pytefas/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytefas.svg)](https://pypi.org/project/pytefas/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![tests](https://github.com/mirzazad/pytefas/actions/workflows/test.yml/badge.svg)](https://github.com/mirzazad/pytefas/actions/workflows/test.yml)
[![canary](https://github.com/mirzazad/pytefas/actions/workflows/canary.yml/badge.svg)](https://github.com/mirzazad/pytefas/actions/workflows/canary.yml)

[TEFAS (Türkiye Elektronik Fon Alım Satım Platformu)](https://www.tefas.gov.tr/) için modern Python istemcisi.

Yeni TEFAS sitesinin (Next.js tabanlı, 2026'da yenilendi) doğrudan resmi API endpoint'lerini kullanır. Authorization, login veya API anahtarı gerektirmez.

## Neden pytefas?

TEFAS sitesi 2026'da Next.js tabanlı yeni bir altyapıya geçti. Eski HTML scraping tabanlı çözümler bu yenilemeden etkilendi. pytefas, yeni sitenin doğrudan JSON API endpoint'lerini kullanır:

- HTML parse yerine yapısal JSON
- Daha hızlı, daha az kırılgan
- 50+ varlık dağılımı kolonu (eski araçlardaki kısıtlama yok)
- Tek istekte 1 ay sınırını arka planda otomatik çözer

## Özellikler

- Yeni resmi TEFAS API endpoint'lerini doğrudan kullanır (HTML scraping yok).
- **Otomatik chunking** - uzun tarih aralıklarını arka planda parçalara böler.
- **Otomatik rate-limit yönetimi** (TEFAS dakikada 6 istek sınırına sahiptir).
- 50+ varlık dağılımı kolonu (hisse, repo, eurobond, kıymetli madenler vs.).
- YAT / EMK / BYF fon tipleri tek DataFrame'de birleştirilebilir.
- Custom exception'lar - hata yönetimi tipli ve kontrollü.
- Tam type hints + NumPy stilinde docstring'ler.

## API endpoints

- `https://www.tefas.gov.tr/api/funds/fonGnlBlgSiraliGetir` - fund info (price / shares / size)
- `https://www.tefas.gov.tr/api/funds/dagilimSiraliGetirT` - portfolio breakdown

## Kurulum

```bash
pip install pytefas
```

## Hızlı başlangıç

```python
from pytefas import Crawler

tefas = Crawler()
df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
print(df.head())
```

```text
        date kind fund_code                              fund_name      price  shares_outstanding  investor_count  portfolio_size
0 2026-04-24  YAT       AAK  ATA PORTFÖY ÇOKLU VARLIK DEĞİŞKEN FON   35.46418            999934.0           769.0    35461839.75
1 2026-04-24  YAT       AAL    ATA PORTFÖY PARA PİYASASI (TL) FONU   ...
```

## Kullanım

### Tek bir gün, fiyat bilgisi

```python
df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
```

9 sütun döner: `date, kind, fund_code, fund_name, price, shares_outstanding, investor_count, portfolio_size, exchange_bulletin_price`.

`exchange_bulletin_price` (borsa bülten fiyatı) genellikle BYF için doludur; YAT/EMK için `None` olabilir.

### Portföy varlık dağılımı

```python
df = tefas.fetch("2026-04-24", columns="breakdown", kind="YAT")
# 50+ sütun: stock_pct, government_bond_pct, repo_pct, foreign_stock_pct, ...
```

Her satırın yüzde toplamı ~100 olur.

### Tarih aralığı (otomatik chunking)

TEFAS API'si tek istekte 1 ay (yaklaşık 30 gün) sınırı uygular. pytefas bu sınırı arka planda yönetir - uzun aralıklar otomatik olarak 28 günlük parçalara bölünür ve birleştirilir.

```python
# 1 ay
df = tefas.fetch("2026-03-24", "2026-04-24", kind="YAT")

# 1 yıl - otomatik chunklanır (~13 chunk, rate-limit ile ~3 dakika)
df = tefas.fetch("2025-04-01", "2026-04-01", kind="YAT")
print(df["date"].nunique())  # ~250 iş günü
```

### Tüm fon tiplerini birlikte (YAT + EMK + BYF)

```python
df = tefas.fetch_many("2026-04-24", columns="info")
print(df.groupby("kind").size())
# kind
# BYF      30
# EMK     392
# YAT    2001
```

### Hata yönetimi

```python
from pytefas import (
    Crawler,
    TefasInvalidParameterError,
    TefasAPIError,
    TefasRateLimitError,
)

tefas = Crawler()

try:
    df = tefas.fetch("2026-04-24", kind="INVALID")
except TefasInvalidParameterError as e:
    print(f"Geçersiz parametre: {e}")
except TefasRateLimitError as e:
    print(f"Rate limit aşıldı: {e}")
except TefasAPIError as e:
    print(f"API hatası: {e}")
```

`TefasInvalidParameterError` aynı zamanda `ValueError`'dan da türer - eski kodlar `except ValueError` ile yakalamaya devam edebilir.

## Parametreler

### `Crawler(timeout=60, max_retry=5)`

| Parametre | Açıklama |
|-----------|----------|
| `timeout` | HTTP istekleri için saniye cinsinden zaman aşımı. |
| `max_retry` | Rate-limit veya geçici hatalarda maksimum yeniden deneme sayısı. |

### `Crawler.fetch(start, end=None, kind="YAT", columns="info")`

| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| `start` | `str`, `date`, `datetime`, `pd.Timestamp` | Başlangıç tarihi. |
| `end` | aynı, veya `None` | Bitiş tarihi. `None` = `start` ile aynı. |
| `kind` | `"YAT"`, `"EMK"`, `"BYF"` | Fon tipi (Yatırım / Emeklilik / BYF). |
| `columns` | `"info"` veya `"breakdown"` | Genel bilgi mi portföy dağılımı mı. |

### `Crawler.fetch_many(start, end=None, kinds=("YAT","EMK","BYF"), columns="info")`

`fetch` ile aynı, ama birden fazla `kind`'ı tek DataFrame'de birleştirir.

## Tarihsel veri ve süre tahmini

TEFAS rate-limit'i nedeniyle uzun aralıklar zaman alır:

| Aralık | Tahmini süre |
|--------|--------------|
| 1 hafta | ~10 saniye |
| 1 ay | ~10 saniye (1 chunk) |
| 3 ay | ~1 dakika |
| 1 yıl | ~3 dakika |
| 5 yıl | ~15 dakika |

## Stabilite

TEFAS API'si halen genel kullanıma açıktır ancak resmi olarak dokümante edilmemiştir. TEFAS site değişikliği yaparsa paket güncellenmesi gerekebilir - issue açın veya PR gönderin.

Periyodik canary testi her hafta TEFAS API'sinin çalıştığını doğrular ([Actions tab](https://github.com/mirzazad/pytefas/actions)).

## Değişiklik geçmişi

Versiyonlar arası değişiklikler için [CHANGELOG.md](CHANGELOG.md).

## Lisans

MIT - bkz. [LICENSE](LICENSE).

## Katkı

Pull request'ler memnuniyetle karşılanır. Major değişiklikler için önce issue açıp tartışalım. Detay için [CONTRIBUTING.md](CONTRIBUTING.md).

## Teşekkürler

TEFAS Python ekosistemine yıllardır katkı sağlayan açık kaynak geliştiricilere teşekkürler. Bu paket, topluluğun kollektif çabasının bir devamıdır.
