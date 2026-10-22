"""Doktor — hasta uyarıları ve kritik hastalar."""

from __future__ import annotations

import datetime
import tkinter as tk

from .... import state, theme
from ....db import doctors as doctors_db
from ... import icons
from ..base import Page, badge, card, empty, kv, metric, section, segmented, stat_grid, table
from ._common import _date, _value_text


class AlertsPage(Page):
    title = "Uyarılar"
    subtitle = "Kritik ölçümleri ve hasta bildirimlerini tek yerden yönetin."
    icon = "alert"
    accent = theme.BLOOD

    def __init__(self, parent, app, tab: str = "alerts") -> None:
        self.initial_tab = tab
        self.active_tab = tab
        super().__init__(parent, app)

    def build(self) -> None:
        self.alerts = []
        self.selected_alert = None
        self.selected_critical = None
        self.page_head(
            actions=(theme.button(self, "Yenile", self.refresh, style="ghost"),)
        )
        all_alerts = doctors_db.patient_alerts_for_doctor(state.session.doctor_id, limit=200)
        critical = doctors_db.critical_patients_for_doctor(state.session.doctor_id)
        unread = sum(1 for a in all_alerts if not a["okundu"])
        today = datetime.date.today()
        today_count = sum(1 for a in all_alerts if a["uyari_tarihi"] == today)
        recent_critical = sum(
            1
            for a in all_alerts
            if a["aciliyet_seviyesi"] == "Kritik"
            and a["uyari_tarihi"] >= today - datetime.timedelta(days=30)
        )
        stats = tk.Frame(self.body, bg=theme.APP_BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            metric(stats, icon="bell", title="Okunmamış", value=unread,
                   accent=theme.AMBER, note="İşlem bekliyor"),
            metric(stats, icon="alert", title="Kritik Uyarı",
                   value=recent_critical,
                   accent=theme.BLOOD, note="Son 30 gün"),
            metric(stats, icon="users", title="Riskli Hasta", value=len(critical),
                   accent=theme.PURPLE, note="Kritik hasta listesi"),
            metric(stats, icon="calendar", title="Bugün", value=today_count,
                   accent=theme.CYAN, note="Yeni uyarı"),
        ]
        stat_grid(stats, cards, columns=4)

        bar, _labels = segmented(
            self.body,
            (("alerts", "Hasta Uyarıları"), ("critical", "Kritik Hastalar")),
            active=self.initial_tab,
            command=self._switch_tab,
        )
        bar.pack(anchor="w", pady=(0, 10))
        self.content = tk.Frame(self.body, bg=theme.APP_BG)
        self.content.pack(fill="both", expand=True)
        self._build_content()

    def _switch_tab(self, key: str) -> None:
        self.active_tab = key
        self._build_content()

    def _build_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        if self.active_tab == "critical":
            self._build_critical()
        else:
            self._build_alerts()

    def _build_alerts(self) -> None:
        self.alerts = doctors_db.patient_alerts_for_doctor(state.session.doctor_id, limit=200)
        left = card(self.content, padx=0, pady=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        head = tk.Frame(left.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Uyarı Akışı", f"{len(self.alerts)} kayıt · aciliyet sırasına göre",
                icon="alert", accent=theme.BLOOD)
        self.alert_tree, wrap = table(
            left.body,
            ("hasta", "uyari", "seviye", "deger", "tarih", "durum"),
            ("Hasta", "Uyarı", "Aciliyet", "Değer", "Tarih", "Durum"),
            (190, 270, 95, 110, 100, 100), height=15,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.alert_tree.tag_configure("Kritik", background=theme.CRITICAL_BG)
        self.alert_tree.tag_configure("Yüksek", background=theme.WARNING_BG)
        self.alert_tree.tag_configure("Orta", background=theme.NOTICE_BG)
        self.alert_tree.tag_configure("okundu", background=theme.READ_BG)
        self.alert_map = {}
        for alert in self.alerts:
            iid = str(alert["uyari_id"])
            self.alert_map[iid] = alert
            tags = ("okundu",) if alert["okundu"] else (alert["aciliyet_seviyesi"],)
            self.alert_tree.insert("", "end", iid=iid, tags=tags, values=(
                alert["hasta_adi"], alert["uyari_adi"], alert["aciliyet_seviyesi"],
                _value_text(alert["kan_sekeri_degeri"]), _date(alert["uyari_tarihi"]),
                "Okundu" if alert["okundu"] else "Yeni",
            ))
        if not self.alerts:
            empty(left.body, "Henüz uyarı yok.", icon="bell").pack(fill="both", expand=True)
        self.alert_tree.bind("<<TreeviewSelect>>", lambda _e: self._show_alert())
        self.detail = card(self.content, padx=16, pady=14, accent=theme.BLOOD)
        self.detail.pack(side="left", fill="both", padx=(6, 0))
        self.detail.configure(width=360)
        self.detail.pack_propagate(False)
        self.detail_body = tk.Frame(self.detail.body, bg=theme.CARD_BG)
        self.detail_body.pack(fill="both", expand=True)
        first = self.alert_tree.get_children()
        if first:
            self.alert_tree.selection_set(first[0])
            self.alert_tree.focus(first[0])
            self.selected_alert = self.alert_map.get(first[0])
        self._render_alert_detail()

    def _show_alert(self) -> None:
        selection = self.alert_tree.focus()
        self.selected_alert = self.alert_map.get(selection)
        self._render_alert_detail()

    def _render_alert_detail(self) -> None:
        for widget in self.detail_body.winfo_children():
            widget.destroy()
        if not self.selected_alert:
            empty(self.detail_body, "Bir uyarı seçin.", icon="alert").pack(fill="both", expand=True)
            return
        a = self.selected_alert
        icons.badge(self.detail_body, "alert", theme.BLOOD, size=48, bg=theme.CARD_BG).pack(anchor="w")
        tk.Label(self.detail_body, text=a["uyari_adi"], font=theme.font(14, True),
                 bg=theme.CARD_BG, fg=theme.TEXT, anchor="w", wraplength=320,
                 justify="left").pack(anchor="w", pady=(10, 4))
        badge(self.detail_body, a["aciliyet_seviyesi"], theme.BLOOD if a["aciliyet_seviyesi"] == "Kritik" else theme.AMBER).pack(anchor="w")
        tk.Label(self.detail_body, text=a["hasta_adi"], font=theme.font(9, True),
                 bg=theme.CARD_BG, fg=theme.CYAN, anchor="w").pack(anchor="w", pady=(12, 0))
        tk.Label(self.detail_body, text=a["uyari_mesaji"], font=theme.font(9),
                 bg=theme.CARD_BG, fg=theme.MUTED, anchor="w", wraplength=320,
                 justify="left").pack(anchor="w", pady=(6, 12))
        for label, value in (
            ("Kan şekeri", _value_text(a["kan_sekeri_degeri"])),
            ("Tarih", _date(a["uyari_tarihi"])),
            ("Durum", "Okundu" if a["okundu"] else "Okunmadı"),
        ):
            kv(self.detail_body, label, value).pack(fill="x", pady=2)
        actions = tk.Frame(self.detail_body, bg=theme.CARD_BG)
        actions.pack(fill="x", pady=(16, 0))
        if not a["okundu"]:
            theme.button(actions, "Okundu İşaretle", self._mark_read, style="success").pack(fill="x")
        theme.button(
            actions, "Hasta Detayı",
            lambda: self.app.navigate("patient_detail", patient_id=str(a.get("hasta_id") or ""), back="alerts"),
            style="ghost",
        ).pack(fill="x", pady=(6, 0))

    def _mark_read(self) -> None:
        if self.selected_alert:
            doctors_db.mark_alert_read(self.selected_alert["uyari_id"])
            self.refresh()

    def _build_critical(self) -> None:
        rows = doctors_db.critical_patients_for_doctor(state.session.doctor_id)
        outer = card(self.content, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Kritik Hastalar", "Son 7 günün risk kategorileri; satıra çift tıklayın.",
                icon="alert", accent=theme.BLOOD)
        self.critical_map = {str(r["hasta_id"]): r for r in rows}
        tree, wrap = table(
            outer.body,
            ("hasta", "ort", "gun", "uyari", "skor", "kategori"),
            ("Hasta", "7 Gün Ort.", "Ölçüm Günü", "Kritik Uyarı", "Uyum", "Kategori"),
            (220, 130, 110, 110, 100, 250), height=14,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tree.tag_configure("risk", background=theme.CRITICAL_BG)
        tree.tag_configure("warn", background=theme.WARNING_BG)
        for row in rows:
            tree.insert("", "end", iid=str(row["hasta_id"]),
                        tags=("risk" if "Kritik" in row["durum_kategorisi"] else "warn",),
                        values=(
                            row["hasta_adi"], f"{row['son_7_gun_ortalama_kan_sekeri']:.1f} mg/dL",
                            f"{row['son_7_gun_olcum_gun_sayisi']} gün",
                            row["kritik_uyari_sayisi"], f"%{row['son_uyum_skoru']:.0f}",
                            row["durum_kategorisi"],
                        ))
        if not rows:
            empty(outer.body, "Kritik hasta bulunmuyor.", icon="shield").pack(fill="both", expand=True)
        tree.bind("<Double-1>", lambda _e: self._open_critical(tree))

    def _open_critical(self, tree) -> None:
        selection = tree.focus()
        if selection:
            self.app.navigate("patient_detail", patient_id=selection, back="alerts")

    def refresh(self) -> None:
        self.app.navigate("alerts", tab=self.active_tab)

