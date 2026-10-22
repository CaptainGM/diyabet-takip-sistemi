"""Hasta — bildirim merkezi."""

from __future__ import annotations

import datetime
import tkinter as tk

from .... import state, theme
from ....db import patients as patients_db
from ... import icons
from ..base import Page, badge, card, empty, kv, metric, section, segmented, stat_grid, table


class NotificationsPage(Page):
    title = "Bildirimler"
    subtitle = "Ölçüm uyarıları ve sistem mesajlarını okuyun; okunmamışları tek tıkla kapatın."
    icon = "bell"
    accent = theme.AMBER

    def __init__(self, parent, app, tab: str = "all") -> None:
        self.initial_tab = tab
        self.active_tab = tab
        super().__init__(parent, app)

    def build(self) -> None:
        self.rows = []
        self.selected = None
        self.page_head(actions=(theme.button(self, "Tümünü Okundu İşaretle", self._mark_all, style="ghost"),))
        rows = patients_db.notifications_for_user(state.session.user_id, limit=200)
        unread = sum(1 for r in rows if not r["okundu"])
        today = sum(1 for r in rows if r["olusturma_tarihi"] == datetime.date.today())
        stats = tk.Frame(self.body, bg=theme.APP_BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            metric(stats, icon="bell", title="Okunmamış", value=unread, accent=theme.AMBER, note="Yeni mesaj"),
            metric(stats, icon="mail", title="Toplam", value=len(rows), accent=theme.CYAN, note="Tüm bildirim"),
            metric(stats, icon="calendar", title="Bugün", value=today, accent=theme.PRIMARY, note="Gelen mesaj"),
            metric(stats, icon="check", title="Okunan", value=len(rows) - unread, accent=theme.GREEN, note="Arşiv"),
        ]
        stat_grid(stats, cards, columns=4)
        bar, _ = segmented(
            self.body,
            (("all", "Tümü"), ("unread", "Okunmamış")),
            active=self.initial_tab,
            command=self._switch,
        )
        bar.pack(anchor="w", pady=(0, 10))
        self.content = tk.Frame(self.body, bg=theme.APP_BG)
        self.content.pack(fill="both", expand=True)
        self._build_content()

    def _switch(self, key: str) -> None:
        self.active_tab = key
        self._build_content()

    def _build_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        self.rows = patients_db.notifications_for_user(state.session.user_id, limit=200)
        rows = [r for r in self.rows if self.active_tab == "all" or not r["okundu"]]
        left = card(self.content, padx=0, pady=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        head = tk.Frame(left.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Bildirim Akışı", f"{len(rows)} kayıt", icon="bell", accent=theme.AMBER)
        self.tree, wrap = table(
            left.body,
            ("durum", "tarih", "tip", "baslik", "mesaj"),
            ("Durum", "Tarih", "Tip", "Başlık", "Mesaj"),
            (90, 150, 90, 220, 440), height=15,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.tag_configure("unread", background=theme.WARNING_BG)
        self.tree.tag_configure("read", background=theme.READ_BG)
        self.map = {}
        for row in rows:
            iid = str(row["bildirim_id"])
            self.map[iid] = row
            message = row["mesaj"] or ""
            preview = message if len(message) <= 58 else message[:55].rstrip() + "…"
            self.tree.insert("", "end", iid=iid, tags=("read",) if row["okundu"] else ("unread",), values=(
                "Okundu" if row["okundu"] else "Yeni",
                row["zamani"].strftime("%d.%m.%Y %H:%M") if row["zamani"] else "—",
                row["bildirim_tipi"] or "Bilgi", row["baslik"], preview,
            ))
        if not rows:
            empty(left.body, "Bu filtrede bildirim yok.", icon="bell").pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_detail())
        self.detail = card(self.content, padx=16, pady=14, accent=theme.AMBER)
        self.detail.pack(side="left", fill="both", padx=(6, 0))
        self.detail.configure(width=360)
        self.detail.pack_propagate(False)
        self.detail_body = tk.Frame(self.detail.body, bg=theme.CARD_BG)
        self.detail_body.pack(fill="both", expand=True)
        self.selected = None
        first = self.tree.get_children()
        if first:
            self.tree.selection_set(first[0])
            self.tree.focus(first[0])
            self.selected = self.map.get(first[0])
        self._render_detail()

    def _show_detail(self) -> None:
        self.selected = self.map.get(self.tree.focus())
        self._render_detail()

    def _render_detail(self) -> None:
        for widget in self.detail_body.winfo_children():
            widget.destroy()
        if not self.selected:
            empty(self.detail_body, "Bir bildirim seçin.", icon="bell").pack(fill="both", expand=True)
            return
        row = self.selected
        icons.badge(self.detail_body, "mail", theme.AMBER, size=48, bg=theme.CARD_BG).pack(anchor="w")
        tk.Label(self.detail_body, text=row["baslik"], font=theme.font(14, True), bg=theme.CARD_BG,
                 fg=theme.TEXT, anchor="w", wraplength=320, justify="left").pack(anchor="w", pady=(10, 4))
        badge(self.detail_body, row["bildirim_tipi"] or "Bilgi", theme.CYAN).pack(anchor="w")
        tk.Label(self.detail_body, text=row["mesaj"], font=theme.font(9), bg=theme.CARD_BG,
                 fg=theme.MUTED, anchor="w", wraplength=320, justify="left").pack(anchor="w", pady=(10, 12))
        kv(self.detail_body, "Tarih", row["zamani"].strftime("%d.%m.%Y %H:%M") if row["zamani"] else "—").pack(fill="x", pady=2)
        kv(self.detail_body, "Durum", "Okundu" if row["okundu"] else "Okunmadı").pack(fill="x", pady=2)
        if not row["okundu"]:
            theme.button(self.detail_body, "Okundu İşaretle", self._mark_one, style="success").pack(
                fill="x", pady=(16, 0)
            )

    def _mark_one(self) -> None:
        if self.selected:
            patients_db.mark_notification_read(self.selected["bildirim_id"], state.session.user_id)
            self._build_content()

    def _mark_all(self) -> None:
        for row in patients_db.notifications_for_user(state.session.user_id, limit=500):
            if not row["okundu"]:
                patients_db.mark_notification_read(row["bildirim_id"], state.session.user_id)
        self._build_content()

    def refresh(self) -> None:
        self._build_content()
