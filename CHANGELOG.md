<!-- markdownlint-disable MD024 -->

# Changelog

Bu projedeki dikkate değer tüm değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standardına dayanır,
ve bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanır.

## [Unreleased]

## [0.1.1] - 2026-04-27

### Added

- Custom exception hierarchy: `TefasError`, `TefasAPIError`, `TefasRateLimitError`, `TefasInvalidParameterError`.
- Tüm public API'lere type hints (`Literal["YAT", "EMK", "BYF"]`, `DateLike` alias).
- NumPy stilinde detaylı docstring'ler (`Parameters`, `Returns`, `Raises`, `Examples`).
- Tarih için `date`, `datetime`, `pd.Timestamp` desteği (sadece string yerine).
- `start > end` validation.

### Changed

- Geçersiz parametre artık `ValueError` yerine `TefasInvalidParameterError` fırlatır.
  Geriye uyumluluk korunmuştur (`TefasInvalidParameterError`, `ValueError`'dan da türer).
- API hataları artık generic `RuntimeError` yerine `TefasAPIError`/`TefasRateLimitError` fırlatır.

## [0.1.0] - 2026-04-27

### Added

- İlk public release.
- `Crawler.fetch(start, end, kind, columns)` - tek tarih veya tarih aralığı için fon verisi çekimi.
- `Crawler.fetch_many(start, end, kinds, columns)` - birden fazla fon tipini (YAT/EMK/BYF) tek DataFrame'de birleştirme.
- İki veri görünümü:
  - `columns="info"` → fiyat, pay sayısı, yatırımcı sayısı, portföy büyüklüğü.
  - `columns="breakdown"` → 50+ varlık sınıfı yüzdesi.
- Otomatik rate-limit yönetimi (TEFAS dakikada 6 istek sınırına sahiptir).
- 6 birim test + 2 canary test (TEFAS API'sini periyodik olarak doğrular).
- GitHub Actions üzerinde haftalık canary workflow.

### TEFAS API endpoints

- `https://www.tefas.gov.tr/api/funds/fonGnlBlgSiraliGetir` - fon genel bilgileri.
- `https://www.tefas.gov.tr/api/funds/dagilimSiraliGetirT` - portföy dağılımı.

[Unreleased]: https://github.com/mirzazad/pytefas/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/mirzazad/pytefas/releases/tag/v0.1.1
[0.1.0]: https://github.com/mirzazad/pytefas/releases/tag/v0.1.0
