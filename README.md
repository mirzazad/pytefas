# pytefas

[![PyPI version](https://img.shields.io/pypi/v/pytefas.svg)](https://pypi.org/project/pytefas/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytefas.svg)](https://pypi.org/project/pytefas/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/pytefas.svg)](https://pypi.org/project/pytefas/)
[![canary](https://github.com/mirzazad/pytefas/actions/workflows/canary.yml/badge.svg)](https://github.com/mirzazad/pytefas/actions/workflows/canary.yml)


[TEFAS (Türkiye Elektronik Fon Alım Satım Platformu)](https://www.tefas.gov.tr/) için modern Python istemcisi.

Yeni TEFAS sitesinin (Next.js tabanlı, 2026'da yenilendi) doğrudan resmi API endpoint'lerini kullanır. Authorization, login veya API anahtarı gerektirmez.

## API endpoints

- `https://www.tefas.gov.tr/api/funds/fonGnlBlgSiraliGetir` — fund info (price / shares / size)
- `https://www.tefas.gov.tr/api/funds/dagilimSiraliGetirT` — portfolio breakdown

## Kurulum

```bash
pip install pytefas
```

## Kullanım

### Tek bir gün, fiyat bilgisi

```python
from pytefas import Crawler

tefas = Crawler()
df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
print(df.head())
```

```
        date kind fund_code                              fund_name      price  shares_outstanding  investor_count  portfolio_size
0 2026-04-24  YAT       AAK  ATA PORTFÖY ÇOKLU VARLIK DEĞİŞKEN FON   35.46418            999934.0           769.0    35461839.75
1 2026-04-24  YAT       AAL    ATA PORTFÖY PARA PİYASASI (TL) FONU   ...
```

### Portföy varlık dağılımı

```python
df = tefas.fetch("2026-04-24", columns="breakdown", kind="YAT")
# Sütunlar: stock_pct, government_bond_pct, repo_pct, foreign_stock_pct, ...
```

### Tarih aralığı

```python
df = tefas.fetch(start="2026-04-22", end="2026-04-24", columns="info", kind="YAT")
```

### Tüm fon tiplerini birlikte (YAT + EMK + BYF)

```python
df = tefas.fetch_many("2026-04-24", columns="info")
# 'kind' sütunu YAT/EMK/BYF değerlerini içerir
```

## Parametreler

### `Crawler.fetch(start, end=None, kind="YAT", columns="info")`

| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| `start` | `str` veya `datetime` | Başlangıç tarihi (`'YYYY-MM-DD'` formatı). |
| `end` | `str` veya `datetime` veya `None` | Bitiş tarihi. `None` = `start` ile aynı. |
| `kind` | `"YAT"`, `"EMK"`, `"BYF"` | Fon tipi: Yatırım / Emeklilik / Borsa Yatırım Fonu. |
| `columns` | `"info"` veya `"breakdown"` | Genel bilgi vs. portföy dağılımı. |

### Dönen DataFrame

- **`columns="info"`** → 8 sütun: `date, kind, fund_code, fund_name, price, shares_outstanding, investor_count, portfolio_size, exchange_bulletin_price`
- **`columns="breakdown"`** → 50+ sütun: tüm varlık sınıflarının yüzdeleri (ör. `stock_pct`, `repo_pct`, `foreign_stock_pct`, `precious_metals_pct`, vs.)

Tatil/hafta sonu için boş DataFrame döner.

## Rate limiting

TEFAS API'si dakikada 6 istek sınırına sahiptir. Paket bunu **otomatik** handle eder — limit aşılırsa bekler ve yeniden dener. Manuel bir şey yapmanıza gerek yok.

## Stabilite

TEFAS API'si halen genel kullanıma açıktır ancak resmi olarak dokümante edilmemiştir. TEFAS site değişikliği yaparsa paket güncellenmesi gerekebilir — issue açın veya PR gönderin.

## Lisans

MIT — bkz. [LICENSE](LICENSE).

## Katkı

Pull request'ler memnuniyetle karşılanır. Major değişiklikler için önce issue açıp tartışalım.
