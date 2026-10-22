# Changelog

## [2.4.0] — 2026-10-22

Yeni nesil görsel dil: giriş ekranı, ana sayfa ve kartların tamamı yuvarlatılmış,
anti-aliased yüzeylere geçti. Kare kenarlı eski bileşenler kaldırıldı; tek
pencere sayfa mimarisi tek kabukta toplandı.

### Eklenen

- **`ui/surface.py`:** Pillow ile çizilen önbellekli yüzeyler — `Panel`
  (yuvarlatılmış kart), `Button` (gradyan düğme ve çip), `Avatar`,
  `hero_banner`, `composite_card` ve giriş arka planı `backdrop_image`
- **Giriş ekranı:** ışıklı lacivert arka plan, EKG çizgisi, cam benzeri form
  kartı, gradyan CTA, özellik vitrini, alan içi yer tutucular ve
  "Güvenli oturum" satırı
- **Ana sayfa:** fotoğraflı yuvarlatılmış karşılama şeridi; metrik kartları
  içeriğe göre boyutlanır, sparkline'lar korunur
- **Kenar çubuğu:** yuvarlatılmış gezinme öğeleri ve kullanıcı kartı
- **`theme.display()`:** Windows'ta Segoe UI Semibold / Variable Display
  varsa başlıklarda kullanılan yarı kalın font
- **`scripts/capture_screens.py --out DIR`:** ekran görüntüleri başka bir
  klasöre üretilebilir; tüm ekranlar artık tutarlı 1920×1080 (1080p)
- **`ui/icons.py`:** ikonlar artık Pillow ile 4× süper örneklenip anti-aliased
  basılıyor (`icon_image`, `badge_image`); Tk Canvas'ın kenar yumuşatmasız
  çizgi/çokgenleri yerine keskin, pürüzsüz PNG benzeri sonuç
- **Hasta avatarları:** Hastalarım tablosu, ana sayfa "Son Ölçümler" listesi
  ve hasta detay başlığı artık baş harfli, duruma göre renklenen avatarlar
  gösteriyor (önceden tüm satırlarda aynı jenerik damla ikonu vardı)
- **Marka logosu:** `icons.brand_image()` artık Tk'nin piksel atlayan
  `subsample()`'ı yerine PIL LANCZOS ile küçültülüyor (bulanıklık giderildi)
- **`LICENSE`:** MIT lisansı eklendi; `pyproject.toml` ve README'ye işlendi
- **README:** CI ve lisans rozetleri eklendi

### Yeniden Yapılandırılan

- **`ui/pages/doctor.py` (1441 satır) → `ui/pages/doctor/` paketi:** sayfalar
  işleve göre ayrı dosyalara bölündü — `patients.py` (liste/ekle/detay),
  `alerts.py`, `appointments.py`, `reports.py`, `plans.py`, ortak sabitler
  `_common.py`'de. Dışa açık API (`main_menu.py`'nin
  `from .pages.doctor import ...` içe aktarması) değişmedi; `__init__.py`
  tüm sayfa sınıflarını yeniden dışa aktarır.
- **`ui/pages/patient.py` (945 satır) → `ui/pages/patient/` paketi:** aynı
  desenle `measure.py`, `history.py`, `compliance.py`, `insulin.py`,
  `notifications.py`, `plans.py`, `appointments.py`, `lifestyle.py`'ye
  bölündü.

### Düzeltilen (bu turda)

- **Ekran görüntüsü çözünürlüğü:** `capture_screens.py` artık her sayfa için
  pencereyi tam 1920×1080'e sabitliyor; önceki sürümde çok ekranlı/sanal
  ekran kurulumlarında ekrandan ekrana 1780×1110, 1420×879 gibi farklı
  boyutlar çıkabiliyordu
- **Ekran görüntüsü alırken `-topmost`:** kaldırıldı; pencere artık sistem
  genelinde önplana atılmıyor (başka bir monitördeki işi bölmüyor)

### Değişen

- **Pillow** artık çalışma zamanı bağımlılığı (`requirements.txt`);
  `baslat.bat` içe aktarmayı denetler. `requirements-dev.txt` yalnızca
  `-r requirements.txt` içerir.
- **Sürüm tek kaynaktan:** `diyabet_takip/__init__.py` `__version__` (2.4.0);
  kabuk ve `pyproject.toml` bunu kullanır
- **Kartlar:** `pages/base.card`, `metric`, `notice`, `theme.stat_card` ve
  ana sayfa kartları yuvarlatılmış `Panel`'e geçti
- **Düğmeler:** `theme.button` yuvarlatılmış `surface.Button` döndürür;
  `configure(text=...)` çağrıları geriye dönük uyumludur
- **Demo çipleri:** yalnızca seed hesapları (T.C. no ile) gösterilir; önceden
  ilk dört hasta listeleniyordu
- **README:** ~310 satırdan ~80 satıra indirildi; uzun mimari/özellik
  anlatımı ve tek tek sıralanan büyük ekran görüntüleri yerine kısa bir
  özet ve küçük bir ekran görüntüsü galerisi kondu. Ayrıntılı dosya haritası
  ve mimari `docs/proje-yapisi.md`'ye taşındı.

### Kaldırılan

- Kabukta artık kullanılmayan eski ekranlar: `ui/doctor/`, `ui/patient/` ve
  `ui/profile.py`. Doktor raporu etiketleri `ui/helpers.py` içine taşındı.
- `ui/helpers.py` içindeki kullanılmayan pencere/form yardımcıları ve
  `theme.py` içindeki kullanılmayan fabrikalar (gradient_canvas, tint, shade,
  scrolled_text vb.)

### Düzeltilen

- **`pages/base.metric()`:** `spark` verildiğinde bozuk import
  (`from ...ui import theme`) yüzünden çökme riski giderildi
- **`generate_demo_data.py --reset`:** sabit `"diyabet_takip"` yerine etkin
  `MONGODB_DB` veritabanını siler; ayrı bir veritabanında güvenle denenebilir
- **Sürüm tutarsızlığı:** pyproject ve paket sürümü (2.3.0) ile arayüz (2.4.0)
  eşitlendi
- **Kırık README görselleri:** silinmiş ekran görüntülerine verilen bağlantılar
  kaldırıldı

## [2.3.0] — 2026-10-22

Premium dashboard ve görsel tutarlılık sürümü: ana menü, tile ızgarasından
sabit menülü, veri odaklı bir klinik panoya dönüştü. Arayüzdeki teknik
veritabanı/güvenlik ifadeleri sadeleştirildi; emoji yerine işlev renkli
vektör ikonlar kullanıldı.

### Eklenen

- **Yeni dashboard kabuğu:** sabit sol menü, üst profil/bildirim/çıkış barı,
  kaydırılabilir içerik ve alt footer; tüm ekranlar mevcut modal akışını
  koruyarak bu kabuğun üzerinden açılır
- **Doktor panosu:** karşılama hero'su, dört metrik kartı (toplam hasta,
  bugün ölçüm, ortalama kan şekeri, riskli hasta), hedef bantlı 7 günlük
  trend grafiği, son ölçümler, risk sıralı hasta listesi, 30 günlük kan
  şekeri dağılımı ve hızlı işlemler
- **Hasta panosu:** son kan şekeri, 7 günlük ortalama, uyum skoru ve
  yaklaşan randevu kartları; kişisel trend, son ölçümler, günlük plan,
  dağılım ve hızlı işlemler
- **`ui/icons.py`:** Canvas tabanlı vektör ikon seti (droplet, syringe,
  calendar, trend, users, alert, report, insulin, kalp vb.), renkli
  `badge()` rozetleri ve `brand_image()` marka işareti
- **`ui/dashboard_home.py`:** 3 → 2 kolon yeniden akış, 4 → 2×2 metrik
  düzeni, sparkline'lar, donut dağılım, boş/hata durumları ve gerçek veri
  bağlantıları
- **`ui/charts.py` → `plot_dashboard_trend`:** koyu tema, alan dolgusu,
  70–140 mg/dL hedef bandı ve kompakt eksenler
- **`db/doctors.py` / `db/records.py`:** dashboard trendi, ortalama,
  dağılım, ölçüm sayıları ve son ölçüm sorguları
- **Hero görseli:** `assets/hero-klinik.png`; `scripts/make_hero.py` ile
  Pexels #5452293 kaynağından yeniden üretilebilir
- **`requirements-dev.txt`:** yalnızca geliştirici araçları için Pillow
- **Yeni ekran görüntüsü:** `07-hastalarim.png` (eski doktor paneli
  görüntüsünün yerine hasta filtreleme ekranı)

### Değişen

- **Palet:** APP_BG `#0a0f1a`, SIDEBAR_BG `#070c16`, CARD_BG `#111a2c`,
  CARD_HOVER `#1b2740`, BORDER `#273350`, PRIMARY `#4f8cff`,
  PRIMARY_DARK `#2f6fe0`, PRIMARY_SOFT `#152747`, CYAN `#22d3ee`;
  gradient mavi → indigo
- **Giriş/kayıt:** lacivert-mavi/cyan aurora arka plan; marka işareti
  `assets/app.png`; form ikonları renkli vektör; göz açık/kapalı durumu;
  “MongoDB destekli”, “PBKDF2”, veritabanı adı gibi teknik ifadeler
  kaldırıldı
- **Butonlar:** yalnızca renk geçişi kullanan hover animasyonu; boyut ve
  padding sabit olduğu için titreme yok
- **Ana pencere:** varsayılan boyut ekrana göre 920 piksel yüksekliğe kadar;
  minimum 1000×680; F11 tam ekran ve Escape geri dönüş korunuyor
- **Dashboard yerleşimi:** 1440×920'de tüm doktor kartları ve footer tek
  ekrana sığar; hasta panosunda doktor notu kartı kaydırmayla açılır
- **Demo randevular:** hasta indeksine göre farklı gün ve 30 dakikalık
  saat aralıkları; aynı tarih-saatte çakışma yok
- **Gece yarısı demo üretimi:** bugünün öğünleri henüz gelecekteyse panonun
  “Bugün Ölçüm” kartı boş kalmaması için güncel bir ölçüm ekleniyor
- **Tablo hücreleri:** emoji yerine okunur “Evet / Hayır / —” metinleri
- **Doktor/hasta ekranları:** emoji başlıklar renkli vektör rozetlere,
  sekmelerdeki emojiler sade metinlere dönüştürüldü; randevu iptal
  düğmesindeki koyu emoji kaldırıldı
- **README/CHANGELOG/proje-yapısı:** v2.3 ekranları, mimari ve hero kaynağı
  ile güncellendi

### Düzeltilen

- `ui/icons.py` içindeki hatalı `_pt(...)` çağrıları (alert, shield, folder,
  apple) düzeltildi; 35 ikon çizim testinden geçti
- Hero banner'da `Dr. Dr.` tekrarı ve avatar baş harflerinde “Dr.” kalması
  giderildi
- Son ölçüm satırları sıkıştırılarak beş kayıt tek karta sığdırıldı;
  donut dikey ortalandı, plan yüzdeleri görünür hâle getirildi
- Hasta uyum skoru aksanı eşiklere göre dinamikleştirildi
  (`<50` kırmızı, `<75` amber, `≥75` yeşil)
- Doktor dashboard'unda alt boşluk ve 1440×920'de taşma giderildi;
  ekran görüntüleri beyaz bant kalmadan tam pencereye kırpılıyor
- Eski `07-doktor-paneli.png` ve geçici geliştirme dosyaları kaldırıldı

## [2.2.0] — 2026-10-21

Görsel revizyon sürümü: uygulamanın tamamı koyu temaya geçti, ekranlar
responsive hâle geldi, butonlar geometri değiştirmeyen renk animasyonlarıyla
canlandı ve şifre politikası sıkılaştırıldı.

### Eklenen

- **Global koyu tema:** `theme.py` yeni palet (APP_BG/CARD_BG/BORDER/PRIMARY)
  ve ttk stilleri; Treeview, Notebook, Combobox, Scrollbar, Listbox ve
  DateEntry dâhil tüm bileşenler koyu
- **Responsive ana menü:** üstte canlı özet şeridi (4 metrik kartı) ve 2–5
  kolona yeniden akan tile grid; 900×740'tan 1850×1000'e kadar akıcı
- **Buton hover animasyonları:** `theme.animate_color` ile renk
  interpolasyonu; geometri/padding değişmediği için titreme yok
- **Şifre politikası:** en az 8 karakter, 1 büyük, 1 küçük, 1 rakam,
  1 özel karakter — otoriter kontrol `auth_service.validate_password`
  içinde; kayıt ekranında canlı kural listesi (●/○) ve zayıf şifre uyarısı
- **Uygulama ikonu:** `assets/app.ico` + `assets/app.png`;
  `SetCurrentProcessExplicitAppUserModelID` sayesinde görev çubuğunda
  Python logosu yerine uygulama ikonu görünür
- **Tam ekran:** F11 ile aç/kapat, Escape ile çık; ana menüde
  "Tam Ekran" butonu
- **Empty-state'ler:** boş tablolarda "kayıt bulunamadı" rozeti (uyarılar,
  kritik hastalar, bildirimler, insülin, randevular, hastalar)
- `docs/screenshots/01b-kayit-ekrani.png` (canlı şifre kuralları)

### Değişen

- Giriş, kayıt ve ana menü ekranları koyu gradient + aurora arka planla
  yeniden çizildi; pencere boyutuna göre yerleşim ve renk geçişleri
  güncelleniyor
- Randevu etiketleri: **Planlandı** amber, **Tamamlandı** yeşil,
  **İptal Edildi** gri; demo üretici tarihe göre doğru durumu yazıyor
- Uyum yüzdeleri tam sayıya yuvarlandı; tarih/etiket hizalamaları düzeltildi
- Rapor penceresi alan adları yerine okunur etiketler (Ad Soyad, Ortalama
  Kan Şekeri, Rapor Aralığı...) ve koyu kaydırma çubuğuyla çalışıyor
- Demo veri üretici: Mehmet için plan/not/randevu/belirti kayıtları,
  bugünün ölçümleri, okunmamış bildirimler ve 7 günden eski uyarıların
  okundu işaretlenmesi eklendi

### Düzeltilen

- Doktor paneli artık en yeni uyarıları gösteriyor (tarih sıralaması)
- Hasta ana menü özet şeridi: son kan şekeri, 7 günlük uyum, okunmamış
  bildirim ve yaklaşan randevu
- Uzun form/label metinlerinin yatayda kırpılması (wraplength + justify)
  giderildi
- `reports.py` içindeki hatalı `helpers.scrolled_text` çağrısı
  `theme.scrolled_text` oldu; beyaz Tk scrollbar koyu ttk ile değiştirildi
- Notebook aktif sekmesindeki beyaz odak halkası kaldırıldı
- `smoke_test.py` yeni şifre politikasına uyarlandı (artık **33 denetim**)

## [2.1.0] — 2026-10-21

Yeni nesil arayüz sürümü: koyu gradient giriş/kayıt ekranı, renkli aksan
sistemi ve tek tıkla başlatıcılar.

### Eklenen

- **Yeni giriş ekranı:** split-hero koyu tema — gradient arka plan + aurora
  lekeleri, gradient başlık ve CTA butonu, özellik pill'leri, **Giriş /
  Kayıt Ol sekmeleri**
- **Kendin kaydolma (Kayıt Ol):** Hasta/Doktor rol seçimi, hasta için diyabet
  tipi segment seçici, şifre tekrar doğrulaması; hastalar en az hastalı
  doktora otomatik atanır
- **Tek tıkla demo girişi:** giriş kartındaki çip butonlarla (Dr. Ahmet /
  Mehmet / Ayşe) şifre yazmadan giriş
- **Şifre gösterme (göz) düğmesi** ve "Şifremi unuttum?" bağlantısı
- **Renkli aksan sistemi:** her özellik kendi rengiyle (kan şekeri kırmızı,
  diyet yeşil, egzersiz turuncu, insülin mor…); ana menü tile'larında renkli
  bant + ikon rozeti; kan şekeri grafikleri kırmızı çizgi + yeşil hedef
  bandı; ölçüm geçmişi tablosunda hiperglisemi/hipoglisemi satır renkleri
- **Tek tık başlatıcılar:** `baslat.bat` (paket + MongoDB kontrolü + açılış),
  `demo-veri.bat`, `dogrula.bat`
- `docs/proje-yapisi.md` dosya haritası
- Ana menü üst bandında koyu gradient bant

### Düzelen

- **form_row master hatası:** Tk'te widget'ın master'ı olmayan bir çerçeveye
  grid edilemez; tüm form ekranlarında (randevu, hasta ekleme…) giriş
  alanları çökük görünüyordu
- Smoke test tekrar koşumunda temizlik (`99999999999` kalıntısı) — artık
  idempotent

## [2.0.0] — 2026-10-21

v1 (2021, tek dosyalık MySQL ilk sürümü → `docs/legacy/`)'in tamamına
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
- **Geliştirici araçları:** `scripts/smoke_test.py` (33 uçtan uca denetim),
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
