# Changelog

## [2.0.0] — 2026-10-21

v1 (2021, tek dosyalık MySQL üniversite ödevi → `docs/legacy/`)'in tamamına
yönelik modernizasyon sürümü.

### Eklenen

- **Paket mimarisi:** `diyabet_takip/` altında `config`, `state`, `security`,
  `db/` (client, bootstrap, records, doctors, patients, reference), `services/`
  (alert, insulin, compliance, stats, recommendation, report, auth,
  measurement), `ui/` (login, menü, doktor/hasta ekranları, profil, grafik)
  katmanları
- **Doktor paneli:** toplam hasta, bugün ölçüm yapan hasta sayısı, okunmamış
  uyarı, bugünün uyarısı ve ortalama uyum skoru tek ekranda
- **Randevu yönetimi (yeni özellik):** v1'de yalnızca tablodan ibaret olan
  randevu sisteminde doktor randevu oluşturur/iptal eder, hasta listeler
- **Profil / şifre değiştirme (yeni özellik):** iki rol için hesap bilgisi ve
  PBKDF2 güvencesiyle şifre güncelleme
- **Günlük görev CLI'sı:** v1 MySQL EVENT'lerinin karşılığı
  (`python -m diyabet_takip.jobs [--all-patients]`)
- **Geliştirici araçları:** `scripts/smoke_test.py` (32 uçtan uca denetim),
  `scripts/generate_demo_data.py` (90 günlük zengin demo veri),
  `scripts/capture_screens.py` (README görüntüleyici)
- **CI:** Ruff lint + MongoDB servis konteynerine karşı smoke test
- Docker compose (yalnız MongoDB), `.env.example`, data-model dokümantasyonu

### Değişen

- **MySQL → MongoDB:** 27 tablo 22 koleksiyona; trigger/prosedür/event rolünü
  servis katmanı, view rolünü aggregation fonksiyonları üstlendi
  (`docs/data-model.md`)
- **Şifre saklama:** PBKDF2-HMAC-SHA256 (tuz + 390k tur). Eski düz metin
  şifreler ilk başarılı girişte şeffafça hash'e yükselir
- **Ekranlar:** tile-grid ana menü, kart bileşenleri, tek renk paleti
  (Segoe UI), ttk.Treeview tablolar, matplotlib grafik kartları
- **Ölçüm geçerliliği:** saat aralıkları `services.measurement_service`
  içinde merkezi; geçerli/saat-dışı ayrımı hem tablo hem ortalama
  hesaplarında kullanılır

### Düzeltilen (v1'den gelen)

- **Geçerli ölçüm bayrağı hep `True` yazılıyordu:** v1'de `gecerli_olcum`
  kolonuna saat kontrolüne rağmen her kayıt geçerli yazılıyor, saat dışı
  ölçümler ortalama ve uyarı hesaplarına dahil oluyordu; artık kayıt anında
  hesaplanıp saklanıyor ve tüm hesaplar bu alanı filtreliyor
- **Düz metin şifreler:** v1'den taşınan kayıtlar ilk girişte PBKDF2'ye
  yükseltilecek şekilde göç yolu eklendi
- **Randevu akışı yoktu:** v1'de `randevu_sistemi` tablosu varken hiçbir
  ekran/akış kullanmıyordu; v2'de yapılma + iptal + listeleme çalışıyor
- **Silme yerine "aktif" bayrağı:** plan ve bildirim kayıtlarında v1'deki
  fiziksel silme yerine `aktif_durum`/`okundu` geçmişi korunuyor
- **Günlük benzersizlik:** diyet/egzersiz takibinde aynı gün için yinelenen
  satırlar hem unique indeks hem upsert ile engelleniyor
