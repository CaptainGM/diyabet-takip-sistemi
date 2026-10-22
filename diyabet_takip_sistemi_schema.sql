
DROP DATABASE IF EXISTS diyabet_takip_sistemi;
CREATE DATABASE diyabet_takip_sistemi CHARACTER SET utf8mb4 COLLATE utf8mb4_turkish_ci;
USE diyabet_takip_sistemi;


CREATE TABLE IF NOT EXISTS kullanici_rolleri (
    rol_id INT PRIMARY KEY AUTO_INCREMENT,
    rol_adi VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS kullanicilar (
    kullanici_id INT PRIMARY KEY AUTO_INCREMENT,
    tc_kimlik_no CHAR(11) NOT NULL UNIQUE,
    sifre VARCHAR(255) NOT NULL,
    ad VARCHAR(100) NOT NULL,
    soyad VARCHAR(100) NOT NULL,
    dogum_tarihi DATE NOT NULL,
    cinsiyet ENUM('Erkek', 'Kadın') NOT NULL,
    eposta VARCHAR(255) NOT NULL UNIQUE,
    profil_resmi LONGBLOB,
    rol_id INT NOT NULL,
    aktif_durum BOOLEAN DEFAULT TRUE,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    son_giris_tarihi TIMESTAMP NULL,
    FOREIGN KEY (rol_id) REFERENCES kullanici_rolleri(rol_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS doktorlar (
    doktor_id INT PRIMARY KEY AUTO_INCREMENT,
    kullanici_id INT NOT NULL UNIQUE,
    uzmanlik_alani VARCHAR(100),
    diploma_no VARCHAR(50),
    calisma_saatleri JSON,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS hastalar (
    hasta_id INT PRIMARY KEY AUTO_INCREMENT,
    kullanici_id INT NOT NULL UNIQUE,
    doktor_id INT NOT NULL,
    tani_tarihi DATE,
    diyabet_tipi ENUM('Tip 1', 'Tip 2', 'Gestasyonel') DEFAULT 'Tip 2',
    hedef_kan_sekeri_min INT DEFAULT 70,
    hedef_kan_sekeri_max INT DEFAULT 110,
    notlar TEXT,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS diyet_turleri (
    diyet_turu_id INT PRIMARY KEY AUTO_INCREMENT,
    diyet_adi VARCHAR(100) NOT NULL UNIQUE,
    aciklama TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS egzersiz_turleri (
    egzersiz_turu_id INT PRIMARY KEY AUTO_INCREMENT,
    egzersiz_adi VARCHAR(100) NOT NULL UNIQUE,
    aciklama TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS belirtiler (
    belirti_id INT PRIMARY KEY AUTO_INCREMENT,
    belirti_adi VARCHAR(100) NOT NULL UNIQUE,
    aciklama TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS kan_sekeri_olcumleri (
    olcum_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    olcum_tarihi DATE NOT NULL,
    olcum_saati TIME NOT NULL,
    olcum_zamani DATETIME NOT NULL,
    kan_sekeri_degeri DECIMAL(5,2) NOT NULL,
    olcum_tipi ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece', 'Diğer') NOT NULL,
    gecerli_olcum BOOLEAN DEFAULT TRUE,
    notlar TEXT,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    CONSTRAINT chk_kan_sekeri CHECK (kan_sekeri_degeri >= 0 AND kan_sekeri_degeri <= 1000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS hasta_belirtileri (
    kayit_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    belirti_id INT NOT NULL,
    kayit_tarihi DATE NOT NULL,
    siddet_seviyesi ENUM('Hafif', 'Orta', 'Şiddetli') DEFAULT 'Orta',
    notlar TEXT,
    kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    FOREIGN KEY (belirti_id) REFERENCES belirtiler(belirti_id),
    UNIQUE KEY unique_hasta_belirti_tarih (hasta_id, belirti_id, kayit_tarihi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS diyet_planlari (
    plan_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    doktor_id INT NOT NULL,
    diyet_turu_id INT NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    aktif_durum BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
    FOREIGN KEY (diyet_turu_id) REFERENCES diyet_turleri(diyet_turu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS egzersiz_planlari (
    plan_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    doktor_id INT NOT NULL,
    egzersiz_turu_id INT NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    haftalik_siklik INT DEFAULT 3,
    sure_dakika INT DEFAULT 30,
    aktif_durum BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
    FOREIGN KEY (egzersiz_turu_id) REFERENCES egzersiz_turleri(egzersiz_turu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS diyet_takibi (
    takip_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    takip_tarihi DATE NOT NULL,
    diyet_uygulandimi BOOLEAN NOT NULL,
    notlar TEXT,
    kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hasta_tarih (hasta_id, takip_tarihi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS egzersiz_takibi (
    takip_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    takip_tarihi DATE NOT NULL,
    egzersiz_yapildimi BOOLEAN NOT NULL,
    sure_dakika INT,
    notlar TEXT,
    kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hasta_tarih_egz (hasta_id, takip_tarihi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS insulin_onerileri (
    oneri_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    tarih DATE NOT NULL,
    olcum_tipi ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece') NOT NULL,
    ortalama_kan_sekeri DECIMAL(5,2) NOT NULL,
    onerilen_doz_ml DECIMAL(3,1) NOT NULL,
    uygulandi BOOLEAN DEFAULT FALSE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hasta_tarih_tip (hasta_id, tarih, olcum_tipi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS uyari_turleri (
    uyari_turu_id INT PRIMARY KEY AUTO_INCREMENT,
    uyari_adi VARCHAR(100) NOT NULL UNIQUE,
    aciklama TEXT,
    aciliyet_seviyesi ENUM('Düşük', 'Orta', 'Yüksek', 'Kritik') NOT NULL DEFAULT 'Orta'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS uyarilar (
    uyari_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    doktor_id INT NOT NULL,
    uyari_turu_id INT NOT NULL,
    uyari_mesaji TEXT NOT NULL,
    kan_sekeri_degeri DECIMAL(5,2),
    uyari_tarihi DATE NOT NULL,
    okundu BOOLEAN DEFAULT FALSE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
    FOREIGN KEY (uyari_turu_id) REFERENCES uyari_turleri(uyari_turu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS sistem_loglari (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    kullanici_id INT,
    islem_tipi VARCHAR(100) NOT NULL,
    islem_detayi TEXT,
    ip_adresi VARCHAR(45),
    tarayici_bilgisi TEXT,
    islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS kural_tabani (
    kural_id INT PRIMARY KEY AUTO_INCREMENT,
    kan_sekeri_min DECIMAL(5,2),
    kan_sekeri_max DECIMAL(5,2),
    belirtiler JSON,
    onerilen_diyet_id INT,
    onerilen_egzersiz_id INT,
    aktif_durum BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (onerilen_diyet_id) REFERENCES diyet_turleri(diyet_turu_id),
    FOREIGN KEY (onerilen_egzersiz_id) REFERENCES egzersiz_turleri(egzersiz_turu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS hasta_uyum_skorlari (
    skor_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    hesaplama_tarihi DATE NOT NULL,
    diyet_uyum_orani DECIMAL(5,2) DEFAULT 0,
    egzersiz_uyum_orani DECIMAL(5,2) DEFAULT 0,
    olcum_uyum_orani DECIMAL(5,2) DEFAULT 0,
    genel_uyum_skoru DECIMAL(5,2) DEFAULT 0,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hasta_tarih_skor (hasta_id, hesaplama_tarihi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS bildirimler (
    bildirim_id INT PRIMARY KEY AUTO_INCREMENT,
    kullanici_id INT NOT NULL,
    baslik VARCHAR(200) NOT NULL,
    mesaj TEXT NOT NULL,
    bildirim_tipi ENUM('Bilgi', 'Uyarı', 'Hata', 'Başarı') DEFAULT 'Bilgi',
    okundu BOOLEAN DEFAULT FALSE,
    okunma_tarihi TIMESTAMP NULL,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS sistem_ayarlari (
    ayar_id INT PRIMARY KEY AUTO_INCREMENT,
    ayar_anahtari VARCHAR(100) NOT NULL UNIQUE,
    ayar_degeri TEXT NOT NULL,
    aciklama TEXT,
    veri_tipi ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS hasta_hedefleri (
    hedef_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    hedef_tipi ENUM('Kan Şekeri', 'Kilo', 'Egzersiz', 'Diyet') NOT NULL,
    hedef_degeri DECIMAL(8,2) NOT NULL,
    olcum_birimi VARCHAR(20) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    mevcut_durum DECIMAL(8,2),
    aktif_durum BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS doktor_hasta_notlari (
    not_id INT PRIMARY KEY AUTO_INCREMENT,
    doktor_id INT NOT NULL,
    hasta_id INT NOT NULL,
    not_basligi VARCHAR(200) NOT NULL,
    not_icerigi TEXT NOT NULL,
    etiketler JSON,
    onem_seviyesi ENUM('Düşük', 'Orta', 'Yüksek') DEFAULT 'Orta',
    gorunurluk ENUM('Sadece Doktor', 'Doktor ve Hasta') DEFAULT 'Sadece Doktor',
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS kan_sekeri_istatistikleri (
    istatistik_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    istatistik_tarihi DATE NOT NULL,
    minimum_deger DECIMAL(5,2),
    maksimum_deger DECIMAL(5,2),
    ortalama_deger DECIMAL(5,2),
    standart_sapma DECIMAL(5,2),
    olcum_sayisi INT DEFAULT 0,
    hedef_aralik_uyum_yuzdesi DECIMAL(5,2),
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hasta_tarih_istatistik (hasta_id, istatistik_tarihi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS randevu_sistemi (
    randevu_id INT PRIMARY KEY AUTO_INCREMENT,
    doktor_id INT NOT NULL,
    hasta_id INT NOT NULL,
    randevu_tarihi DATE NOT NULL,
    randevu_saati TIME NOT NULL,
    randevu_suresi INT DEFAULT 30,
    randevu_durumu ENUM('Planlandı', 'Onaylandı', 'Tamamlandı', 'İptal Edildi') DEFAULT 'Planlandı',
    randevu_notu TEXT,
    hatirlatma_gonderildi BOOLEAN DEFAULT FALSE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS ilac_takibi (
    takip_id INT PRIMARY KEY AUTO_INCREMENT,
    hasta_id INT NOT NULL,
    ilac_adi VARCHAR(200) NOT NULL,
    doz VARCHAR(100) NOT NULL,
    kullanim_saatleri JSON NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    yan_etkiler TEXT,
    aktif_durum BOOLEAN DEFAULT TRUE,
    doktor_notu TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

CREATE TABLE IF NOT EXISTS ilac_kullanim_kayitlari (
    kayit_id INT PRIMARY KEY AUTO_INCREMENT,
    takip_id INT NOT NULL,
    kullanim_tarihi DATE NOT NULL,
    kullanim_saati TIME NOT NULL,
    kullanildi BOOLEAN NOT NULL,
    gecikme_suresi INT DEFAULT 0,
    not_metni TEXT,
    kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (takip_id) REFERENCES ilac_takibi(takip_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;

DELIMITER //

DROP TRIGGER IF EXISTS kan_sekeri_uyari_kontrol//
CREATE TRIGGER kan_sekeri_uyari_kontrol
AFTER INSERT ON kan_sekeri_olcumleri
FOR EACH ROW
BEGIN
    DECLARE doktor_id_var INT;
    DECLARE uyari_mesaji_var TEXT;
    DECLARE uyari_turu_id_var INT;
    DECLARE hipoglisemi_esik DECIMAL(5,2);
    DECLARE hiperglisemi_esik DECIMAL(5,2);

    SELECT CAST(ayar_degeri AS DECIMAL(5,2)) INTO hipoglisemi_esik 
    FROM sistem_ayarlari WHERE ayar_anahtari = 'hipoglisemi_esik';

    SELECT CAST(ayar_degeri AS DECIMAL(5,2)) INTO hiperglisemi_esik 
    FROM sistem_ayarlari WHERE ayar_anahtari = 'hiperglisemi_esik';

    SELECT h.doktor_id INTO doktor_id_var
    FROM hastalar h
    WHERE h.hasta_id = NEW.hasta_id;

    IF NEW.gecerli_olcum = TRUE THEN
        IF NEW.kan_sekeri_degeri < hipoglisemi_esik THEN
            SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri seviyesi ', NEW.kan_sekeri_degeri, 
                ' mg/dL\'nin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.');
            SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Uyarı');

        ELSEIF NEW.kan_sekeri_degeri > hiperglisemi_esik THEN
            SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, 
                ' mg/dL\'nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.');
            SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Müdahale Uyarısı');

        ELSEIF NEW.kan_sekeri_degeri BETWEEN 151 AND 200 THEN
            SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, 
                ' mg/dL arasında. Diyabet kontrolü gereklidir.');
            SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'İzleme Uyarısı');

        ELSEIF NEW.kan_sekeri_degeri BETWEEN 111 AND 150 THEN
            SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, 
                ' mg/dL arasında. Durum izlenmeli.');
            SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Takip Uyarısı');
        END IF;

        IF uyari_mesaji_var IS NOT NULL THEN
            INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji, kan_sekeri_degeri)
            VALUES (NEW.hasta_id, doktor_id_var, uyari_turu_id_var, NEW.olcum_tarihi, uyari_mesaji_var, NEW.kan_sekeri_degeri);
        END IF;

    ELSE
        INSERT INTO bildirimler (kullanici_id, baslik, mesaj, bildirim_tipi)
        SELECT k.kullanici_id, 'Ölçüm Zamanı Uyarısı',
               CONCAT('Girdiğiniz ölçüm (', NEW.kan_sekeri_degeri, ' mg/dL) saat dışındadır. Lütfen önerilen zaman aralığında tekrar ölçüm yapınız.'),
               'Uyarı'
        FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
        WHERE h.hasta_id = NEW.hasta_id;
    END IF;
END;
//




DROP FUNCTION IF EXISTS gunluk_ortalama_hesapla//
CREATE FUNCTION gunluk_ortalama_hesapla(hasta_id_param INT, tarih_param DATE)
RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE ortalama DECIMAL(5,2) DEFAULT 0;
    SELECT AVG(kan_sekeri_degeri) INTO ortalama
    FROM kan_sekeri_olcumleri
    WHERE hasta_id = hasta_id_param
    AND DATE(olcum_zamani) = tarih_param
    AND gecerli_olcum = TRUE;
    RETURN IFNULL(ortalama, 0);
END//

DROP FUNCTION IF EXISTS ogun_ortalama_kan_sekeri_hesapla//
CREATE FUNCTION ogun_ortalama_kan_sekeri_hesapla(
    hasta_id_param INT,
    tarih_param DATE,
    olcum_tipi_param ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
)
RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE ortalama_deger DECIMAL(5,2);
    DECLARE total_sum DECIMAL(10,2) DEFAULT 0;
    DECLARE num_measurements INT DEFAULT 0;
    IF olcum_tipi_param = 'Sabah' THEN
        SELECT SUM(kan_sekeri_degeri), COUNT(*)
        INTO total_sum, num_measurements
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_param
        AND DATE(olcum_zamani) = tarih_param
        AND olcum_tipi = 'Sabah'
        AND gecerli_olcum = TRUE;
    ELSEIF olcum_tipi_param = 'Öğle' THEN
        SELECT SUM(kan_sekeri_degeri), COUNT(*)
        INTO total_sum, num_measurements
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_param
        AND DATE(olcum_zamani) = tarih_param
        AND olcum_tipi IN ('Sabah', 'Öğle')
        AND gecerli_olcum = TRUE;
    ELSEIF olcum_tipi_param = 'İkindi' THEN
        SELECT SUM(kan_sekeri_degeri), COUNT(*)
        INTO total_sum, num_measurements
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_param
        AND DATE(olcum_zamani) = tarih_param
        AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi')
        AND gecerli_olcum = TRUE;
    ELSEIF olcum_tipi_param = 'Akşam' THEN
        SELECT SUM(kan_sekeri_degeri), COUNT(*)
        INTO total_sum, num_measurements
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_param
        AND DATE(olcum_zamani) = tarih_param
        AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi', 'Akşam')
        AND gecerli_olcum = TRUE;
    ELSEIF olcum_tipi_param = 'Gece' THEN
        SELECT SUM(kan_sekeri_degeri), COUNT(*)
        INTO total_sum, num_measurements
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_param
        AND DATE(olcum_zamani) = tarih_param
        AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
        AND gecerli_olcum = TRUE;
    END IF;
    IF num_measurements > 0 THEN
        SET ortalama_deger = total_sum / num_measurements;
    ELSE
        SET ortalama_deger = 0;
    END IF;
    RETURN ortalama_deger;
END//

DROP FUNCTION IF EXISTS insulin_doz_hesapla//
CREATE FUNCTION insulin_doz_hesapla(ortalama_kan_sekeri DECIMAL(5,2))
RETURNS DECIMAL(3,1)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE doz DECIMAL(3,1) DEFAULT 0;
    IF ortalama_kan_sekeri < 70 THEN
        SET doz = 0;
    ELSEIF ortalama_kan_sekeri BETWEEN 70 AND 110 THEN
        SET doz = 0;
    ELSEIF ortalama_kan_sekeri BETWEEN 111 AND 150 THEN
        SET doz = 1.0;
    ELSEIF ortalama_kan_sekeri BETWEEN 151 AND 200 THEN
        SET doz = 2.0;
    ELSEIF ortalama_kan_sekeri > 200 THEN
        SET doz = 3.0;
    END IF;
    RETURN doz;
END//

DROP PROCEDURE IF EXISTS insulin_onerisi_olustur//
CREATE PROCEDURE insulin_onerisi_olustur(
    IN hasta_id_param INT,
    IN tarih_param DATE,
    IN olcum_tipi_param ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
)
BEGIN
    DECLARE avg_blood_sugar DECIMAL(5,2);
    DECLARE recommended_dose DECIMAL(3,1);
    SET avg_blood_sugar = ogun_ortalama_kan_sekeri_hesapla(hasta_id_param, tarih_param, olcum_tipi_param);
    IF avg_blood_sugar > 0 THEN
        SET recommended_dose = insulin_doz_hesapla(avg_blood_sugar);
        INSERT INTO insulin_onerileri (hasta_id, tarih, olcum_tipi, ortalama_kan_sekeri, onerilen_doz_ml)
        VALUES (hasta_id_param, tarih_param, olcum_tipi_param, avg_blood_sugar, recommended_dose)
        ON DUPLICATE KEY UPDATE
            ortalama_kan_sekeri = VALUES(ortalama_kan_sekeri),
            onerilen_doz_ml = VALUES(onerilen_doz_ml);
    END IF;
END//

DROP PROCEDURE IF EXISTS gunluk_insulin_onerileri_yonet//
CREATE PROCEDURE gunluk_insulin_onerileri_yonet(IN hasta_id_param INT, IN tarih_param DATE)
BEGIN
    CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Sabah');
    CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Öğle');
    CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'İkindi');
    CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Akşam');
    CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Gece');
END//

DROP PROCEDURE IF EXISTS gunluk_olcum_kontrol_ve_uyari//
CREATE PROCEDURE gunluk_olcum_kontrol_ve_uyari()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE hasta_id_var INT;
    DECLARE doktor_id_var INT;
    DECLARE olcum_sayisi_bugun INT;
    DECLARE gunluk_minimum_olcum INT;

    DECLARE hasta_cursor CURSOR FOR
        SELECT h.hasta_id, h.doktor_id
        FROM hastalar h
        JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
        WHERE k.aktif_durum = TRUE;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SELECT CAST(ayar_degeri AS UNSIGNED) INTO gunluk_minimum_olcum
    FROM sistem_ayarlari
    WHERE ayar_anahtari = 'minimum_gunluk_olcum';

    OPEN hasta_cursor;

    hasta_loop: LOOP
        FETCH hasta_cursor INTO hasta_id_var, doktor_id_var;

        IF done THEN
            LEAVE hasta_loop;
        END IF;

        SELECT COUNT(*) INTO olcum_sayisi_bugun
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = hasta_id_var
        AND DATE(olcum_zamani) = CURDATE() - INTERVAL 1 DAY
        AND gecerli_olcum = TRUE;

        IF olcum_sayisi_bugun = 0 THEN
            INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji)
            VALUES (hasta_id_var, doktor_id_var, (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Eksik Uyarısı'), CURDATE() - INTERVAL 1 DAY, 'Hasta bir önceki gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.');
        ELSEIF olcum_sayisi_bugun < gunluk_minimum_olcum THEN
            INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji)
            VALUES (hasta_id_var, doktor_id_var, (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Yetersiz Uyarısı'), CURDATE() - INTERVAL 1 DAY, CONCAT('Hastanın bir önceki günkü kan şekeri ölçüm sayısı yetersiz (', olcum_sayisi_bugun, '/5). Durum izlenmelidir.'));
        END IF;

    END LOOP;

    CLOSE hasta_cursor;
END//

DROP PROCEDURE IF EXISTS hasta_uyum_skoru_hesapla//
CREATE PROCEDURE hasta_uyum_skoru_hesapla(IN hasta_id_param INT, IN tarih_param DATE)
BEGIN
    DECLARE diyet_uyum DECIMAL(5,2) DEFAULT 0;
    DECLARE egzersiz_uyum DECIMAL(5,2) DEFAULT 0;
    DECLARE olcum_uyum DECIMAL(5,2) DEFAULT 0;
    DECLARE genel_skor DECIMAL(5,2) DEFAULT 0;
    DECLARE son_7_gun_toplam_gun INT DEFAULT 7;

    SELECT
        IFNULL((SUM(CASE WHEN diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
    INTO diyet_uyum
    FROM diyet_takibi
    WHERE hasta_id = hasta_id_param
    AND takip_tarihi BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param;

    SELECT
        IFNULL((SUM(CASE WHEN egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
    INTO egzersiz_uyum
    FROM egzersiz_takibi
    WHERE hasta_id = hasta_id_param
    AND takip_tarihi BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param;

    SELECT
        IFNULL((COUNT(DISTINCT DATE(olcum_zamani)) * 100.0 / son_7_gun_toplam_gun), 0)
    INTO olcum_uyum
    FROM kan_sekeri_olcumleri
    WHERE hasta_id = hasta_id_param
    AND DATE(olcum_zamani) BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param
    AND gecerli_olcum = TRUE;

    SET genel_skor = (diyet_uyum * 0.4) + (egzersiz_uyum * 0.3) + (olcum_uyum * 0.3);

    INSERT INTO hasta_uyum_skorlari (hasta_id, hesaplama_tarihi, diyet_uyum_orani, egzersiz_uyum_orani, olcum_uyum_orani, genel_uyum_skoru)
    VALUES (hasta_id_param, tarih_param, diyet_uyum, egzersiz_uyum, olcum_uyum, genel_skor)
    ON DUPLICATE KEY UPDATE
        diyet_uyum_orani = VALUES(diyet_uyum_orani),
        egzersiz_uyum_orani = VALUES(egzersiz_uyum_orani),
        olcum_uyum_orani = VALUES(olcum_uyum_orani),
        genel_uyum_skoru = VALUES(genel_uyum_skoru);
END//

DROP PROCEDURE IF EXISTS gunluk_istatistik_hesapla//
CREATE PROCEDURE gunluk_istatistik_hesapla(IN hasta_id_param INT, IN tarih_param DATE)
BEGIN
    DECLARE min_deger DECIMAL(5,2);
    DECLARE max_deger DECIMAL(5,2);
    DECLARE ort_deger DECIMAL(5,2);
    DECLARE std_sapma DECIMAL(5,2);
    DECLARE olcum_count INT;
    DECLARE hedef_uyum DECIMAL(5,2);
    DECLARE hedef_min DECIMAL(5,2);
    DECLARE hedef_max DECIMAL(5,2);

    SELECT hedef_kan_sekeri_min, hedef_kan_sekeri_max
    INTO hedef_min, hedef_max
    FROM hastalar
    WHERE hasta_id = hasta_id_param;

    SELECT
        MIN(kan_sekeri_degeri),
        MAX(kan_sekeri_degeri),
        AVG(kan_sekeri_degeri),
        STDDEV(kan_sekeri_degeri),
        COUNT(*)
    INTO min_deger, max_deger, ort_deger, std_sapma, olcum_count
    FROM kan_sekeri_olcumleri
    WHERE hasta_id = hasta_id_param
    AND DATE(olcum_zamani) = tarih_param
    AND gecerli_olcum = TRUE;

    SELECT
        IFNULL((SUM(CASE WHEN kan_sekeri_degeri BETWEEN hedef_min AND hedef_max THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
    INTO hedef_uyum
    FROM kan_sekeri_olcumleri
    WHERE hasta_id = hasta_id_param
    AND DATE(olcum_zamani) = tarih_param
    AND gecerli_olcum = TRUE;

    INSERT INTO kan_sekeri_istatistikleri
    (hasta_id, istatistik_tarihi, minimum_deger, maksimum_deger, ortalama_deger, standart_sapma, olcum_sayisi, hedef_aralik_uyum_yuzdesi)
    VALUES (hasta_id_param, tarih_param, min_deger, max_deger, ort_deger, std_sapma, olcum_count, hedef_uyum)
    ON DUPLICATE KEY UPDATE
        minimum_deger = VALUES(minimum_deger),
        maksimum_deger = VALUES(maksimum_deger),
        ortalama_deger = VALUES(ortalama_deger),
        standart_sapma = VALUES(standart_sapma),
        olcum_sayisi = VALUES(olcum_sayisi),
        hedef_aralik_uyum_yuzdesi = VALUES(hedef_aralik_uyum_yuzdesi);
END//

DROP PROCEDURE IF EXISTS kural_tabanli_oneri_getir//
CREATE PROCEDURE kural_tabanli_oneri_getir(IN kan_sekeri_param DECIMAL(5,2), IN belirtiler_json_param JSON)
BEGIN
    SELECT
        kt.kural_id,
        dt.diyet_adi AS onerilen_diyet,
        et.egzersiz_adi AS onerilen_egzersiz,
        kt.kan_sekeri_min,
        kt.kan_sekeri_max,
        kt.belirtiler
    FROM kural_tabani kt
    LEFT JOIN diyet_turleri dt ON kt.onerilen_diyet_id = dt.diyet_turu_id
    LEFT JOIN egzersiz_turleri et ON kt.onerilen_egzersiz_id = et.egzersiz_turu_id
    WHERE kt.aktif_durum = TRUE
    AND kan_sekeri_param BETWEEN kt.kan_sekeri_min AND kt.kan_sekeri_max
    AND JSON_OVERLAPS(kt.belirtiler, belirtiler_json_param)
    ORDER BY
        ABS(kan_sekeri_param - ((kt.kan_sekeri_min + kt.kan_sekeri_max) / 2))
    LIMIT 1;
END//

DROP PROCEDURE IF EXISTS hasta_rapor_olustur//
CREATE PROCEDURE hasta_rapor_olustur(IN hasta_id_param INT, IN baslangic_tarihi DATE, IN bitis_tarihi DATE)
BEGIN
    SELECT
        'Genel Bilgiler' AS bolum,
        JSON_OBJECT(
            'hasta_adi', CONCAT(k.ad, ' ', k.soyad),
            'tc_kimlik', k.tc_kimlik_no,
            'diyabet_tipi', h.diyabet_tipi,
            'tani_tarihi', h.tani_tarihi,
            'doktor_adi', CONCAT(dk.ad, ' ', dk.soyad),
            'rapor_araligi', JSON_OBJECT('baslangic', baslangic_tarihi, 'bitis', bitis_tarihi)
        ) AS veri
    FROM hastalar h
    JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
    JOIN doktorlar d ON h.doktor_id = d.doktor_id
    JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
    WHERE h.hasta_id = hasta_id_param
    UNION ALL
    SELECT
        'Kan Şekeri İstatistikleri' AS bolum,
        JSON_OBJECT(
            'ortalama', ROUND(AVG(kan_sekeri_degeri), 2),
            'minimum', MIN(kan_sekeri_degeri),
            'maksimum', MAX(kan_sekeri_degeri),
            'olcum_sayisi', COUNT(*),
            'normal_aralik_uyum', ROUND(
                SUM(CASE WHEN kan_sekeri_degeri BETWEEN 70 AND 110 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
            )
        ) AS veri
    FROM kan_sekeri_olcumleri
    WHERE hasta_id = hasta_id_param
    AND DATE(olcum_zamani) BETWEEN baslangic_tarihi AND bitis_tarihi
    AND gecerli_olcum = TRUE
    HAVING COUNT(*) > 0
    UNION ALL
    SELECT
        'Uyum Skorları' AS bolum,
        JSON_OBJECT(
            'ortalama_diyet_uyum', ROUND(AVG(diyet_uyum_orani), 2),
            'ortalama_egzersiz_uyum', ROUND(AVG(egzersiz_uyum_orani), 2),
            'ortalama_olcum_uyum', ROUND(AVG(olcum_uyum_orani), 2),
            'genel_uyum_skoru', ROUND(AVG(genel_uyum_skoru), 2)
        ) AS veri
    FROM hasta_uyum_skorlari
    WHERE hasta_id = hasta_id_param
    AND hesaplama_tarihi BETWEEN baslangic_tarihi AND bitis_tarihi
    HAVING COUNT(*) > 0
    UNION ALL
    SELECT
        'Uyarı İstatistikleri' AS bolum,
        JSON_OBJECT(
            'toplam_uyari', COUNT(*),
            'acil_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Uyarı') THEN 1 ELSE 0 END),
            'hiperglisemi_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Müdahale Uyarısı') THEN 1 ELSE 0 END),
            'olcum_eksik_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Eksik Uyarısı') THEN 1 ELSE 0 END)
        ) AS veri
    FROM uyarilar
    WHERE hasta_id = hasta_id_param
    AND uyari_tarihi BETWEEN baslangic_tarihi AND bitis_tarihi
    HAVING COUNT(*) > 0;
END//

DELIMITER ;

DROP VIEW IF EXISTS hasta_ozet_bilgileri;
CREATE VIEW hasta_ozet_bilgileri AS
SELECT
    h.hasta_id,
    CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
    k.tc_kimlik_no,
    k.dogum_tarihi,
    k.cinsiyet,
    k.eposta,
    h.diyabet_tipi,
    h.tani_tarihi,
    CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
    (SELECT COUNT(*) FROM kan_sekeri_olcumleri ks WHERE ks.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) = CURDATE() AND ks.gecerli_olcum = TRUE) AS bugun_gecerli_olcum_sayisi,
    (SELECT AVG(ks.kan_sekeri_degeri) FROM kan_sekeri_olcumleri ks WHERE ks.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) = CURDATE() AND ks.gecerli_olcum = TRUE) AS bugun_ortalama_kan_sekeri
FROM hastalar h
JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
JOIN doktorlar d ON h.doktor_id = d.doktor_id
JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
WHERE k.aktif_durum = TRUE;

DROP VIEW IF EXISTS doktor_hasta_listesi;
CREATE VIEW doktor_hasta_listesi AS
SELECT
    d.doktor_id,
    CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
    h.hasta_id,
    CONCAT(hk.ad, ' ', hk.soyad) AS hasta_adi,
    hk.tc_kimlik_no,
    h.diyabet_tipi,
    h.tani_tarihi,
    (SELECT COUNT(*) FROM uyarilar u WHERE u.hasta_id = h.hasta_id AND u.okundu = FALSE) AS okunmamis_uyari_sayisi
FROM doktorlar d
JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
JOIN hastalar h ON d.doktor_id = h.doktor_id
JOIN kullanicilar hk ON h.kullanici_id = hk.kullanici_id
WHERE dk.aktif_durum = TRUE AND hk.aktif_durum = TRUE;

DROP VIEW IF EXISTS haftalik_performans;
CREATE VIEW haftalik_performans AS
SELECT
    h.hasta_id,
    YEARWEEK(COALESCE(dt.takip_tarihi, et.takip_tarihi)) AS hafta,
    COUNT(DISTINCT COALESCE(dt.takip_tarihi, et.takip_tarihi)) AS toplam_kayit_gunu,
    SUM(CASE WHEN dt.diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) AS diyet_uygulanan_gun,
    SUM(CASE WHEN et.egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) AS egzersiz_yapilan_gun,
    ROUND(IFNULL((SUM(CASE WHEN dt.diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(dt.takip_id)), 0), 2) AS diyet_uyum_yuzdesi,
    ROUND(IFNULL((SUM(CASE WHEN et.egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(et.takip_id)), 0), 2) AS egzersiz_uyum_yuzdesi
FROM hastalar h
LEFT JOIN diyet_takibi dt ON h.hasta_id = dt.hasta_id AND dt.takip_tarihi >= DATE_SUB(CURDATE(), INTERVAL 4 WEEK)
LEFT JOIN egzersiz_takibi et ON h.hasta_id = et.hasta_id AND et.takip_tarihi >= DATE_SUB(CURDATE(), INTERVAL 4 WEEK) AND dt.takip_tarihi = et.takip_tarihi
WHERE dt.takip_id IS NOT NULL OR et.takip_id IS NOT NULL
GROUP BY h.hasta_id, YEARWEEK(COALESCE(dt.takip_tarihi, et.takip_tarihi));

DROP VIEW IF EXISTS hasta_performans_detay;
CREATE VIEW hasta_performans_detay AS
SELECT
    h.hasta_id,
    CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
    DATE(ks.olcum_zamani) AS tarih,
    ks.olcum_tipi,
    ks.kan_sekeri_degeri,
    dt.diyet_uygulandimi,
    (SELECT diyet_adi FROM diyet_planlari dpl JOIN diyet_turleri dt_t ON dpl.diyet_turu_id = dt_t.diyet_turu_id WHERE dpl.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) BETWEEN dpl.baslangic_tarihi AND IFNULL(dpl.bitis_tarihi, '9999-12-31') AND dpl.aktif_durum = TRUE LIMIT 1) AS uygulanan_diyet_adi,
    et.egzersiz_yapildimi,
    (SELECT egzersiz_adi FROM egzersiz_planlari epl JOIN egzersiz_turleri et_t ON epl.egzersiz_turu_id = et_t.egzersiz_turu_id WHERE epl.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) BETWEEN epl.baslangic_tarihi AND IFNULL(epl.bitis_tarihi, '9999-12-31') AND epl.aktif_durum = TRUE LIMIT 1) AS uygulanan_egzersiz_adi,
    CASE
        WHEN ks.kan_sekeri_degeri BETWEEN h.hedef_kan_sekeri_min AND h.hedef_kan_sekeri_max THEN 'Hedefte'
        WHEN ks.kan_sekeri_degeri < h.hedef_kan_sekeri_min THEN 'Düşük'
        ELSE 'Yüksek'
    END AS kan_sekeri_durumu
FROM hastalar h
JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id AND ks.gecerli_olcum = TRUE
LEFT JOIN diyet_takibi dt ON h.hasta_id = dt.hasta_id AND DATE(ks.olcum_zamani) = dt.takip_tarihi
LEFT JOIN egzersiz_takibi et ON h.hasta_id = et.hasta_id AND DATE(ks.olcum_zamani) = et.takip_tarihi
WHERE ks.olcum_id IS NOT NULL
ORDER BY h.hasta_id, DATE(ks.olcum_zamani), ks.olcum_zamani;

DROP VIEW IF EXISTS doktor_dashboard;
CREATE VIEW doktor_dashboard AS
SELECT
    d.doktor_id,
    CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
    COUNT(DISTINCT h.hasta_id) AS toplam_hasta_sayisi,
    COUNT(DISTINCT CASE WHEN DATE(ks.olcum_zamani) = CURDATE() THEN h.hasta_id END) AS bugun_olcum_yapan_hasta_sayisi,
    COUNT(DISTINCT CASE WHEN u.okundu = FALSE THEN u.uyari_id END) AS okunmamis_uyari_sayisi,
    COUNT(DISTINCT CASE WHEN u.uyari_tarihi = CURDATE() THEN u.uyari_id END) AS bugun_uyari_sayisi,
    ROUND(AVG(hus.genel_uyum_skoru), 2) AS ortalama_hasta_uyum_skoru
FROM doktorlar d
JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
LEFT JOIN hastalar h ON d.doktor_id = h.doktor_id
LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id AND ks.gecerli_olcum = TRUE
LEFT JOIN uyarilar u ON d.doktor_id = u.doktor_id
LEFT JOIN hasta_uyum_skorlari hus ON h.hasta_id = hus.hasta_id AND hus.hesaplama_tarihi >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
WHERE dk.aktif_durum = TRUE
GROUP BY d.doktor_id, doktor_adi;

DROP VIEW IF EXISTS kritik_hastalar;
CREATE VIEW kritik_hastalar AS
SELECT
    h.hasta_id,
    CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
    h.doktor_id,
    IFNULL(AVG(ks.kan_sekeri_degeri), 0) AS son_7_gun_ortalama_kan_sekeri,
    COUNT(DISTINCT DATE(ks.olcum_zamani)) AS son_7_gun_olcum_gun_sayisi,
    SUM(CASE WHEN ut.aciliyet_seviyesi = 'Kritik' THEN 1 ELSE 0 END) AS kritik_uyari_sayisi,
    IFNULL(hus.genel_uyum_skoru, 0) AS son_uyum_skoru,
    CASE
        WHEN IFNULL(AVG(ks.kan_sekeri_degeri), 0) < (SELECT CAST(ayar_degeri AS DECIMAL(5,2)) FROM sistem_ayarlari WHERE ayar_anahtari = 'hipoglisemi_esik')
             OR IFNULL(AVG(ks.kan_sekeri_degeri), 0) > (SELECT CAST(ayar_degeri AS DECIMAL(5,2)) FROM sistem_ayarlari WHERE ayar_anahtari = 'hiperglisemi_esik') THEN 'Kritik Durum (Kan Şekeri)'
        WHEN COUNT(DISTINCT DATE(ks.olcum_zamani)) < (SELECT CAST(ayar_degeri AS UNSIGNED) FROM sistem_ayarlari WHERE ayar_anahtari = 'minimum_gunluk_olcum') THEN 'Ölçüm Eksikliği'
        WHEN IFNULL(hus.genel_uyum_skoru, 0) < 50 THEN 'Düşük Uyum'
        ELSE 'Stabil'
    END AS durum_kategorisi
FROM hastalar h
JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id
    AND DATE(ks.olcum_zamani) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    AND ks.gecerli_olcum = TRUE
LEFT JOIN uyarilar u ON h.hasta_id = u.hasta_id
    AND u.uyari_tarihi >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
LEFT JOIN uyari_turleri ut ON u.uyari_turu_id = ut.uyari_turu_id
LEFT JOIN hasta_uyum_skorlari hus ON h.hasta_id = hus.hasta_id
    AND hus.hesaplama_tarihi = CURDATE()
WHERE k.aktif_durum = TRUE
GROUP BY h.hasta_id, k.ad, k.soyad, h.doktor_id, IFNULL(hus.genel_uyum_skoru, 0)
HAVING durum_kategorisi != 'Stabil' OR kritik_uyari_sayisi > 0
ORDER BY FIELD(durum_kategorisi, 'Kritik Durum (Kan Şekeri)', 'Ölçüm Eksikliği', 'Düşük Uyum', 'Stabil'), son_7_gun_ortalama_kan_sekeri DESC;

CREATE INDEX idx_kan_sekeri_performans ON kan_sekeri_olcumleri(hasta_id, olcum_tarihi, kan_sekeri_degeri, gecerli_olcum);
CREATE INDEX idx_diyet_takip_performans ON diyet_takibi(hasta_id, takip_tarihi, diyet_uygulandimi);
CREATE INDEX idx_egzersiz_takip_performans ON egzersiz_takibi(hasta_id, takip_tarihi, egzersiz_yapildimi);
CREATE INDEX idx_uyari_doktor_tarih_okundu ON uyarilar(doktor_id, uyari_tarihi, okundu);

SET GLOBAL event_scheduler = ON;

DELIMITER //

DROP EVENT IF EXISTS event_gunluk_olcum_kontrol//
CREATE EVENT event_gunluk_olcum_kontrol
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 5 MINUTE)
DO
BEGIN
    CALL gunluk_olcum_kontrol_ve_uyari();
END//

DROP EVENT IF EXISTS event_gunluk_uyum_skoru_hesapla//
CREATE EVENT event_gunluk_uyum_skoru_hesapla
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 10 MINUTE)
DO
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE hasta_id_var INT;

    DECLARE hasta_cursor CURSOR FOR
        SELECT hasta_id FROM hastalar;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN hasta_cursor;

    hasta_loop: LOOP
        FETCH hasta_cursor INTO hasta_id_var;
        IF done THEN
            LEAVE hasta_loop;
        END IF;
        CALL hasta_uyum_skoru_hesapla(hasta_id_var, CURDATE() - INTERVAL 1 DAY);
    END LOOP;

    CLOSE hasta_cursor;
END//

DROP EVENT IF EXISTS event_gunluk_kan_sekeri_istatistikleri//
CREATE EVENT event_gunluk_kan_sekeri_istatistikleri
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 15 MINUTE)
DO
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE hasta_id_var INT;

    DECLARE hasta_cursor CURSOR FOR
        SELECT hasta_id FROM hastalar;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN hasta_cursor;

    hasta_loop: LOOP
        FETCH hasta_cursor INTO hasta_id_var;
        IF done THEN
            LEAVE hasta_loop;
        END IF;
        CALL gunluk_istatistik_hesapla(hasta_id_var, CURDATE() - INTERVAL 1 DAY);
    END LOOP;

    CLOSE hasta_cursor;
END//

DELIMITER ;

INSERT INTO kullanici_rolleri (rol_adi) VALUES ('Doktor'), ('Hasta') ON DUPLICATE KEY UPDATE rol_adi = rol_adi;

INSERT INTO uyari_turleri (uyari_adi, aciklama, aciliyet_seviyesi) VALUES
('Acil Uyarı', 'Hastanın kan şekeri seviyesi kritik seviyelerin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.', 'Kritik'),
('Takip Uyarısı', 'Hastanın kan şekeri orta yüksek seviyede. Durum izlenmeli.', 'Orta'),
('İzleme Uyarısı', 'Hastanın kan şekeri yüksek seviyede. Diyabet kontrolü gereklidir.', 'Yüksek'),
('Acil Müdahale Uyarısı', 'Hastanın kan şekeri kritik seviyelerin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.', 'Kritik'),
('Ölçüm Eksik Uyarısı', 'Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.', 'Yüksek'),
('Ölçüm Yetersiz Uyarısı', 'Hastanın günlük kan şekeri ölçüm sayısı yetersizdir (<3). Durum izlenmelidir.', 'Orta')
ON DUPLICATE KEY UPDATE uyari_adi = uyari_adi;

INSERT INTO diyet_turleri (diyet_adi, aciklama) VALUES
('Az Şekerli Diyet', 'Şekerli gıdalar sınırlanır, kompleks karbonhidratlara öncelik verilir. Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilir.'),
('Şekersiz Diyet', 'Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanır. Hiperglisemi riski taşıyan bireylerde önerilir.'),
('Dengeli Beslenme', 'Diyabetli bireylerin yaşam tarzına uygun, dengeli ve sürdürülebilir bir diyet yaklaşımıdır. Tüm besin gruplarından yeterli miktarda alınır; porsiyon kontrolü, mevsimsel taze ürünler ve su tüketimi temel unsurlardır.')
ON DUPLICATE KEY UPDATE diyet_adi = diyet_adi;

INSERT INTO egzersiz_turleri (egzersiz_adi, aciklama) VALUES
('Yürüyüş', 'Hafif tempolu, günlük yapılabilecek bir egzersizdir.'),
('Bisiklet', 'Alt vücut kaslarını çalıştırır ve dış mekanda veya sabit bisikletle uygulanabilir.'),
('Klinik Egzersiz', 'Doktor tarafından verilen belirli hareketleri içeren planlı egzersizlerdir. Stresi azaltılması ve hareket kabiliyetinin artırılması amaçlanır.')
ON DUPLICATE KEY UPDATE egzersiz_adi = egzersiz_adi;

INSERT INTO belirtiler (belirti_adi, aciklama) VALUES
('Poliüri', 'Sık idrara çıkma'), ('Polifaji', 'Aşırı açlık hissi'), ('Polidipsi', 'Aşırı susama hissi'),
('Nöropati', 'El ve ayaklarda karıncalanma veya uyuşma hissi'), ('Kilo kaybı', 'Ani kilo kaybı'),
('Yorgunluk', 'Sürekli yorgunluk hissi'), ('Yaraların yavaş iyileşmesi', 'Yaraların normal sürede iyileşmemesi'),
('Bulanık görme', 'Görme bozukluğu')
ON DUPLICATE KEY UPDATE belirti_adi = belirti_adi;

INSERT INTO sistem_ayarlari (ayar_anahtari, ayar_degeri, aciklama, veri_tipi) VALUES
('olcum_hatirlatma_saatleri', '["07:00", "12:00", "15:00", "18:00", "22:00"]', 'Kan şekeri ölçüm hatırlatma saatleri', 'json'),
('hipoglisemi_esik', '70', 'Hipoglisemi uyarı eşiği (mg/dL)', 'number'),
('hiperglisemi_esik', '200', 'Hiperglisemi uyarı eşiği (mg/dL)', 'number'),
('minimum_gunluk_olcum', '3', 'Minimum günlük ölçüm sayısı', 'number'),
('sifre_gecerlilik_suresi', '90', 'Şifre geçerlilik süresi (gün)', 'number'),
('oturum_zaman_asimi', '30', 'Oturum zaman aşımı (dakika)', 'number')
ON DUPLICATE KEY UPDATE ayar_degeri = VALUES(ayar_degeri);

INSERT INTO kural_tabani (kan_sekeri_min, kan_sekeri_max, belirtiler, onerilen_diyet_id, onerilen_egzersiz_id) VALUES
(0, 69.99, '["Nöropati", "Polifaji", "Yorgunluk"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Dengeli Beslenme'), NULL),
(0, 69.99, '["Yorgunluk", "Kilo kaybı"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Az Şekerli Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş')),
(70, 110, '["Polifaji", "Polidipsi"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Dengeli Beslenme'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş')),
(70, 110, '["Bulanık görme", "Nöropati"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Az Şekerli Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Klinik Egzersiz')),
(70, 110, '["Poliüri", "Polidipsi"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Şekersiz Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Klinik Egzersiz')),
(110.01, 180, '["Yorgunluk", "Nöropati", "Bulanık görme"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Az Şekerli Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş')),
(110.01, 180, '["Yaraların yavaş iyileşmesi", "Polifaji", "Polidipsi"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Şekersiz Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Klinik Egzersiz')),
(180.01, 999.99, '["Yaraların yavaş iyileşmesi", "Kilo kaybı"]', (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Şekersiz Diyet'), (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş'))
ON DUPLICATE KEY UPDATE kan_sekeri_min = VALUES(kan_sekeri_min);

INSERT INTO kullanicilar (tc_kimlik_no, sifre, ad, soyad, dogum_tarihi, cinsiyet, eposta, rol_id)
VALUES ('11111111111', 'doktor123', 'Dr. Ahmet', 'Yılmaz', '1980-05-10', 'Erkek', 'ahmet.yilmaz@ornek.com', (SELECT rol_id FROM kullanici_rolleri WHERE rol_adi = 'Doktor'))
ON DUPLICATE KEY UPDATE ad = VALUES(ad), sifre = VALUES(sifre);

INSERT INTO doktorlar (kullanici_id, uzmanlik_alani, diploma_no, calisma_saatleri)
SELECT kullanici_id, 'Endokrinoloji', 'DIP123456', JSON_OBJECT('Pzt', '09:00-17:00', 'Salı', '09:00-17:00')
FROM kullanicilar
WHERE tc_kimlik_no = '11111111111'
ON DUPLICATE KEY UPDATE uzmanlik_alani = VALUES(uzmanlik_alani);

INSERT INTO kullanicilar (tc_kimlik_no, sifre, ad, soyad, dogum_tarihi, cinsiyet, eposta, rol_id)
VALUES ('22222222222', 'hasta123', 'Mehmet', 'Demir', '1990-09-25', 'Erkek', 'mehmet.demir@ornek.com', (SELECT rol_id FROM kullanici_rolleri WHERE rol_adi = 'Hasta'))
ON DUPLICATE KEY UPDATE ad = VALUES(ad), sifre = VALUES(sifre);

INSERT INTO hastalar (kullanici_id, doktor_id, tani_tarihi, diyabet_tipi)
SELECT
    h.kullanici_id,
    (SELECT doktor_id FROM doktorlar d JOIN kullanicilar k ON d.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '11111111111'),
    '2024-01-15',
    'Tip 2'
FROM kullanicilar h
WHERE h.tc_kimlik_no = '22222222222'
ON DUPLICATE KEY UPDATE diyabet_tipi = VALUES(diyabet_tipi);

INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar)
VALUES (
    (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
    (SELECT belirti_id FROM belirtiler WHERE belirti_adi = 'Yorgunluk'),
    CURDATE(),
    'Orta',
    'Bugün biraz daha yorgun hissediyor.'
)
ON DUPLICATE KEY UPDATE siddet_seviyesi = VALUES(siddet_seviyesi);

INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar)
VALUES (
    (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
    (SELECT belirti_id FROM belirtiler WHERE belirti_adi = 'Polifaji'),
    CURDATE() - INTERVAL 1 DAY,
    'Hafif',
    'Dün akşam hafif açlık hissi vardı.'
)
ON DUPLICATE KEY UPDATE siddet_seviyesi = VALUES(siddet_seviyesi);

INSERT INTO diyet_planlari (hasta_id, doktor_id, diyet_turu_id, baslangic_tarihi, aktif_durum)
SELECT
    (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
    (SELECT doktor_id FROM doktorlar d JOIN kullanicilar k ON d.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '11111111111'),
    (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Az Şekerli Diyet'),
    CURDATE() - INTERVAL 7 DAY,
    TRUE
ON DUPLICATE KEY UPDATE aktif_durum = VALUES(aktif_durum);

INSERT INTO egzersiz_planlari (hasta_id, doktor_id, egzersiz_turu_id, baslangic_tarihi, aktif_durum)
SELECT
    (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
    (SELECT doktor_id FROM doktorlar d JOIN kullanicilar k ON d.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '11111111111'),
    (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş'),
    CURDATE() - INTERVAL 7 DAY,
    TRUE
ON DUPLICATE KEY UPDATE aktif_durum = VALUES(aktif_durum);