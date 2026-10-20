# Veri Modeli — v1 (MySQL) → v2 (MongoDB)

Bu doküman, v1'in 27 SQL tablosunun v2'nin 22 Mongo koleksiyonuna dönüşümünü ve
v1'in trigger/prosedür/event/view ürünlerinin **Python servis/repo katmanına**
geçişini tarif eder. Legacy kaynaklar: `docs/legacy/`.

## 1. Tablo → Koleksiyon eşlemesi

| v1 tablo | v2 koleksiyon | Not |
| --- | --- | --- |
| `kullanicilar` | `users` | `sifre_hash` artık PBKDF2 (düz metin yok) |
| `kullanici_rolleri` | *(tablo yok)* | `users.rol` string alanı ("Doktor"/"Hasta") |
| `doktorlar` | `doctor_profiles` | `user_id` → `users._id` |
| `hastalar` | `patient_profiles` | `user_id` → `users._id` |
| `hasta_hedefleri` | *(tablo yok)* | `patient_profiles` içinde `hedef_kan_sekeri_min/max` |
| `diyet_turleri` | `diet_types` | seed ile 3 tür |
| `egzersiz_turleri` | `exercise_types` | seed ile 6 tür |
| `belirtiler` | `symptom_types` | seed ile 8 belirti |
| `kan_sekeri_olcumleri` | `measurements` | `gecerli` alanı servis hesaplar |
| `hasta_belirtileri` | `symptom_records` | `kaydeden` ("Hasta Kaydı" / "Doktor Girişi") |
| `diyet_planlari` | `diet_plans` | `aktif_durum` + geçmiş satırları |
| `egzersiz_planlari` | `exercise_plans` | `aktif_durum` + geçmiş satırları |
| `diyet_takibi` | `diet_logs` | günlük upsert (unique `hasta_id+takip_tarihi`) |
| `egzersiz_takibi` | `exercise_logs` | günlük upsert (unique `hasta_id+takip_tarihi`) |
| `insulin_onerileri` | `insulin_recommendations` | unique `hasta_id+tarih+olcum_tipi` |
| `uyari_turleri` | `alert_types` | seed ile 6 uyarı tipi |
| `uyarilar` | `alerts` | doktora/hastaya |
| `bildirimler` | `notifications` | okundu yönetimi |
| `kural_tabani` | `rule_base` | seed ile 8 kural |
| `hasta_uyum_skorlari` | `compliance_scores` | günlük upsert |
| `sistem_ayarlari` | `system_settings` | `anahtar` unique |
| `doktor_hasta_notlari` | `doctor_notes` | `gorunurluk` ile paylaşımlı/özel |
| `kan_sekeri_istatistikleri` | `blood_sugar_stats` | günlük upsert |
| `randevu_sistemi` | `appointments` | v1'de modellenmiş, v2'de ekran da var |
| `sistem_loglari` | *(bırakıldı)* | uygulama içi hata mesajları yeterli |
| `ilac_takibi` | *(roadmap)* | v2'de modellenmedi; insülin önerileri benzer akış |
| `ilac_kullanim_kayitlari` | *(roadmap)* | — |

## 2. Trigger / Prosedür / Event / View → Python

| v1 nesnesi | v2 karşılığı |
| --- | --- |
| `TRIGGER kan_sekeri_uyari_kontrol` | `services.alert_service.evaluate_measurement()` — ekleme sonrası çağrılır (`ui.patient.measurements` ve `scripts/generate_demo_data.py`) |
| `PROCEDURE insulin_onerisi_olustur` | `services.insulin_service.generate_for_day()` (öğün ortalaması → ml doz) |
| `PROCEDURE gunluk_insulin_onerileri_yonet` | aynı fonksiyon (gün bazlı orkestrasyon) |
| `PROCEDURE gunluk_olcum_kontrol_ve_uyari` | `jobs.py` → `alert_service.check_missing_measurements()` |
| `PROCEDURE hasta_uyum_skoru_hesapla` | `services.compliance_service.compute_for()` (7 gün 0.4/0.3/0.3) |
| `PROCEDURE gunluk_istatistik_hesapla` | `services.stats_service.compute_for()` (`blood_sugar_stats` upsert) |
| `PROCEDURE kural_tabanli_oneri_getir` | `services.recommendation_service.recommend()` (rule_base eşleme) |
| `PROCEDURE hasta_rapor_olustur` | `services.report_service.build_report()` (bölmeli rapor) |
| `VIEW doktor_dashboard` | `db.doctors.doctor_dashboard()` — 5 metrikli tek pipeline grubu |
| `VIEW kritik_hastalar` | `db.doctors.critical_patients_for_doctor()` — risk kategorili aggregation |
| `VIEW doktor_hasta_listesi` | `db.doctors.list_patients_for_doctor()` / `search_patients_for_doctor()` |
| `VIEW hasta_ozet_bilgileri` | `db.records.patient_summary_for_current_user()`
| `VIEW haftalik_performans` | `db.records.compliance_history()` + `ui.charts.plot_compliance_percentages()` |
| `VIEW hasta_performans_detay` | hasta uyum ekranı (`ui.patient.tracking`) |
| `EVENT event_gunluk_olcum_kontrol` | `python -m diyabet_takip.jobs` (CLI; zamanlayıcı dışarıda: Görev Zamanlayıcı/cron) |
| `EVENT event_gunluk_uyum_skoru_hesapla` | `jobs.py --all-patients` |
| `EVENT event_gunluk_kan_sekeri_istatistikleri` | `jobs.py --all-patients` |

## 3. Koleksiyonlar ve indeksler

`diyabet_takip.db.bootstrap.ensure_schema()` idempotent kurulur:

```python
USERS, DOCTOR_PROFILES, PATIENT_PROFILES, DIET_TYPES, EXERCISE_TYPES,
SYMPTOM_TYPES, MEASUREMENTS, DIET_PLANS, EXERCISE_PLANS, DIET_LOGS,
EXERCISE_LOGS, INSULIN_RECS, ALERT_TYPES, ALERTS, NOTIFICATIONS,
DOCTOR_NOTES, COMPLIANCE_SCORES, APPOINTMENTS, SYSTEM_SETTINGS, RULE_BASE,
SYMPTOM_RECORDS, BLOOD_SUGAR_STATS
```

Kritik indeksler:

- `users`: `tc_kimlik_no` unique, `eposta` unique, `rol`
- `patient_profiles`: `user_id` unique, `doktor_id`
- `measurements`: `(hasta_id, olcum_zamani -1/+1)`, `(hasta_id, gecerli, olcum_zamani -1)`
- `diet_logs` / `exercise_logs`: `(hasta_id, takip_tarihi)` **unique** — günlük yinelenen kaydı engeller (upsert ile)
- `insulin_recommendations`: `(hasta_id, tarih, olcum_tipi)` **unique**
- `symptom_records`: `(hasta_id, belirti_id, kayit_tarihi)` **unique**
- `blood_sugar_stats`: `(hasta_id, istatistik_tarihi)` **unique**
- `compliance_scores`: `(hasta_id, hesaplama_tarihi)` **unique**
- `alerts`: `(doktor_id, okundu, olusturma_tarihi -1)`, `(hasta_id, uyari_tarihi -1)`
- `appointments`: `(doktor_id, randevu_tarihi -1)`, `(hasta_id, randevu_tarihi -1)`

## 4. Tasarım notları

- **Tarihler:** Tüm gün bazlı alanlar midnight-naive `datetime` olarak saklanır
  (Mongo'da tek tarih tipi olduğu için); repo katmanı `as_date()`/`as_time()`
  ile `date`/`time` nesnesine çevirir. `date_at()` yardımcısı gün eşlemesini
  stabil yapar (timezone kayması yok).
- **İlişkiler:** REFERANS bütünlüğü uygulama katmanındadır; silme yok,
  yalnız `aktif_durum` bayrağı. `doktor_id`/`hasta_id` alanları `ObjectId`
  referanslarıdır ve sorgular `$lookup` yerine çift sorgu + indeks kullanır.
- **Unique kısıtları upsert akışlarıyla birlikte çalışır:** `replace_one(upsert)`
  çağrısı, aynı gün için ikinci kaydı bünyesinde çözer.
- **Standalone mongod:** transaction/koleksiyon birbirine bağımlı yazımlar
  sıralı uygulanır (`measurement_service` önce ölçüm sonra uyarı/bildirim).
