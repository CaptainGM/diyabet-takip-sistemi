"""Hasta — insülin önerileri (tarih filtreli) ve bildirimler ekranı."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import tkcalendar

from ... import state, theme
from ...db import patients as patients_db
from ...db import records as records_db
from .. import helpers


def show_insulin_recommendations_for_patient_filtered() -> None:
    win = helpers.modal_window(None, "İnsülin Önerilerim (Filtreli)", "880x620")
    helpers.header(
        win,
        "💉 İnsülin Önerilerim (Ölçüm Tipi & Tarih Aralığına Göre)",
        "Öneriler öğün ortalamalarına göre otomatik hesaplanır",
    )

    card_filters = theme.frame(win, card=True)
    card_filters.pack(fill="x", padx=16, pady=(0, 10))
    form = theme.frame(card_filters)
    form.pack(padx=12, pady=10)

    tip_var = tk.StringVar(value="Tümü")
    tip_menu, _ = helpers.dropdown(form, ("Tümü", "Sabah", "Öğle", "İkindi", "Akşam", "Gece"), width=12)
    helpers.form_row(form, 0, "Ölçüm Tipi:", tip_menu)

    # form_row grid kullandığı için filtreleri yan yana değil alta alıyoruz;
    # sade ve hizalı kalması için ayrı satırlar:
    bas_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    bas_entry.set_date(datetime.date.today() - datetime.timedelta(days=7))
    helpers.form_row(form, 1, "Başlangıç Tarihi:", bas_entry)
    bit_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 2, "Bitiş Tarihi:", bit_entry)

    card_list = theme.frame(win, card=True)
    card_list.pack(fill="both", expand=True, padx=16, pady=(0, 10))
    tree = ttk.Treeview(
        card_list,
        columns=("tarih", "tip", "ortalama", "doz", "uygulandi"),
        show="headings",
        height=11,
        style="Card.Treeview",
    )
    for key, text, width in (
        ("tarih", "Tarih", 110),
        ("tip", "Ölçüm Tipi", 110),
        ("ortalama", "Ortalama KŞ", 130),
        ("doz", "Önerilen Doz", 130),
        ("uygulandi", "Uygulandı mı", 120),
    ):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card_list, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    tree.tag_configure("uygulandi", background=theme.READ_BG, foreground=theme.MUTED)
    tree.tag_configure("bekliyor", background="#e9f4f6")

    recs: dict[str, dict] = {}

    def refresh() -> None:
        start = bas_entry.get_date()
        end = bit_entry.get_date()
        if end < start:
            messagebox.showerror("Hata", "Bitiş tarihi başlangıçtan önce olamaz.", parent=win)
            return
        rows = records_db.insulin_history(
            state.session.patient_id, start=start, end=end, limit=200
        )
        selected_tip = tip_var.get()
        if selected_tip != "Tümü":
            rows = [r for r in rows if r["olcum_tipi"] == selected_tip]
        recs.clear()
        tree.delete(*tree.get_children())
        for row in rows:
            iid = str(row["oneri_id"])
            recs[iid] = row
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=("uygulandi" if row["uygulandi"] else "bekliyor",),
                values=(
                    helpers.date_label(row["tarih"]),
                    row["olcum_tipi"],
                    f"{row['ortalama_kan_sekeri']:g} mg/dL",
                    f"{row['onerilen_doz_ml']:g} ml",
                    "Evet" if row["uygulandi"] else "Hayır",
                ),
            )
        if not rows:
            theme.muted_label(card_list, "Aradığınız kriterlere uygun öneri yok.", 10).pack(pady=8)

    def mark_applied() -> None:
        selection = tree.focus()
        if not selection:
            messagebox.showinfo("Bilgi", "Önce bir öneri seçin.", parent=win)
            return
        ok = patients_db.mark_insulin_applied(
            recs[selection]["oneri_id"], state.session.patient_id
        )
        if ok:
            messagebox.showinfo("Başarılı", "Doz uygulandı olarak işaretlendi!", parent=win)
            refresh()
        else:
            messagebox.showerror("Hata", "İşaretlenemedi.", parent=win)

    tip_menu["menu"].delete(0, "end")
    for opt in ("Tümü", "Sabah", "Öğle", "İkindi", "Akşam", "Gece"):
        tip_menu["menu"].add_command(
            label=opt, command=lambda o=opt: (tip_var.set(o), refresh())
        )

    bar = theme.frame(win)
    bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(bar, "✓ Uygulandı Olarak İşaretle", mark_applied, style="success").pack(side="left")
    theme.button(bar, "Filtrele", refresh, style="primary").pack(side="left", padx=(8, 0))
    refresh()


# ---------------------------------------------------------------------------
# Bildirimler
# ---------------------------------------------------------------------------
def show_patient_notifications() -> None:
    win = helpers.modal_window(None, "Bildirimlerim", "760x560")
    helpers.header(win, "🔔 Bildirimlerim", "Ölçüm uyarıları ve sistem bildirimleri")

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=16, pady=(0, 10))
    tree = ttk.Treeview(
        card,
        columns=("durum", "tarih", "tip", "baslik", "mesaj"),
        show="headings",
        height=12,
        style="Card.Treeview",
    )
    for key, text, width in (
        ("durum", "Durum", 95),
        ("tarih", "Tarih", 115),
        ("tip", "Tip", 80),
        ("baslik", "Başlık", 150),
        ("mesaj", "Mesaj", 300),
    ):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    tree.tag_configure("okunmadı", background=theme.WARNING_BG)
    tree.tag_configure("okundu", background=theme.READ_BG, foreground=theme.MUTED)

    notifications: dict[str, dict] = {}

    def refresh() -> None:
        rows = patients_db.notifications_for_user(state.session.user_id, limit=80)
        notifications.clear()
        tree.delete(*tree.get_children())
        for row in rows:
            iid = str(row["bildirim_id"])
            notifications[iid] = row
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=("okundu" if row["okundu"] else "okunmadı",),
                values=(
                    "✓ Okundu" if row["okundu"] else "● Yeni",
                    helpers.datetime_label(row["zamani"]),
                    row["bildirim_tipi"] or "Bilgi",
                    row["baslik"],
                    row["mesaj"],
                ),
            )
        for widget in card.winfo_children():
            if isinstance(widget, tk.Label):
                widget.destroy()
        if not rows:
            theme.muted_label(card, "Bildirim yok. 🎉", 10).pack(pady=8)

    def mark_read() -> None:
        selection = tree.focus()
        if not selection:
            messagebox.showinfo("Bilgi", "Önce bir bildirim seçin.", parent=win)
            return
        patients_db.mark_notification_read(
            notifications[selection]["bildirim_id"], state.session.user_id
        )
        refresh()

    def mark_all() -> None:
        for row in patients_db.notifications_for_user(state.session.user_id, limit=200):
            if not row["okundu"]:
                patients_db.mark_notification_read(
                    row["bildirim_id"], state.session.user_id
                )
        refresh()

    def show_detail(_event=None) -> None:
        selection = tree.focus()
        if not selection:
            return
        row = notifications[selection]
        messagebox.showinfo(
            f"{row['bildirim_tipi']} — {row['baslik']}", row["mesaj"], parent=win
        )

    tree.bind("<Double-1>", show_detail)

    bar = theme.frame(win)
    bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(bar, "✓ Okundu İşaretle", mark_read, style="success").pack(side="left")
    theme.button(bar, "Tümünü Okundu İşaretle", mark_all, style="ghost").pack(
        side="left", padx=(8, 0)
    )
    theme.button(bar, "Yenile", refresh, style="neutral").pack(side="right")
    refresh()
