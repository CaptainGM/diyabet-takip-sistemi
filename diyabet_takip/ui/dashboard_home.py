"""Role göre ana dashboard içeriği.

Doktor: hasta metrikleri, kan şekeri trendi, son ölçümler, hasta durumu,
dağılım ve hızlı işlemler. Hasta: kendi son ölçümü, trendi, uyumu, planı,
doktor notları ve hızlı işlemler.

Tüm veriler mevcut veri reposundan gelir; görselde kullanılan ikonlar
``ui/icons.py`` içindeki renkli Canvas çizimleridir (emoji fontu kullanılmaz).
"""

from __future__ import annotations

import datetime
import tkinter as tk

from PIL import Image, ImageTk

from .. import state, theme
from ..db import doctors as doctors_db
from ..db import patients as patients_db
from ..db import records as records_db
from . import charts, helpers, icons, surface

MONTHS_TR = (
    "Oca", "Şub", "Mar", "Nis", "May", "Haz",
    "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara",
)

HERO_H = 176


def _status(value) -> tuple[str, str]:
    """Kan şekeri değeri → (etiket, renk)."""
    if value is None:
        return ("Veri yok", theme.MUTED)
    value = float(value)
    if value < 70:
        return ("Düşük", theme.BLOOD)
    if value <= 140:
        return ("Normal", theme.GREEN)
    if value <= 200:
        return ("Yüksek", theme.AMBER)
    return ("Kritik", theme.BLOOD)


def _when(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime.datetime):
        day, clock = value.date(), value.strftime("%H:%M")
    else:
        day, clock = value, ""
    today = datetime.date.today()
    if day == today:
        base = "Bugün"
    elif day == today - datetime.timedelta(days=1):
        base = "Dün"
    else:
        base = f"{day.day} {MONTHS_TR[day.month - 1]}"
    return f"{base} · {clock}" if clock else base


def _initials(ad: str | None, soyad: str | None) -> str:
    letters = f"{(ad or '')[:1]}{(soyad or '')[:1]}".upper()
    return letters or "HA"


def _status_badge(parent, value, *, size: int = 8) -> tk.Label:
    text, color = _status(value)
    return tk.Label(
        parent,
        text=text,
        font=theme.font(size, True),
        bg=theme.dark_soft(color, 0.34),
        fg=color,
        padx=8,
        pady=2,
    )


def _bind_tree(widget, sequence: str, callback) -> None:
    widget.bind(sequence, callback)
    for child in widget.winfo_children():
        _bind_tree(child, sequence, callback)


def _is_inside(widget, container) -> bool:
    while widget is not None:
        if widget is container:
            return True
        widget = getattr(widget, "master", None)
    return False


def _bind_hover(container, enter, leave) -> None:
    """Alt widget'lar arasında gezerken hover'ın titremesini önler."""

    def _enter(_event=None):
        enter()

    def _leave(_event=None):
        def check():
            try:
                under = container.winfo_containing(*container.winfo_pointerxy())
            except tk.TclError:
                under = None
            if under is None or not _is_inside(under, container):
                leave()

        container.after_idle(check)

    def walk(widget):
        widget.bind("<Enter>", _enter, add="+")
        widget.bind("<Leave>", _leave, add="+")
        for child in widget.winfo_children():
            walk(child)

    walk(container)


def _paint(widget, color: str) -> None:
    """Bir satırdaki tüm zeminleri (rozet canvas'ı dâhil) boyar."""
    if getattr(widget, "_keep_bg", False):
        return
    try:
        widget.configure(bg=color)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        _paint(child, color)


class DashboardContent:
    def __init__(self, parent, navigate) -> None:
        self.parent = parent
        self.navigate = navigate
        self.doctor = state.session.user_role == "Doktor"
        self.data: dict = {}
        self.cards: dict[str, tk.Frame] = {}
        self.stat_cards: list[tk.Frame] = []
        self._mode: int | None = None
        self._stat_cols: int | None = None

    # ------------------------------------------------------------------ build
    def build(self) -> None:
        self.root = tk.Frame(self.parent, bg=theme.APP_BG)
        self.root.pack(fill="both", expand=True)
        self.data = self._load()

        self._build_hero()
        if self.data.get("error"):
            tk.Label(
                self.root,
                text=f"Bazı veriler yüklenemedi: {self.data['error']}",
                font=theme.font(8),
                bg=theme.dark_soft(theme.DANGER, 0.22),
                fg=theme.DANGER,
                anchor="w",
                padx=12,
                pady=5,
            ).pack(fill="x", padx=10, pady=(6, 0))
        self._build_stats()

        self.body = tk.Frame(self.root, bg=theme.APP_BG)
        self.body.pack(fill="both", expand=True, padx=10, pady=(6, 6))

        self._build_chart_card()
        self._build_recent_card()
        self._build_main_card()
        self._build_donut_card()
        self._build_quick_card()
        if not self.doctor:
            self._build_notes_card()

        self._reflow(force=True)
        self.root.after(40, lambda: self._reflow(force=True))
        self.root.bind("<Configure>", lambda _e: self._reflow())

    # ------------------------------------------------------------------- data
    def _load(self) -> dict:
        try:
            if self.doctor:
                doktor_id = state.session.doctor_id
                stats = doctors_db.doctor_dashboard(doktor_id)
                patients = doctors_db.search_patients_for_doctor(doktor_id)
                patients.sort(key=self._risk_key)
                return {
                    "stats": stats,
                    "patients": patients,
                    "risk": len(doctors_db.critical_patients_for_doctor(doktor_id)),
                    "trend": doctors_db.glucose_trend_for_doctor(doktor_id, 7),
                    "avg": doctors_db.average_glucose_for_doctor(doktor_id, 7),
                    "counts": doctors_db.measurement_counts_for_doctor(doktor_id, 7),
                    "recent": doctors_db.recent_measurements_for_doctor(doktor_id, 5),
                    "distribution": doctors_db.glucose_distribution_for_doctor(doktor_id, 30),
                    "unread": stats.get("okunmamis_uyari_sayisi", 0),
                }

            patient_id = state.session.patient_id
            recent = records_db.recent_measurements(patient_id, limit=5)
            scores = records_db.compliance_history(patient_id, limit=1)
            appointments = patients_db.appointments_for_patient(patient_id)
            today = datetime.date.today()
            future = [
                row
                for row in appointments
                if row["durum"] == "Planlandı" and row["randevu_tarihi"] >= today
            ]
            future.sort(key=lambda row: (row["randevu_tarihi"], row["randevu_saati"] or ""))
            notifications = patients_db.notifications_for_user(
                state.session.user_id, limit=200
            )
            return {
                "latest": recent[0] if recent else None,
                "recent": recent,
                "trend": records_db.daily_averages(patient_id, 7),
                "avg": records_db.average_glucose(patient_id, 7),
                "counts": [1 if row["ortalama"] is not None else 0 for row in records_db.daily_averages(patient_id, 7)],
                "distribution": records_db.glucose_distribution(patient_id, 30),
                "compliance": scores[0] if scores else None,
                "diet": records_db.active_diet_plan(patient_id),
                "exercise": records_db.active_exercise_plan(patient_id),
                "appointment": future[0] if future else None,
                "notes": records_db.shared_doctor_notes(patient_id),
                "unread": sum(1 for row in notifications if not row["okundu"]),
            }
        except Exception as exc:  # bağlantı / şema hatası
            return {"error": str(exc)}

    @staticmethod
    def _risk_key(patient: dict) -> tuple:
        value = patient.get("son_kan_sekeri")
        if value is None:
            return (2, 0)
        value = float(value)
        if value < 70:
            return (0, 70 - value)
        if value > 140:
            return (0, value - 140)
        return (1, 0)

    # ------------------------------------------------------------------- hero
    def _build_hero(self) -> None:
        self.hero = tk.Canvas(
            self.root, height=HERO_H, bg=theme.APP_BG, highlightthickness=0, bd=0
        )
        self.hero.pack(fill="x", padx=10, pady=(8, 0))
        self.hero.bind("<Configure>", self._draw_hero)
        self.root.after(20, lambda: self._draw_hero())

    def _draw_hero(self, _event=None) -> None:
        width = max(self.hero.winfo_width(), 320)
        height = HERO_H
        self.hero.delete("all")
        hero_pil = surface.hero_banner_image(
            width, height, str(helpers.ASSETS / "hero-klinik.png"), 18, theme.APP_BG
        )

        is_doctor = self.doctor
        name = state.session.full_name or "Kullanıcı"
        if is_doctor and not name.lower().startswith(("dr.", "dr ")):
            greeting = f"Merhaba, Dr. {name}"
        else:
            greeting = f"Merhaba, {name}"
        subtitle = (
            "Hastalarınızın sağlık verileri tek bakışta. Bugünkü durumu inceleyin."
            if is_doctor
            else "Kan şekerinizi, uyumunuzu ve randevularınızı tek ekrandan takip edin."
        )

        if is_doctor:
            stats = self.data.get("stats", {})
            pill = (
                f"Bugün {stats.get('bugun_olcum_yapan_hasta_sayisi', 0)} hasta ölçüm yaptı"
                f"   ·   {self.data.get('unread', 0)} okunmamış uyarı"
            )
            pill_color = theme.AMBER if self.data.get("unread") else theme.GREEN
            pill_icon = "alert" if self.data.get("unread") else "check"
            pill_tag = "alerts"
        else:
            latest = self.data.get("latest")
            if latest:
                etiket, color = _status(latest["kan_sekeri_degeri"])
                pill = f"Son ölçüm {latest['kan_sekeri_degeri']:g} mg/dL   ·   {etiket}"
                pill_color = color
                pill_icon = "droplet"
            else:
                pill = "Henüz ölçüm kaydınız yok — ilk ölçümünüzü ekleyin."
                pill_color = theme.BLOOD
                pill_icon = "droplet"
            pill_tag = "history"

        # Pill zemini + ikon, hero fotoğrafının kırpımı üzerine tek PIL görüntüsü
        # olarak bastırılır (anti-aliased; ayrı canvas çizimi yerine).
        pill_w = round(max(300, min(600, 40 + len(pill) * 6.4)))
        pill_x, pill_y, pill_h = 30, 126, 38
        crop = hero_pil.crop((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h))
        pill_img = surface.composite_card_image(crop, pill_h // 2, "#0b1628", theme.CARD_EDGE)
        icon_img = icons.icon_image(pill_icon, 26, pill_color)
        pill_img.paste(icon_img, (14, (pill_h - 26) // 2), icon_img)
        hero_pil.paste(pill_img, (pill_x, pill_y))

        self._hero_image = ImageTk.PhotoImage(hero_pil)
        self.hero.create_image(0, 0, anchor="nw", image=self._hero_image)
        self.hero.create_text(
            30, 48, text=greeting, anchor="w",
            font=theme.display(22), fill="white",
        )
        self.hero.create_text(
            30, 86, text=subtitle, anchor="w", width=min(560, width - 80),
            font=theme.font(10), fill="#c9d6ea", justify="left",
        )
        # Tk, dolgusuz dikdörtgenlerde yalnızca kenarı tıklanabilir sayar; pilin
        # tamamını tıklanabilir yapmak için tamamen saydam bir PhotoImage kullanılır
        # (Tk, resim öğelerinde piksel alfasına değil sınırlayıcı kutuya bakar).
        self._pill_hit = ImageTk.PhotoImage(Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0)))
        self.hero.create_image(
            pill_x, pill_y, anchor="nw", image=self._pill_hit, tags=("pillbg", pill_tag),
        )
        self.hero.create_text(
            pill_x + 36, pill_y + pill_h / 2, text=pill, anchor="w", font=theme.font(9),
            fill="#dbe6f7", tags=(pill_tag,),
        )
        self.hero.tag_bind(pill_tag, "<Button-1>", lambda _e: self._hero_pill_click())

    def _hero_pill_click(self) -> None:
        if self.doctor:
            self.navigate("alerts")
        else:
            self.navigate("history")

    # ------------------------------------------------------------------ stats
    def _build_stats(self) -> None:
        self.stats_frame = tk.Frame(self.root, bg=theme.APP_BG)
        self.stats_frame.pack(fill="x", padx=6, pady=(6, 0))

        if self.doctor:
            stats = self.data.get("stats", {})
            avg = self.data.get("avg")
            trend_values = [
                row["ortalama"] for row in self.data.get("trend", []) if row["ortalama"] is not None
            ]
            cards = [
                ("users", "Toplam Hasta", stats.get("toplam_hasta_sayisi", 0),
                 theme.BLUE, None, "Kayıtlı hasta"),
                ("droplet", "Bugün Ölçüm", stats.get("bugun_olcum_yapan_hasta_sayisi", 0),
                 theme.BLOOD, self.data.get("counts"), "Ölçüm yapan hasta"),
                ("trend", "Ort. Kan Şekeri", f"{avg:g}" if avg is not None else "—",
                 theme.PURPLE, trend_values if len(trend_values) >= 2 else None,
                 "mg/dL · son 7 gün"),
                ("alert", "Riskli Hasta", self.data.get("risk", 0),
                 theme.AMBER, None, "Takip gerektiren"),
            ]
        else:
            latest = self.data.get("latest")
            last_value = f"{latest['kan_sekeri_degeri']:g}" if latest else "—"
            etiket, _ = _status(latest["kan_sekeri_degeri"] if latest else None)
            avg = self.data.get("avg")
            score = self.data.get("compliance")
            score_value = f"%{score['genel_uyum_skoru']:.0f}" if score else "—"
            score_accent = theme.GREEN
            if score:
                score_num = float(score.get("genel_uyum_skoru", 0))
                if score_num < 50:
                    score_accent = theme.BLOOD
                elif score_num < 75:
                    score_accent = theme.AMBER
            appointment = self.data.get("appointment")
            appt_value = (
                f"{appointment['randevu_tarihi'].day:02d}.{appointment['randevu_tarihi'].month:02d}"
                if appointment
                else "Yok"
            )
            appt_note = (
                appointment.get("randevu_saati") or "Randevularım"
                if appointment
                else "Planlanmış randevu yok"
            )
            trend_values = [
                row["ortalama"] for row in self.data.get("trend", []) if row["ortalama"] is not None
            ]
            cards = [
                ("droplet", "Son Kan Şekeri", last_value, theme.BLOOD, None,
                 f"mg/dL · {etiket}"),
                ("chart", "7 Günlük Ortalama", f"{avg:g}" if avg is not None else "—",
                 theme.CYAN, trend_values if len(trend_values) >= 2 else None, "mg/dL"),
                ("target", "Uyum Skoru", score_value, score_accent, None, "Son hesaplama"),
                ("calendar", "Yaklaşan Randevu", appt_value, theme.AMBER, None, appt_note),
            ]

        for icon, title, value, accent, spark, note in cards:
            card = theme.stat_card(
                self.stats_frame,
                icon=icon,
                title=title,
                value=value,
                accent=accent,
                spark=spark,
                note=note,
            )
            self.stat_cards.append(card)

    def _layout_stats(self, cols: int) -> None:
        for _index, card in enumerate(self.stat_cards):
            card.grid_forget()
        for col in range(4):
            self.stats_frame.grid_columnconfigure(
                col, weight=0, uniform=""
            )
        for index, card in enumerate(self.stat_cards):
            row, col = divmod(index, cols)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        for col in range(cols):
            self.stats_frame.grid_columnconfigure(col, weight=1, uniform="stat")

    # ------------------------------------------------------------------- card
    def _card(
        self,
        key: str,
        title: str,
        subtitle: str,
        icon: str,
        accent: str,
        *,
        link: str | None = None,
        link_command=None,
    ) -> surface.Panel:
        """Yuvarlatılmış kart: üstte başlık satırı, altta ``card.content`` içeriği."""
        card = surface.Panel(
            self.body, radius=18, fill=theme.CARD_BG, border=theme.BORDER, pad=16,
            fit_width=False,
        )

        head = tk.Frame(card.body, bg=theme.CARD_BG)
        head.pack(fill="x", pady=(0, 12))
        icons.badge(head, icon, accent, size=32, bg=theme.CARD_BG).pack(side="left")
        title_box = tk.Frame(head, bg=theme.CARD_BG)
        title_box.pack(side="left", padx=(10, 4), fill="x", expand=True)
        tk.Label(
            title_box, text=title, font=theme.display(11),
            bg=theme.CARD_BG, fg=theme.TEXT, anchor="w",
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                title_box, text=subtitle, font=theme.font(8),
                bg=theme.CARD_BG, fg=theme.MUTED, anchor="w",
            ).pack(anchor="w")

        if link:
            link_label = tk.Label(
                head, text=link, font=theme.font(8, True),
                bg=theme.CARD_BG, fg=theme.PRIMARY, cursor="hand2",
            )
            link_label.pack(side="right", padx=(4, 0))
            if link_command is not None:
                link_label.bind("<Button-1>", lambda _e: link_command())
            link_label.bind("<Enter>", lambda _e: link_label.configure(fg=theme.CYAN))
            link_label.bind("<Leave>", lambda _e: link_label.configure(fg=theme.PRIMARY))

        content = tk.Frame(card.body, bg=theme.CARD_BG)
        content.pack(fill="both", expand=True)
        card.content = content
        self.cards[key] = card
        return card

    # ------------------------------------------------------------------ chart
    def _build_chart_card(self) -> None:
        if self.doctor:
            link, command = "Hastalar →", lambda: self.navigate("patients")
        else:
            link, command = "Geçmiş →", lambda: self.navigate("history")
        card = self._card(
            "chart", "Kan Şekeri Trendi", "Günlük ortalama · hedef bant 70–140 mg/dL",
            "trend", theme.CYAN, link=link, link_command=command,
        )
        points = [
            (row["tarih"], row["ortalama"]) for row in self.data.get("trend", [])
        ]
        color = theme.CYAN if self.doctor else theme.BLOOD
        charts.plot_dashboard_trend(card.content, points, color=color)

    # ----------------------------------------------------------------- recent
    def _build_recent_card(self) -> None:
        if self.doctor:
            link, command = "Hastalar →", lambda: self.navigate("patients")
        else:
            link, command = "Tümü →", lambda: self.navigate("history")
        card = self._card(
            "recent", "Son Ölçümler", "En yeni 5 kayıt",
            "droplet", theme.BLOOD, link=link, link_command=command,
        )
        rows = self.data.get("recent", [])
        if not rows:
            tk.Label(
                card.content, text="Henüz ölçüm kaydı yok.", font=theme.font(9),
                bg=theme.CARD_BG, fg=theme.MUTED,
            ).pack(pady=24)
            return

        for index, row in enumerate(rows):
            if self.doctor:
                value = row["kan_sekeri_degeri"]
                title = row["hasta_adi"]
                when = _when(row["olcum_zamani"])
            else:
                value = row["kan_sekeri_degeri"]
                title = row.get("olcum_tipi") or "Kan Şekeri"
                when = _when(
                    datetime.datetime.combine(row["olcum_tarihi"], row["olcum_saati"])
                )
            _, color = _status(value)
            line = tk.Frame(card.content, bg=theme.CARD_BG)
            line.pack(fill="x", pady=1)
            if self.doctor:
                # Hangi hastaya ait olduğu tek bakışta görünsün: jenerik ikon
                # yerine hastanın baş harfli, durum renkli avatarı.
                first, _, last = title.partition(" ")
                surface.Avatar(line, _initials(first, last), color, size=28,
                               bg=theme.CARD_BG).pack(side="left", padx=(0, 8))
            else:
                icons.badge(line, "droplet", color, size=26, bg=theme.CARD_BG).pack(
                    side="left", padx=(0, 8)
                )
            text_box = tk.Frame(line, bg=theme.CARD_BG)
            text_box.pack(side="left", fill="x", expand=True)
            tk.Label(
                text_box, text=title, font=theme.font(9, True),
                bg=theme.CARD_BG, fg=theme.TEXT, anchor="w",
            ).pack(anchor="w")
            tk.Label(
                text_box, text=when, font=theme.font(7),
                bg=theme.CARD_BG, fg=theme.MUTED, anchor="w",
            ).pack(anchor="w")
            right = tk.Frame(line, bg=theme.CARD_BG)
            right.pack(side="right")
            tk.Label(
                right, text=f"{value:g}", font=theme.font(11, True),
                bg=theme.CARD_BG, fg=theme.TEXT, anchor="e",
            ).pack(side="left", pady=(2, 0))
            _status_badge(right, value, size=7).pack(
                side="left", padx=(5, 0), pady=(3, 0)
            )
            if index < len(rows) - 1:
                tk.Frame(card.content, bg=theme.BORDER, height=1).pack(fill="x", pady=(1, 0))

    # ---------------------------------------------------------------- patients
    def _build_main_card(self) -> None:
        if self.doctor:
            self._build_patients_card()
        else:
            self._build_plan_card()

    def _build_patients_card(self) -> None:
        card = self._card(
            "main", "Hastalarınızın Durumu", "Risk sırasına göre",
            "users", theme.BLUE, link="Tümü →", link_command=lambda: self.navigate("patients"),
        )
        patients = self.data.get("patients", [])[:4]
        if not patients:
            tk.Label(
                card.content, text="Henüz hasta kaydı yok.", font=theme.font(9),
                bg=theme.CARD_BG, fg=theme.MUTED,
            ).pack(pady=20)
            return
        for patient in patients:
            value = patient.get("son_kan_sekeri")
            _, color = _status(value)
            row = tk.Frame(card.content, bg=theme.CARD_BG, cursor="hand2")
            row.pack(fill="x", pady=0)
            surface.Avatar(
                row, _initials(patient.get("ad"), patient.get("soyad")), color,
                size=32, bg=theme.CARD_BG,
            ).pack(side="left", padx=(0, 8), pady=2)
            text_box = tk.Frame(row, bg=theme.CARD_BG)
            text_box.pack(side="left", fill="x", expand=True)
            tk.Label(
                text_box, text=f"{patient.get('ad', '')} {patient.get('soyad', '')}".strip(),
                font=theme.font(9, True), bg=theme.CARD_BG, fg=theme.TEXT, anchor="w",
            ).pack(anchor="w")
            tip = patient.get("diyabet_tipi") or "Diyabet"
            tk.Label(
                text_box, text=tip, font=theme.font(8),
                bg=theme.CARD_BG, fg=theme.MUTED, anchor="w",
            ).pack(anchor="w")
            right = tk.Frame(row, bg=theme.CARD_BG)
            right.pack(side="right", padx=(6, 0))
            tk.Label(
                right, text=f"{value:g}" if value is not None else "—",
                font=theme.font(9, True), bg=theme.CARD_BG, fg=theme.TEXT, anchor="e",
            ).pack(anchor="e")
            _status_badge(right, value, size=7).pack(anchor="e", pady=(1, 0))
            arrow = icons.icon(row, "arrow", size=13, color=theme.MUTED, bg=theme.CARD_BG)
            arrow.pack(side="right", padx=(4, 2))

            def open_patient(_event=None, p=patient):
                self.navigate("patient_detail", patient_id=str(p["hasta_id"]))

            _bind_tree(row, "<Button-1>", open_patient)
            _bind_hover(
                row,
                lambda r=row: _paint(r, theme.CARD_HOVER),
                lambda r=row: _paint(r, theme.CARD_BG),
            )

    def _build_plan_card(self) -> None:
        card = self._card(
            "main", "Günlük Planım", "Diyet, egzersiz ve ölçüm uyumu",
            "clipboard", theme.GREEN, link="Planlar →", link_command=lambda: self.navigate("patient_plans"),
        )
        score = self.data.get("compliance") or {}
        diet = self.data.get("diet")
        exercise = self.data.get("exercise")
        rows = [
            (
                "apple",
                diet.get("diyet_adi") if diet else "Aktif diyet planı yok",
                "Diyet uyumu",
                float(score.get("diyet_uyum_orani", 0)),
                theme.GREEN,
            ),
            (
                "dumbbell",
                exercise.get("egzersiz_adi") if exercise else "Aktif egzersiz planı yok",
                "Egzersiz uyumu",
                float(score.get("egzersiz_uyum_orani", 0)),
                theme.ORANGE,
            ),
            (
                "droplet",
                "Kan şekeri ölçüm düzeni",
                "Ölçüm uyumu",
                float(score.get("olcum_uyum_orani", 0)),
                theme.BLOOD,
            ),
        ]
        for icon, title, label, ratio, color in rows:
            item = tk.Frame(card.content, bg=theme.CARD_BG)
            item.pack(fill="x", pady=4)
            icons.badge(item, icon, color, size=28, bg=theme.CARD_BG).pack(
                side="left", padx=(0, 8)
            )
            tk.Label(
                item, text=f"%{ratio:.0f}", font=theme.font(9, True),
                bg=theme.CARD_BG, fg=color,
            ).pack(side="right", padx=(6, 0))
            text_box = tk.Frame(item, bg=theme.CARD_BG)
            text_box.pack(side="left", fill="x", expand=True)
            tk.Label(
                text_box, text=title, font=theme.font(9, True),
                bg=theme.CARD_BG, fg=theme.TEXT, anchor="w",
            ).pack(anchor="w")
            tk.Label(
                text_box, text=label, font=theme.font(8),
                bg=theme.CARD_BG, fg=theme.MUTED, anchor="w",
            ).pack(anchor="w")
            bar = tk.Canvas(
                text_box, height=5, bg=theme.CARD_2, highlightthickness=0, bd=0,
            )
            bar.pack(fill="x", pady=(4, 0))

            def _draw_bar(event, canvas=bar, value=ratio, c=color):
                canvas.delete("all")
                width = max(event.width, 1)
                canvas.create_rectangle(0, 0, width, 5, fill=theme.CARD_2, outline="")
                canvas.create_rectangle(
                    0, 0, max(2, width * min(max(value, 0), 100) / 100), 5,
                    fill=c, outline="",
                )

            bar.bind("<Configure>", _draw_bar)

    # ------------------------------------------------------------------ donut
    def _build_donut_card(self) -> None:
        card = self._card(
            "donut", "Kan Şekeri Dağılımı", "Son 30 gün",
            "target", theme.AMBER, )
        counts = self.data.get("distribution", {}) or {}
        normal = int(counts.get("normal", 0))
        high = int(counts.get("yuksek", 0))
        low = int(counts.get("dusuk", 0))
        total = normal + high + low

        holder = tk.Frame(card.content, bg=theme.CARD_BG)
        holder.pack(expand=True)
        ring = tk.Canvas(
            holder, width=132, height=132, bg=theme.CARD_BG,
            highlightthickness=0, bd=0,
        )
        ring.pack(side="left", padx=(2, 10), pady=2)
        ring.create_oval(
            14, 14, 118, 118, outline=theme.CARD_2, width=13,
        )
        segments = (
            ("normal", normal, theme.GREEN),
            ("yuksek", high, theme.AMBER),
            ("dusuk", low, theme.BLOOD),
        )
        if total:
            start = 90.0
            for _key, count, color in segments:
                if count <= 0:
                    continue
                extent = -360.0 * count / total
                ring.create_arc(
                    14, 14, 118, 118, start=start, extent=extent,
                    style="arc", outline=color, width=13,
                )
                start += extent
        ring.create_text(
            66, 60, text=str(total), font=theme.font(18, True), fill=theme.TEXT,
        )
        ring.create_text(
            66, 82, text="ölçüm", font=theme.font(8), fill=theme.MUTED,
        )

        legend = tk.Frame(holder, bg=theme.CARD_BG)
        legend.pack(side="left", fill="both", expand=True, pady=4)
        for label, count, color in (
            ("Normal", normal, theme.GREEN),
            ("Yüksek", high, theme.AMBER),
            ("Düşük", low, theme.BLOOD),
        ):
            line = tk.Frame(legend, bg=theme.CARD_BG)
            line.pack(fill="x", pady=2)
            dot = tk.Canvas(
                line, width=9, height=9, bg=theme.CARD_BG,
                highlightthickness=0, bd=0,
            )
            dot.create_oval(1, 1, 8, 8, fill=color, outline="")
            dot.pack(side="left", padx=(0, 6))
            tk.Label(
                line, text=label, font=theme.font(8),
                bg=theme.CARD_BG, fg=theme.MUTED,
            ).pack(side="left")
            tk.Label(
                line, text=str(count), font=theme.font(8, True),
                bg=theme.CARD_BG, fg=theme.TEXT,
            ).pack(side="right")

    # ------------------------------------------------------------------- quick
    def _build_quick_card(self) -> None:
        card = self._card(
            "quick", "Hızlı İşlemler", "Sık kullanılan ekranlar", "plus", theme.PRIMARY,
        )
        if self.doctor:
            actions = [
                ("add_patient", "Yeni Hasta Ekle", "Hasta kaydı oluştur", "plus", theme.GREEN),
                ("alerts", "Hasta Uyarıları", f"{self.data.get('unread', 0)} okunmamış", "alert", theme.BLOOD),
                ("appointments", "Randevu Yönetimi", "Takvimi düzenle", "calendar", theme.AMBER),
                ("reports", "Rapor Oluştur", "Hasta raporu al", "report", theme.TEAL),
            ]
        else:
            actions = [
                ("measure", "Ölçüm Gir", "Kan şekeri kaydı", "droplet", theme.BLOOD),
                ("diet", "Diyet / Egzersiz", "Günlük durum", "apple", theme.GREEN),
                ("symptoms", "Semptom Takibi", "Belirti kaydı", "bandage", theme.ORANGE),
                ("history", "Geçmiş & Grafik", "Ölçüm trendi", "chart", theme.CYAN),
            ]
        for key, title, sub, icon, accent in actions:
            row = tk.Frame(
                card.content, bg=theme.CARD_2,
                highlightbackground=theme.BORDER, highlightthickness=1,
                cursor="hand2",
            )
            row.pack(fill="x", pady=2)
            icons.badge(row, icon, accent, size=32, bg=theme.CARD_2).pack(
                side="left", padx=7, pady=3
            )
            text_box = tk.Frame(row, bg=theme.CARD_2)
            text_box.pack(side="left", fill="x", expand=True, padx=(2, 0))
            tk.Label(
                text_box, text=title, font=theme.font(9, True),
                bg=theme.CARD_2, fg=theme.TEXT, anchor="w",
            ).pack(anchor="w")
            tk.Label(
                text_box, text=sub, font=theme.font(8),
                bg=theme.CARD_2, fg=theme.MUTED, anchor="w",
            ).pack(anchor="w")
            arrow = icons.icon(row, "arrow", size=13, color=theme.MUTED, bg=theme.CARD_2)
            arrow.pack(side="right", padx=(4, 8))
            _bind_tree(row, "<Button-1>", lambda _e, k=key: self.navigate(k))
            _bind_hover(
                row,
                lambda r=row: _paint(r, theme.CARD_HOVER),
                lambda r=row: _paint(r, theme.CARD_2),
            )

    # ------------------------------------------------------------------- notes
    def _build_notes_card(self) -> None:
        card = self._card(
            "notes", "Doktor Notlarım", "Sizinle paylaşılan son not",
            "report", theme.TEAL, link="Planlar →", link_command=lambda: self.navigate("patient_plans"),
        )
        notes = self.data.get("notes") or []
        if not notes:
            tk.Label(
                card.content, text="Henüz sizinle paylaşılmış bir doktor notu yok.",
                font=theme.font(9), bg=theme.CARD_BG, fg=theme.MUTED,
            ).pack(anchor="w", pady=8)
            return
        note = notes[0]
        head = tk.Frame(card.content, bg=theme.CARD_BG)
        head.pack(fill="x")
        tk.Label(
            head, text=note["not_basligi"], font=theme.font(9, True),
            bg=theme.CARD_BG, fg=theme.TEXT, anchor="w",
        ).pack(side="left")
        tk.Label(
            head, text=helpers.date_label(note.get("olusturma_tarihi")),
            font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED,
        ).pack(side="right")
        content = tk.Label(
            card.content, text=note["not_icerigi"], font=theme.font(9),
            bg=theme.CARD_BG, fg=theme.MUTED, anchor="w", justify="left",
            wraplength=760,
        )
        content.pack(fill="x", pady=(2, 0))
        content.bind(
            "<Configure>",
            lambda e: content.configure(wraplength=max(240, e.width - 8)),
        )

    # ----------------------------------------------------------------- reflow
    def _reflow(self, force: bool = False) -> None:
        width = max(self.root.winfo_width(), 1)
        if width <= 10:
            return
        mode = 3 if width >= 930 else 2
        stat_cols = 4 if width >= 900 else 2
        if not force and (mode, stat_cols) == (self._mode, self._stat_cols):
            return
        self._mode, self._stat_cols = mode, stat_cols
        self._layout_stats(stat_cols)

        for card in self.cards.values():
            card.grid_forget()
        for col in range(3):
            self.body.grid_columnconfigure(col, weight=0, uniform="")
        self.body.grid_rowconfigure(0, weight=0)
        self.body.grid_rowconfigure(1, weight=0)
        self.body.grid_rowconfigure(2, weight=0)
        self.body.grid_rowconfigure(3, weight=0)

        if mode == 3:
            for col in range(3):
                self.body.grid_columnconfigure(col, weight=1, uniform="card")
            # Tam ekranda kartların dikeyde büyümesini sağla.
            self.body.grid_rowconfigure(0, weight=1)
            self.body.grid_rowconfigure(1, weight=1)
            self.cards["chart"].grid(
                row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=4
            )
            self.cards["recent"].grid(row=0, column=2, sticky="nsew", padx=5, pady=4)
            self.cards["main"].grid(row=1, column=0, sticky="nsew", padx=5, pady=4)
            self.cards["donut"].grid(row=1, column=1, sticky="nsew", padx=5, pady=4)
            self.cards["quick"].grid(row=1, column=2, sticky="nsew", padx=5, pady=4)
            if "notes" in self.cards:
                self.cards["notes"].grid(
                    row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=4
                )
        else:
            for col in range(2):
                self.body.grid_columnconfigure(col, weight=1, uniform="card")
            for row in range(3):
                self.body.grid_rowconfigure(row, weight=1)
            self.cards["chart"].grid(
                row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=4
            )
            self.cards["recent"].grid(row=1, column=0, sticky="nsew", padx=5, pady=4)
            self.cards["quick"].grid(row=1, column=1, sticky="nsew", padx=5, pady=4)
            self.cards["main"].grid(row=2, column=0, sticky="nsew", padx=5, pady=4)
            self.cards["donut"].grid(row=2, column=1, sticky="nsew", padx=5, pady=4)
            if "notes" in self.cards:
                self.cards["notes"].grid(
                    row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=4
                )


def build_dashboard(parent, navigate) -> DashboardContent:
    content = DashboardContent(parent, navigate)
    content.build()
    return content
