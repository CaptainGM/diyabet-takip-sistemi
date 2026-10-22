# Proje Yapısı — Dosya Haritası

Bu doküman, projedeki her klasör ve dosyanın ne yaptığını açıklayan haritadır.
Depoda gezinirken yolunuzu kaybetmeyin.

```text
diyabet-takip-sistemi/
├── baslat.bat                 # TEK TIKLA BAŞLAT: paket + MongoDB kontrolü → main.py
├── demo-veri.bat              # Demo verisini silip yeniden üretir (4 hasta, ~90 gün)
├── dogrula.bat                # 33 uçtan uca denetim (GUI açmaz)
├── main.py                    # python main.py → diyabet_takip.app.launch()
├── requirements.txt           # pymongo, matplotlib, tkcalendar, Pillow (çalışma zamanı)
├── requirements-dev.txt       # -r requirements.txt (ekran görüntüsü aracı da bunu kullanır)
├── pyproject.toml             # proje meta (2.4.0) + ruff lint ayarları
├── LICENSE                    # MIT
├── .env.example               # MONGODB_URI / HOST / PORT / DB örneği
├── docker-compose.yml         # yalnız MongoDB kapsayıcısı
├── assets/
│   ├── app.ico / app.png      # görev çubuğu + pencere + marka işareti
│   └── hero-klinik.png        # ana sayfa karşılama fotoğrafı (Pexels #5452293)
│
├── diyabet_takip/            ★ ANA PAKET
│   ├── __init__.py            # paket + __version__ (tek sürüm kaynağı)
│   ├── __main__.py            # python -m diyabet_takip
│   ├── app.py                 # launch() — kök pencere; ui.app'e kısayol
│   ├── config.py              # MONGODB_URI/HOST/PORT/DB + basit .env okuyucu
│   ├── state.py               # Session — oturum kimliği + pencere referansı
│   ├── security.py            # PBKDF2-HMAC-SHA256 hash / verify / is_hashed
│   ├── theme.py               # palet, fontlar, ttk stilleri, buton/entry/tarih
│   │                          # fabrikaları, stat_card + sparkline
│   │
│   ├── db/                    ── VERİ KATMANI (repo)
│   │   ├── client.py          # get_db(), get_db_strict(), as_date/as_time/date_at
│   │   ├── bootstrap.py       # 22 koleksiyon sabiti + indeksler + seed_if_empty
│   │   ├── records.py         # iki rolün ortak sorguları; trend/dağılım
│   │   ├── doctors.py         # doktor repo: liste/filtre/panel/uyarı/kritik/
│   │   │                      # dashboard trend & dağılım/atama
│   │   ├── patients.py        # hasta repo: günlük upsert'ler, bildirim, randevu
│   │   └── reference.py       # diyet/egzersiz/belirti/uyarı tipleri + arama
│   │
│   ├── services/              ── İŞ KURALLARI (v1 trigger/prosedür karşılıkları)
│   │   ├── measurement_service.py  # ölçüm ekleme + saat aralığı (geçerli mi?)
│   │   ├── alert_service.py        # eşik uyarıları + eksik ölçüm taraması
│   │   ├── insulin_service.py      # öğün ortalaması → doz; günlük öneri
│   │   ├── compliance_service.py   # 7 günlük uyum (.4/.3/.3)
│   │   ├── stats_service.py        # günlük istatistik upsert
│   │   ├── recommendation_service.py # kural tabanlı diyet/egzersiz önerisi
│   │   ├── report_service.py       # build_report() → bölmeli metin raporu
│   │   └── auth_service.py         # authenticate + hash yükseltmesi + politika
│   │
│   ├── ui/                    ── ARAYÜZ
│   │   ├── app.py             # launch(): kök pencere + tema + navigation
│   │   ├── navigation.py      # go_main / go_login callback registry
│   │   ├── surface.py         # ★ Pillow yüzeyleri: yuvarlatılmış Panel, Button,
│   │   │                      #   Avatar, hero_banner, login_backdrop (önbellekli)
│   │   ├── login_screen.py    # giriş/kayıt: ışıklı arka plan, EKG, cam kart,
│   │   │                      # demo çipleri (bootstrap hesapları), şifre kuralları
│   │   ├── main_menu.py       # kabuk: sidebar (yuvarlatılmış gezinme), topbar,
│   │   │                      # kaydırılabilir içerik, rol bazlı sayfa yönlendirici
│   │   ├── dashboard_home.py  # ana sayfa: fotoğraflı karşılama, metrikler, trend,
│   │   │                      # son ölçümler, hasta/plan, donut, hızlı işlemler
│   │   ├── icons.py           # Pillow ile anti-aliased vektör ikonlar, avatar_image()
│   │   ├── helpers.py         # ASSETS, tarih biçimleri, rapor etiketleri/biçimi
│   │   ├── charts.py          # matplotlib: trend, dashboard trendi, uyum yüzdeleri
│   │   │
│   │   └── pages/             — Tek pencere içindeki sayfalar (kabuğa gömülür)
│   │       ├── base.py        # card, section, metric, table, notice, segmented, Page
│   │       ├── doctor/         ── doktor sayfaları (işleve göre ayrı dosyalarda)
│   │       │   ├── _common.py  # paylaşılan sabitler + _date/_value_text
│   │       │   ├── patients.py # hasta listesi, ekleme, detay (sekmeli klinik görünüm)
│   │       │   ├── alerts.py   # hasta uyarıları + kritik hastalar
│   │       │   ├── appointments.py # randevu oluşturma/iptal/takvim
│   │       │   ├── reports.py  # tarih aralığına göre metin raporu
│   │       │   └── plans.py    # diyet/egzersiz/belirti atama
│   │       ├── patient/        ── hasta sayfaları (işleve göre ayrı dosyalarda)
│   │       │   ├── _common.py  # paylaşılan sabitler + _num/_yes
│   │       │   ├── measure.py  # kan şekeri ölçümü girişi
│   │       │   ├── history.py  # geçmiş ve trend grafiği
│   │       │   ├── compliance.py # diyet/egzersiz/ölçüm uyum takibi
│   │       │   ├── insulin.py  # insülin önerileri
│   │       │   ├── notifications.py # bildirim merkezi
│   │       │   ├── plans.py    # doktorun atadığı planlar + paylaşılan notlar
│   │       │   ├── appointments.py # randevularım
│   │       │   └── lifestyle.py # günlük diyet/egzersiz kaydı + belirti takibi
│   │       └── profile.py     # profil ve şifre değiştirme (iki rol)
│   │
│   └── jobs.py                # v1 EVENT CLI: python -m diyabet_takip.jobs
│
├── scripts/
│   ├── smoke_test.py          # 33 uçtan uca denetim (CI'da da çalışır)
│   ├── generate_demo_data.py  # --reset: MONGODB_DB'yi siler; zengin demo veri üretir
│   ├── capture_screens.py     # README görüntülerini docs/screenshots altına çeker
│   │                          # (--out DIR ile başka klasöre)
│   ├── make_hero.py           # Pexels kaynağından hero-klinik.png üretir
│   └── make_icon.py           # assets/app.ico üretir
│
├── docs/
│   ├── data-model.md          # v1 tablo → v2 koleksiyon + servis eşlemesi
│   ├── proje-yapisi.md        # bu dosya
│   ├── screenshots/           # 21 UI görüntüsü (README kullanır)
│   └── legacy/                # v1: tek dosya Python + 946 satır MySQL şeması
│
└── .github/workflows/ci.yml   # CI: ruff + şema/seed + 33 denetim
```

## İki rolün ekran akışı

```text
Giriş (login_screen)
 └─ kabuk (main_menu) — sidebar role göre değişir
     ├─ DOKTOR: Ana Sayfa → Hastalarım → Uyarılar → Randevular → Raporlar
     │           → Plan/Belirti → Profilim
     └─ HASTA : Ana Sayfa → Ölçüm Gir → Geçmiş & Grafik → Uyum Takibi
                 → İnsülin → Bildirimler → Planlarım → Randevularım → Profilim
```

Tüm sayfalar kabuğun içinde açılır (`main_menu.route`); ayrı pencere açılmaz.

## Veri akışı (bir ölçüm yazılınca)

```text
ui.pages.patient.MeasurePage (form)
  → services.measurement_service.insert_measurement()
      → db MEASUREMENTS insert (gecerli = saat bandına göre)
      → services.alert_service.evaluate_measurement()   # eşik → alerts
      → saat dışıysa → db NOTIFICATIONS insert          # hastaya bildirim
  → bildirim (kayıt sonucu / saat dışı uyarısı)
```

Dashboard sorguları aynı kayıtlardan beslenir:
`doctors.recent_measurements_for_doctor`, `glucose_trend_for_doctor`,
`average_glucose_for_doctor`, `glucose_distribution_for_doctor`,
`measurement_counts_for_doctor`.

## Görsel katman (v2.4)

- **Yüzeyler (`ui/surface.py`):** Tk Canvas köşe yuvarlatmayı ve kısmi
  saydamlığı desteklemediği için şekiller Pillow ile 4× süper örnekleyerek
  çizilir. `Panel` bir kartın dört köşe parçasını önbellekten alır ve
  yeniden boyutlandırmada yalnızca taşır; içerik `panel.body` içine konur.
  `composite_card()` kartı arka plan görselinin üstüne oturtur (giriş ekranı).
- **Düğmeler:** `surface.Button` yuvarlatılmış gradyan ya da çip olarak çizilir;
  hover'da yalnızca ton değişir. `theme.button()` bunu kullanır ve eski
  `configure(text=...)` çağrılarıyla uyumludur.
- **İkonlar (`ui/icons.py`):** 35 ikonun tarifi değişmedi; render Tk Canvas
  yerine `_PILCanvas` şimi üzerinden 4× süper örneklenmiş bir PIL görüntüsüne
  yapılır (`icon_image()`, `badge_image()`, önbellekli). Tk Canvas'ın kenar
  yumuşatmasız çizgileri yerine pürüzsüz sonuç verir; `avatar_image()` aynı
  altyapıyla baş harfli avatar üretir (ör. Hastalarım tablosu satırları).
- **Marka logosu:** `brand_image()` PIL LANCZOS ile küçültülür (eskiden Tk'nin
  piksel atlayan `subsample()`'ı kullanılıyordu).
- **Palet (`theme.py`):** APP_BG `#0a0f1a`, CARD_BG `#111a2c`, BORDER `#273350`,
  CARD_EDGE `#2a3c62`, PRIMARY `#4f8cff`, CYAN `#22d3ee`; gradyan mavi → indigo.
  BLOOD/PURPLE/AMBER/GREEN işlev renkleri korunur.
- **Başlık fontu:** `theme.display()` Windows'ta Segoe UI Semibold / Variable
  Display varsa onu, yoksa kalın Segoe UI'ı kullanır.
- **Kart boyutu:** Izgarada kullanılan kartlar (`fit_width=False`) genişliği
  yerleştiren geometri yöneticisine bırakır; yükseklik içeriğe göre belirlenir.
- **Giriş ekranı:** `backdrop_image()` (lacivert gradyan, ışık lekeleri, EKG,
  vinyet) önbelleğe alınır; form kartı ve yüzen öğeler bu görselin üzerine oturur.
- **`scripts/capture_screens.py`:** README için 21 görüntü üretir. Çıktı klasörü
  `--out` ile değiştirilebilir; pencere görüntüleme sırasında üste alınır.
