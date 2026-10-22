"""README ekran görüntülerini tek pencere arayüzünden üretir.

Kullanım::

    pip install -r requirements-dev.txt
    python scripts/capture_screens.py                 # docs/screenshots/ içine
    python scripts/capture_screens.py --out DIR       # başka bir klasöre

Görüntüler yalnızca mevcut demo verisiyle alınır; veritabanına yazılmaz.
"""

from __future__ import annotations

import argparse
import sys
import time
import tkinter as tk
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import ImageGrab

from diyabet_takip import state, theme
from diyabet_takip.db import bootstrap as B
from diyabet_takip.db.client import get_db
from diyabet_takip.ui import app, main_menu
from diyabet_takip.ui.login_screen import show_login_screen

OUT = ROOT / "docs" / "screenshots"  # --out ile değiştirilebilir


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)


def find_label(widget, text: str) -> tk.Label | None:
    for item in walk(widget):
        if isinstance(item, tk.Label) and str(item.cget("text")) == text:
            return item
    return None


def _pin_geometry(root: tk.Tk, width: int = 1920, height: int = 1080) -> None:
    """Kabuk ekranlarının pencere boyutunu ve konumunu sabitler.

    Boyut tam 1080p: ekran görüntüleri her zaman aynı, tutarlı çözünürlükte
    çıkar. ``-topmost`` KULLANILMAZ; pencere sistem genelinde önplana
    atılmaz (ör. başka bir monitörde oynanan bir oyunu bölmez). Pencere,
    birincil monitörün sol-üst köşesine konur — ikincil bir monitöre
    taşımak denendi, ancak bu ortamda (sanal/uzak ekran) ``ImageGrab``
    bazı karelerde pencerenin bir köşesini boş yakalıyordu; birincil
    monitörde bu sorun hiç görülmedi. Bazı çok ekranlı / sanal ekranlı
    kurulumlarda ``winfo_screenwidth/height`` aynı betik çalışması
    içinde bile farklı sonuçlar dönebilir; bu yüzden geometri, ölçüm
    hedefle eşleşene kadar tekrar tekrar uygulanır.
    """
    for _attempt in range(6):
        root.geometry(f"{width}x{height}+20+20")
        for _ in range(10):
            root.update_idletasks()
            root.update()
            time.sleep(0.02)
        if (root.winfo_width(), root.winfo_height()) == (width, height):
            return
        time.sleep(0.15)  # bir sonraki denemeden önce dış etken yatışsın


def snap(root: tk.Tk, name: str) -> None:
    """Pencere çizilsin, sonra yalnızca istemci alanını kaydet.

    Bazı çok ekranlı / DPI ölçekli kurulumlarda ``winfo_width/height`` birkaç
    kare boyunca kararsız olabilir (pencere geometrisi tam oturmadan önce
    ölçüm alınırsa görüntünün altında boş/beyaz bir şerit kalabilir). Ölçüm,
    art arda iki karede aynı sonucu verene kadar tekrarlanır.
    """
    root.lift()  # yalnızca kendi katmanında öne gelir; sistem genelinde önplana atmaz
    last_size: tuple[int, int] | None = None
    for _ in range(80):
        root.update_idletasks()
        root.update()
        time.sleep(0.025)
        size = (root.winfo_width(), root.winfo_height())
        if size == last_size:
            break
        last_size = size
    image = ImageGrab.grab(window=root.winfo_id())
    expected = (root.winfo_width(), root.winfo_height())
    if image.size != expected:  # bazı Windows sürümlerinde başlık çubuğu eklenir
        image = image.crop((0, 0, expected[0], expected[1]))
    image.save(OUT / name)
    print(f"{name}  {image.size[0]}x{image.size[1]}")


def set_session(db, role: str) -> None:
    state.session.reset()
    user = db[B.USERS].find_one({"rol": role})
    if user is None:
        raise RuntimeError("Demo kullanıcılar bulunamadı; önce demo-veri.bat çalıştırın.")
    state.session.user_id = user["_id"]
    state.session.user_ad = user["ad"]
    state.session.user_soyad = user["soyad"]
    state.session.user_role = role
    if role == "Doktor":
        profile = db[B.DOCTOR_PROFILES].find_one({"user_id": user["_id"]})
        state.session.doctor_id = profile["_id"]
        state.session.patient_id = None
    else:
        profile = db[B.PATIENT_PROFILES].find_one({"user_id": user["_id"]})
        state.session.patient_id = profile["_id"]
        state.session.doctor_id = None


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description="README ekran görüntüleri")
    parser.add_argument("--out", type=Path, default=OUT, help="çıktı klasörü")
    OUT = parser.parse_args().out
    app._enable_high_dpi()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()

    db = get_db()
    if db is None:
        raise SystemExit("MongoDB bağlantısı kurulamadı.")

    root = tk.Tk()
    theme.apply_theme(root)
    app.apply_app_icon(root)
    state.session.window = root
    root.deiconify()

    # --- Giriş ve kayıt -----------------------------------------------------
    # Not: giriş ekranı kendi boyutunu/konumunu ayarlar (_pin_geometry
    # kullanılmaz). Bu pencereyi başka bir monitöre taşımak dene(n)di, ancak
    # ImageGrab bazı karelerde üst kısmı boş/beyaz yakalıyordu (muhtemelen bu
    # sanal/uzak masaüstü kurulumuna özgü bir kırpma hatası); mevcut hâliyle
    # bu iki görüntü sorunsuz çıktığı için dokunulmadı.
    show_login_screen(lambda: None)
    root.update()
    snap(root, "01-giris-ekrani.png")

    show_login_screen(lambda: None, start_tab="register")
    root.update()
    snap(root, "02-kayit-ekrani.png")

    # --- Doktor panelleri ---------------------------------------------------
    set_session(db, "Doktor")
    main_menu.show_main_app_screen()
    _pin_geometry(root)
    snap(root, "03-doktor-dashboard.png")

    patient = db[B.PATIENT_PROFILES].find_one({"doktor_id": state.session.doctor_id})
    if patient is None:
        raise SystemExit("Doktorun hastası bulunamadı.")
    patient_id = str(patient["_id"])

    pages = [
        ("patients", "04-hastalarim.png", {}),
        ("patient_detail", "05-hasta-detayi.png", {"patient_id": patient_id}),
        ("alerts", "06-hasta-uyarilari.png", {}),
        ("critical", "06b-kritik-hastalar.png", {}),
        ("appointments", "07-randevular.png", {}),
        ("reports", "08-raporlar.png", {"patient_id": patient_id}),
        ("plans", "09-plan-belirti.png", {}),
        ("add_patient", "10-hasta-ekle.png", {}),
        ("profile", "11-doktor-profil.png", {}),
    ]
    for key, name, kwargs in pages:
        root._app_router.navigate(key, **kwargs)
        _pin_geometry(root)
        snap(root, name)

    # --- Hasta panelleri ----------------------------------------------------
    set_session(db, "Hasta")
    main_menu.show_main_app_screen()
    _pin_geometry(root)
    snap(root, "12-hasta-dashboard.png")

    patient_pages = [
        ("measure", "13-olcum-gir.png"),
        ("history", "14-gecmis-grafik.png"),
        ("compliance", "15-uyum-takibi.png"),
        ("insulin", "16-insulin.png"),
        ("notifications", "17-bildirimler.png"),
        ("patient_plans", "18-planlarim.png"),
        ("patient_appointments", "19-randevularim.png"),
        ("profile", "20-hasta-profil.png"),
    ]
    for key, name in patient_pages:
        root._app_router.navigate(key)
        _pin_geometry(root)
        snap(root, name)

    root.destroy()
    print(f"\n{len(list(OUT.glob('*.png')))} görüntü hazır: {OUT}")


if __name__ == "__main__":
    main()
