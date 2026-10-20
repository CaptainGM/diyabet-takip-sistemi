"""Doktor — hasta uyarıları ve kritik hastalar ekranları."""

from __future__ import annotations

from tkinter import messagebox, ttk

from ... import state, theme
from ...db import doctors as doctors_db
from .. import helpers
from .patients import show_patient_detail_window

ROW_COLORS = {
    "Kritik": theme.CRITICAL_BG,
    "Yüksek": theme.WARNING_BG,
    "Orta": theme.NOTICE_BG,
}


def show_doctor_alerts() -> None:
    win = helpers.modal_window(None, "Hasta Uyarıları", "900x600")
    helpers.header(
        win, "🚨 Hasta Uyarıları", "Okunmamış ve aciliyet sırasına göre listelenir"
    )

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    tree = ttk.Treeview(
        card,
        columns=("once", "hasta", "uyari", "seviye", "kan_sekeri", "tarih"),
        show="headings",
        height=14,
        style="Card.Treeview",
    )
    headings = (
        ("once", "Durum", 90),
        ("hasta", "Hasta", 170),
        ("uyari", "Uyarı / Mesaj", 300),
        ("seviye", "Aciliyet", 80),
        ("kan_sekeri", "Kan Şekeri", 100),
        ("tarih", "Tarih", 90),
    )
    for key, text, width in headings:
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    for seviye, renk in ROW_COLORS.items():
        tree.tag_configure(seviye, background=renk)
    tree.tag_configure("okundu", background=theme.READ_BG, foreground=theme.MUTED)

    alert_ids: dict[str, object] = {}

    def refresh() -> None:
        alerts = doctors_db.patient_alerts_for_doctor(state.session.doctor_id)
        alert_ids.clear()
        tree.delete(*tree.get_children())
        for alert in alerts:
            iid = str(alert["uyari_id"])
            alert_ids[iid] = alert["uyari_id"]
            durum = "✓ Okundu" if alert["okundu"] else "● Okunmadı"
            deger = (
                f"{alert['kan_sekeri_degeri']:g} mg/dL"
                if alert["kan_sekeri_degeri"] is not None
                else "—"
            )
            tags = ("okundu",) if alert["okundu"] else (alert["aciliyet_seviyesi"],)
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=tags,
                values=(durum, alert["hasta_adi"], alert["uyari_adi"], alert["aciliyet_seviyesi"], deger, helpers.date_label(alert["uyari_tarihi"])),
            )

    def mark_read() -> None:
        selection = tree.focus()
        if not selection:
            messagebox.showinfo("Bilgi", "Önce bir uyarı seçin.", parent=win)
            return
        doctors_db.mark_alert_read(alert_ids[selection])
        refresh()

    # --- Mesaj kutusu --------------------------------------------------------
    def show_message() -> None:
        selection = tree.focus()
        if not selection:
            return
        alerts = doctors_db.patient_alerts_for_doctor(
            state.session.doctor_id, limit=200
        )
        current = next((a for a in alerts if str(a["uyari_id"]) == selection), None)
        if current:
            messagebox.showinfo(
                f"{current['uyari_adi']} ({current['aciliyet_seviyesi']})",
                f"Hasta: {current['hasta_adi']}\n\n{current['uyari_mesaji']}",
                parent=win,
            )

    tree.bind("<Double-1>", lambda e: show_message())

    button_bar = theme.frame(win)
    button_bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(button_bar, "✓ Okundu Olarak İşaretle", mark_read, style="success").pack(
        side="left"
    )
    theme.button(button_bar, "Detayı Göster", show_message, style="ghost").pack(
        side="left", padx=(8, 0)
    )
    theme.button(button_bar, "Yenile", refresh, style="neutral").pack(
        side="right"
    )
    refresh()


def show_critical_patients() -> None:
    win = helpers.modal_window(None, "Kritik Hastalar", "860x540")
    helpers.header(win, "🩹 Kritik Hastalar", "Son 7 güne göre otomatik risk kategorileri")

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    tree = ttk.Treeview(
        card,
        columns=("hasta", "ort", "gun", "uyari", "skor", "kategori"),
        show="headings",
        height=11,
        style="Card.Treeview",
    )
    headings = (
        ("hasta", "Hasta", 180),
        ("ort", "7 Günlük Ortalama KŞ", 160),
        ("gun", "Ölçüm Günü", 100),
        ("uyari", "Kritik Uyarı", 90),
        ("skor", "Son Uyum Skoru", 110),
        ("kategori", "Kategori", 170),
    )
    for key, text, width in headings:
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    tree.tag_configure("Kritik Durum (Kan Şekeri)", background=theme.CRITICAL_BG)
    tree.tag_configure("Ölçüm Eksikliği", background=theme.WARNING_BG)
    tree.tag_configure("Düşük Uyum", background=theme.NOTICE_BG)
    tree.tag_configure("Kritik Uyarı Var", background=theme.NOTICE_BG)

    patients: dict[str, dict] = {}

    def refresh() -> None:
        rows = doctors_db.critical_patients_for_doctor(state.session.doctor_id)
        patients.clear()
        tree.delete(*tree.get_children())
        for row in rows:
            iid = str(row["hasta_id"])
            patients[iid] = row
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=(row["durum_kategorisi"],),
                values=(
                    row["hasta_adi"],
                    f"{row['son_7_gun_ortalama_kan_sekeri']:g} mg/dL",
                    f"{row['son_7_gun_olcum_gun_sayisi']}/7",
                    row["kritik_uyari_sayisi"],
                    f"%{row['son_uyum_skoru']:g}",
                    row["durum_kategorisi"],
                ),
            )
        if not rows:
            theme.muted_label(card, "Kritik kategoride hasta yok. 🎉", 10).pack(pady=10)

    def open_detail() -> None:
        selection = tree.focus()
        if not selection:
            messagebox.showinfo("Bilgi", "Önce bir hasta seçin.", parent=win)
            return
        row = patients[selection]
        show_patient_detail_window(
            {"hasta_id": row["hasta_id"], "ad": row["hasta_adi"].split(" ")[0], "soyad": " ".join(row["hasta_adi"].split(" ")[1:])}
        )

    button_bar = theme.frame(win)
    button_bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(button_bar, "Hasta Detayını Aç", open_detail, style="primary").pack(side="left")
    theme.button(button_bar, "Yenile", refresh, style="neutral").pack(side="right")
    refresh()
