# Katkıda bulunma rehberi

Katkılarınız memnuniyetle karşılanır! Hata bildirimi, özellik önerisi veya pull request - her türlü geri bildirim değerli.

## Hata bildirimi / özellik önerisi

[Issues](https://github.com/mirzazad/pytefas/issues) üzerinden açabilirsiniz. Hata bildirirken lütfen ekleyin:

- Hatayı yeniden üreten **minimum kod örneği**
- Beklenen davranış vs. gerçek davranış
- `pytefas` ve Python sürümü
- TEFAS API'sinden alınan response (varsa)

## Pull Request açma

### 1. Repo'yu fork edip klonla

```bash
git clone https://github.com/<your-username>/pytefas.git
cd pytefas
```

### 2. Geliştirme ortamı kur

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. Yeni branch aç

```bash
git checkout -b feature/yeni-ozellik
# veya
git checkout -b fix/hata-aciklamasi
```

### 4. Değişikliklerini yap

- Yeni özellik için **test ekle** (`tests/` klasörü).
- Mevcut testlerin geçtiğinden emin ol.
- Public API değişikliği yapıyorsan `CHANGELOG.md`'ye not düş.

### 5. Testleri çalıştır

```bash
pytest tests/ -v
```

Network'e gerçek istek atan canary testleri için TEFAS canlı olmalı.

### 6. Commit ve push

Commit mesajları için [Conventional Commits](https://www.conventionalcommits.org/) önerilir:

- `feat: yeni özellik açıklaması`
- `fix: hatanın açıklaması`
- `docs: README güncellemesi`
- `test: yeni test eklendi`
- `chore: bakım/refactor`

```bash
git commit -m "feat: add support for fund history endpoint"
git push origin feature/yeni-ozellik
```

### 7. Pull Request aç

GitHub üzerinden PR aç. Açıklamada:

- Ne değiştirdiğini ve **neden**
- Bağlı issue varsa link'le (`Closes #12` gibi)
- Test edildi mi?

## Kod stili

- Python 3.9+ uyumlu kod yazın.
- Public API'lere type hint ekleyin.
- Public method'lara docstring ekleyin (NumPy stili tercih edilir).
- Mevcut kodun stiline uyun (line length ~100, snake_case).

## Soru?

Karar veremediğin bir şey varsa **önce issue açıp tartışalım**, sonra kod yaz. Büyük değişikliklerde bu yaklaşım hem senin hem benim zamanımı korur.
