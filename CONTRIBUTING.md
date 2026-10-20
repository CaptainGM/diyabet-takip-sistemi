# Katkı Kılavuzu

Teşekkürler! Küçük ama düzenli bir proje; aşağıdaki kurallara uyan PR'lar
hızla birleştirilir.

## Geliştirme ortamı

```bash
pip install -r requirements.txt
pip install ruff                  # lint
```

MongoDB gereklidir (lokal `mongod` veya `docker compose up -d`).
`.env` örnek için `.env.example`.

## Çalıştırma ve doğrulama

```bash
python scripts/generate_demo_data.py --reset --days 90   # demo veri
python scripts/smoke_test.py                             # 32 denetim — tümü ✔ olmalı
python main.py                                           # uygulama
```

UI'ya dokunuyorsanız `python scripts/capture_screens.py` ile ekran
görüntülerini yenileyip ekleyin.

## Kod stili

- `ruff check diyabet_takip scripts main.py` — sıfır uyarı hedefi
  (ayrıntılar `pyproject.toml` içinde)
- Type hintler `from __future__ import annotations` ile; IO/tkinter
  fonksiyonlarında esnek
- Türkçe UI metinleri, Türkçe docstring (kod tanımlayıcıları Türkçe isimli
  alanlarla eşleşir: `kan_sekeri_degeri`, `gecerli_olcum` ...)
- Repo katmanı (`db/`) dict döndürür; UI legacy anahtar adlarını korur.
  Servis katmanı (`services/`) iş kararlarını içerir; `db/` sorgu,
  `services/` kural

## Commit mesajı

- Küçük ve konu başına tek: `feat(ui): hasta randevularim ekrani`,
  `fix(db): insulin unique upsert` gibi
- `feat|fix|docs|chore|refactor(scope)` ön eki tercih edilir

## Test

Ekran testi elle (demo veriyle), mantık testleri `scripts/smoke_test.py`.
Yeni servis kuralı eklediyseniz smoke test'e bir denetim ekleyin.
