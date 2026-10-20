"""Doktor — hasta raporu üretimi ve randevu yönetimi (v2'de eklenen özellik)."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import tkcalendar

from ... import state, theme
from ...db import doctors as doctors_db
from ...db.client import get_db
from ...services import report_service
from .. import helpers


# ---------------------------------------------------------------------------
# Hasta raporu
# ---------------------------------------------------------------------------
def show_patient_report_options() -> None:
    patient, _ = _select_patient_dialog("Hasta Raporu Oluştur")
    if not patient:
        return
    _report_window(patient)


def _select_patient_dialog(title: str):
    """T.C. girişi ile hasta seçimi; başarılıysa hasta dicts döner."""
    db = get_db()
    if db is None:
        return None, None
    patients = doctors_db.list_patients_for_doctor(state.session.doctor_id)
    if not patients:
        messagebox.showwarning(title, "Kayıtlı hasta bulunamadı.")
        return None, None

    dialog = helpers.modal_window(None, title, "460x260")
    helpers.header(dialog, title, "Raporu oluşturulacak hastayı seçin")

    card = theme.frame(dialog, card=True)
    card.pack(fill="x", padx=18, pady=(0, 12))
    form = theme.frame(card)
    form.pack(padx=12, pady=12)

    labels = [f"{p['ad']} {p['soyad']} — {p['tc_kimlik_no']}" for p in patients]
    menu, var = helpers.dropdown(form, labels, width=42)
    helpers.form_row(form, 0, "Hasta:", menu)

    chosen: list = []

    def _ok() -> None:
        index = labels.index(var.get())
        chosen.append(patients[index])
        dialog.destroy()

    # Tk variable indekse güvenli erişim: dropdown ilk elemanı gösterir;
    # kullanıcı menüyü açamazsa varsayılan hasta seçilir.
    theme.button(card, "Devam Et", _ok).pack(fill="x", padx=12, pady=(0, 12), ipady=4)
    dialog.grab_set()
    dialog.wait_window()
    return (chosen[-1] if chosen else None), None


def _report_window(patient: dict) -> None:
    win = helpers.modal_window(None, f"Rapor — {patient['ad']} {patient['soyad']}", "820x640")
    helpers.header(
        win,
        "🧾 Hasta Raporu",
        f"{patient['ad']} {patient['soyad']} ({patient['tc_kimlik_no']}) için metin raporu",
    )

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=16, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=12, pady=10)

    bas = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 0, "Rapor Başlangıç Tarihi:", bas)
    bit = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 1, "Rapor Bitiş Tarihi:", bit)
    bit.set_date(datetime.date.today())
    bas.set_date(datetime.date.today() - datetime.timedelta(days=30))

    text = helpers.scrolled_text(win, width=90, height=16)
    text.pack(fill="both", expand=True, padx=16, pady=(0, 6))

    def generate() -> None:
        start = bas.get_date()
        end = bit.get_date()
        if end < start:
            messagebox.showerror("Hata", "Bitiş tarihi başlangıçtan önce olamaz.", parent=win)
            return
        sections = report_service.build_report(patient["hasta_id"], start, end)
        if not sections:
            messagebox.showinfo(
                "Bilgi", "Bu tarihte raporlanacak kayıt bulunamadı.", parent=win
            )
            return

        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("1.0", "DIYABET TAKIP SISTEMI — HASTA RAPORU\n")
        text.insert(
            "end",
            f"Rapor Tarihi: {datetime.date.today().strftime('%d.%m.%Y')}\n",
        )
        text.insert("end", "-" * 70 + "\n\n")
        for section in sections:
            text.insert("end", f"■ {section['bolum']}\n")
            for key, value in section["veri"].items():
                text.insert("end", f"    {key}: {value}\n")
            text.insert("end", "\n")
        text.configure(state="disabled")

    def save_txt() -> None:
        content = text.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Bilgi", "Önce bir rapor oluşturun.", parent=win)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Metin Dosyası", "*.txt")],
            initialfile=f"rapor_{patient['tc_kimlik_no']}.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            messagebox.showinfo("Başarı", f"Rapor kaydedildi: {path}", parent=win)

    bar = theme.frame(win)
    bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(bar, "Rapor Oluştur", generate, style="primary").pack(side="left")
    theme.button(bar, "💾 Metin Dosyası Olarak Kaydet", save_txt, style="ghost").pack(
        side="left", padx=(8, 0)
    )
    generate()


# ---------------------------------------------------------------------------
# Randevu yönetimi (yeni özellik)
# ---------------------------------------------------------------------------
def show_appointment_management() -> None:
    win = helpers.modal_window(None, "Randevu Yönetimi", "880x680")
    helpers.header(win, "🗓️ Randevu Yönetimi", "Hastalara muayene/kontrol randevusu tanımlayın")

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=16, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=12, pady=10)

    tc_entry = theme.entry(form)
    helpers.form_row(form, 0, "Hasta T.C. Kimlik No:", tc_entry)

    tarih_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 1, "Randevu Tarihi:", tarih_entry)

    saat_entry = theme.entry(form, width=12)
    saat_entry.insert(0, datetime.datetime.now().strftime("%H:%M"))
    helpers.form_row(form, 2, "Randevu Saati (SS:DAK):", saat_entry)

    sure = tk.Spinbox(form, from_=10, to=180, width=10, font=theme.font(10), increment=5)
    sure.delete(0, tk.END)
    sure.insert(0, 30)
    helpers.form_row(form, 3, "Süre (dk):", sure)

    not_entry = theme.entry(form)
    helpers.form_row(form, 4, "Not (hasta görünür):", not_entry)

    def create() -> None:
        saat = saat_entry.get().strip().replace(".", ":")
        try:
            datetime.datetime.strptime(saat, "%H:%M")
        except ValueError:
            messagebox.showerror("Hata", "Saati SS:DD biçiminde girin (örn. 14:30).", parent=win)
            return
        result = doctors_db.create_appointment(
            state.session.doctor_id,
            tc_entry.get().strip(),
            tarih_entry.get_date(),
            saat,
            int(sure.get()),
            not_entry.get().strip(),
        )
        if result["ok"]:
            messagebox.showinfo("Başarı", result["mesaj"], parent=win)
            refresh()
        else:
            messagebox.showerror("Hata", result["mesaj"], parent=win)

    button_line = theme.frame(card)
    button_line.pack(fill="x", padx=14, pady=(2, 12))
    theme.button(button_line, "Randevu Oluştur", create, style="primary").pack(side="left")

    # --- Randevu listesi -------------------------------------------------------
    card_list = theme.frame(win, card=True)
    card_list.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    tree = ttk.Treeview(
        card_list,
        columns=("hasta", "tarih", "saat", "sure", "durum", "not"),
        show="headings",
        height=11,
        style="Card.Treeview",
    )
    headings = (
        ("hasta", "Hasta (T.C.)", 220),
        ("tarih", "Tarih", 100),
        ("saat", "Saat", 70),
        ("sure", "Süre", 60),
        ("durum", "Durum", 110),
        ("not", "Not", 220),
    )
    for key, text, width in headings:
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card_list, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    appointments: dict[str, dict] = {}

    def refresh() -> None:
        rows = doctors_db.appointments_for_doctor(state.session.doctor_id)
        appointments.clear()
        tree.delete(*tree.get_children())
        # satır renk etiketleri (her refresh'te bir kez tanımlanır)
        tree.tag_configure("p", background=theme.WARNING_BG)
        tree.tag_configure("c", background=theme.READ_BG)
        tree.tag_configure("t", background="#e6f4ea")
        for row in rows:
            iid = str(row["randevu_id"])
            appointments[iid] = row
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=("p" if row["durum"] == "Planlandı" else "c" if row["durum"] == "İptal Edildi" else "t",),
                values=(
                    f"{row['hasta_adi']} ({row['hasta_tc']})",
                    helpers.date_label(row["randevu_tarihi"]),
                    row["randevu_saati"],
                    f"{row['sure_dakika']} dk",
                    row["durum"],
                    row["not_metni"] or "—",
                ),
            )
        # boş durum bilgi etiketi
        for widget in card_list.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("Henüz"):
                widget.destroy()
        if not rows:
            theme.muted_label(card_list, "Henüz randevu yok.", 10).pack(pady=8)

    def cancel() -> None:
        selection = tree.focus()
        if not selection:
            messagebox.showinfo("Bilgi", "Önce bir randevu seçin.", parent=win)
            return
        if appointments[selection]["durum"] != "Planlandı":
            messagebox.showinfo("Bilgi", "Sadece 'Planlandı' durumu iptal edilebilir.", parent=win)
            return
        if messagebox.askyesno("Onay", "Bu randevuyu iptal etmek istiyor musunuz?", parent=win):
            doctors_db.cancel_appointment(appointments[selection]["randevu_id"])
            refresh()

    bar = theme.frame(win)
    bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(bar, "🗑️ Seçili Randevuyu İptal Et", cancel, style="danger").pack(side="left")
    theme.button(bar, "Yenile", refresh, style="neutral").pack(side="right")
    refresh()
