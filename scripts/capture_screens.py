"""README için taze ekran görüntülerini üretir.

Kullanım::

    python scripts/capture_screens.py

Görüntüler ``docs/screenshots/*.png`` altına yazılır. Uygulama GUI'si kısa
süreliğine açılır (sadece lokal veritabanı gerektirir).
"""

from __future__ import annotations

import ctypes
import datetime
import pathlib
import sys
import tkinter as tk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    ctypes.windll.user32.SetProcessDPIAware()  # Windows DPI ölçek eşlemesi
except Exception:
    pass

from PIL import ImageGrab

from diyabet_takip import state
from diyabet_takip.db.client import get_db_strict

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def last_modal(root: tk.Tk) -> tk.Wm:
    """En son açılan Toplevel (modal) pencere."""
    widgets = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
    return widgets[-1] if widgets else root


def caption_window(widget: tk.Wm, name: str, settle_ms: int = 400) -> None:
    """Pencereyi öne getirip içeriği doldurduktan sonra PNG'ye kaydeder."""

    def _grab() -> None:
        widget.update_idletasks()
        widget.attributes("-topmost", True)
        widget.update()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        w = widget.winfo_width()
        h = widget.winfo_height()
        bbox = (max(0, x - 1), max(0, y - 30), x + w + 2, y + h + 2)
        ImageGrab.grab(bbox=bbox).save(OUT / name)
        print(f"  ↳ {name} kaydedildi")
        widget.attributes("-topmost", False)

    widget.update_idletasks()
    widget.after(settle_ms, _grab)
    widget.update()
    widget.after(int(settle_ms * 2 + 200))
    widget.update()


def close_all(root: tk.Tk) -> None:
    for child in list(root.winfo_children()):
        try:
            child.grab_release()
        except Exception:
            pass
        child.destroy()
    root.update_idletasks()


def main() -> None:
    print(f"Görüntüler oluşturuluyor: {datetime.date.today().isoformat()}")
    root = tk.Tk()
    root.withdraw()
    state.session.window = root

    from diyabet_takip.db import reference as ref
    from diyabet_takip.ui.doctor.alerts import show_critical_patients, show_doctor_alerts
    from diyabet_takip.ui.doctor.dashboard import show_doctor_dashboard
    from diyabet_takip.ui.doctor.patients import show_patient_detail_window
    from diyabet_takip.ui.doctor.reports import show_appointment_management
    from diyabet_takip.ui.login_screen import show_login_screen
    from diyabet_takip.ui.main_menu import show_main_app_screen
    from diyabet_takip.ui.patient.measurements import (
        enter_blood_sugar,
        show_blood_sugar_history_and_graphs,
    )
    from diyabet_takip.ui.patient.tracking import show_patient_compliance

    root.deiconify()

    # 1) Giriş ekranı
    show_login_screen(lambda: None)
    caption_window(root, "01-giris-ekrani.png")
    close_all(root)

    db = get_db_strict()
    doc_user = db["users"].find_one({"tc_kimlik_no": "11111111111"})
    doc_profile = db["doctor_profiles"].find_one({"user_id": doc_user["_id"]})
    pat_user = db["users"].find_one({"tc_kimlik_no": "22222222222"})
    pat_profile = db["patient_profiles"].find_one({"user_id": pat_user["_id"]})
    patient = ref.find_patient_profile(db, pat_profile["_id"])

    # 2) Hasta ana menü
    _set_patient_session(state, pat_user, pat_profile)
    show_main_app_screen()
    caption_window(root, "02-ana-menu-hasta.png")
    close_all(root)

    # 3) Hasta — ölçüm girme
    enter_blood_sugar()
    caption_window(last_modal(root), "03-olcum-gir.png")
    close_all(root)

    # 4) Hasta — geçmiş + grafik
    show_blood_sugar_history_and_graphs()
    caption_window(last_modal(root), "04-olcum-gecmis-grafik.png")
    close_all(root)

    # 5) Hasta — uyum takibi
    show_patient_compliance()
    caption_window(last_modal(root), "05-uyum-takibi.png")
    close_all(root)

    # 6) Doktor ana menü
    _set_doctor_session(state, doc_user, doc_profile)
    show_main_app_screen()
    caption_window(root, "06-ana-menu-doktor.png")
    close_all(root)

    # 7) Doktor paneli
    show_doctor_dashboard()
    caption_window(last_modal(root), "07-doktor-paneli.png")
    close_all(root)

    # 8) Hasta uyarıları
    show_doctor_alerts()
    caption_window(last_modal(root), "08-hasta-uyarilari.png")
    close_all(root)

    # 9) Kritik hastalar
    show_critical_patients()
    caption_window(last_modal(root), "09-kritik-hastalar.png")
    close_all(root)

    # 10) Randevu yönetimi
    show_appointment_management()
    caption_window(last_modal(root), "10-randevu-yonetimi.png")
    close_all(root)

    # 11) Hasta detayı (sekmeli pencere)
    show_patient_detail_window(patient)
    caption_window(last_modal(root), "11-hasta-detay.png")
    close_all(root)

    root.destroy()
    print("Tamamlandı →", OUT)


def _set_patient_session(state, pat_user: dict, pat_profile: dict) -> None:
    state.session.user_id = pat_user["_id"]
    state.session.user_ad = pat_user["ad"]
    state.session.user_soyad = pat_user["soyad"]
    state.session.user_role = "Hasta"
    state.session.patient_id = pat_profile["_id"]
    state.session.doctor_id = None


def _set_doctor_session(state, doc_user: dict, doc_profile: dict) -> None:
    state.session.user_id = doc_user["_id"]
    state.session.user_ad = doc_user["ad"]
    state.session.user_soyad = doc_user["soyad"]
    state.session.user_role = "Doktor"
    state.session.doctor_id = doc_profile["_id"]
    state.session.patient_id = None


if __name__ == "__main__":
    main()
