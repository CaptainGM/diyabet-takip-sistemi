"""Doktor — hasta listesi, yeni hasta kaydı ve hasta detayı."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from bson import ObjectId
from PIL import ImageTk

from .... import state, theme
from ....db import bootstrap as B
from ....db import doctors as doctors_db
from ....db import records as records_db
from ....db import reference as ref
from ....db.client import get_db
from ....services import auth_service
from ... import charts, icons
from ...dashboard_home import _initials, _status, _when
from ..base import (
    Page,
    badge,
    card,
    empty,
    field_label,
    metric,
    notice,
    section,
    stat_grid,
    table,
)
from ._common import DIABET_TYPES, IMPORTANCE, VISIBILITY, _date, _value_text


class PatientsPage(Page):
    title = "Hastalarım"
    subtitle = "Hasta kayıtlarını filtreleyin, riskleri görün ve detaylara geçin."
    icon = "users"
    accent = theme.CYAN

    def build(self) -> None:
        self.patients: dict[str, dict] = {}
        self.empty_label = None
        self.page_head(
            actions=(
                theme.button(self, "Uyarılar", lambda: self.app.navigate("alerts"), style="ghost"),
                theme.button(self, "Yeni Hasta", lambda: self.app.navigate("add_patient"), style="primary"),
            )
        )
        self._build_metrics()
        self._build_filters()
        self._build_table()
        self.refresh()

    def _build_metrics(self) -> None:
        stats = doctors_db.doctor_dashboard(state.session.doctor_id)
        critical = len(doctors_db.critical_patients_for_doctor(state.session.doctor_id))
        total = int(stats.get("toplam_hasta_sayisi", 0))
        avg = doctors_db.average_glucose_for_doctor(state.session.doctor_id, 7)
        box = tk.Frame(self.body, bg=theme.APP_BG)
        box.pack(fill="x", pady=(0, 12))
        cards = [
            metric(
                box,
                icon="users",
                title="Kayıtlı Hasta",
                value=total,
                accent=theme.CYAN,
                note="Takip listenizde",
            ),
            metric(
                box,
                icon="alert",
                title="Riskli Hasta",
                value=critical,
                accent=theme.BLOOD,
                note="Öncelik verin" if critical else "Risk yok",
            ),
            metric(
                box,
                icon="droplet",
                title="Bugün Ölçüm",
                value=int(stats.get("bugun_olcum_yapan_hasta_sayisi", 0)),
                accent=theme.PRIMARY,
                note="Ölçüm yapan hasta",
            ),
            metric(
                box,
                icon="trend",
                title="7 Gün Ortalaması",
                value=_value_text(avg),
                accent=theme.PURPLE,
                note="Tüm hastalar",
            ),
        ]
        stat_grid(box, cards, columns=4)

    def _build_filters(self) -> None:
        outer = card(self.body, padx=16, pady=14)
        outer.pack(fill="x", pady=(0, 12))
        body = outer.body
        grid = tk.Frame(body, bg=theme.CARD_BG)
        grid.pack(fill="x")

        field_label(grid, "Ad / Soyad / T.C.").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.name_entry = theme.entry(grid, width=22)
        self.name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))

        field_label(grid, "Min mg/dL").grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.min_entry = theme.entry(grid, width=8)
        self.min_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))

        field_label(grid, "Max mg/dL").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.max_entry = theme.entry(grid, width=8)
        self.max_entry.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(4, 0))

        field_label(grid, "Belirti").grid(row=0, column=3, sticky="w", padx=(0, 8))
        self.symptom_options = ref.get_symptom_options()
        symptom_names = ["(Tümü)"] + [name for _sid, name in self.symptom_options]
        self.symptom_var = tk.StringVar(value="(Tümü)")
        self.symptom_menu = tk.OptionMenu(grid, self.symptom_var, *symptom_names)
        self.symptom_menu.configure(
            width=20,
            font=theme.font(9),
            bg=theme.DARK_FIELD,
            fg=theme.TEXT,
            activebackground=theme.PRIMARY_DARK,
            activeforeground="white",
            relief="flat",
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        self.symptom_menu["menu"].configure(
            bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK,
            activeforeground="white",
        )
        self.symptom_menu.grid(row=1, column=3, sticky="ew", padx=(0, 14), pady=(4, 0))

        actions = tk.Frame(grid, bg=theme.CARD_BG)
        actions.grid(row=1, column=4, sticky="e", pady=(4, 0))
        theme.button(actions, "Temizle", self._clear, style="ghost").pack(side="left", padx=(0, 6))
        theme.button(actions, "Filtrele", self.refresh, style="primary").pack(side="left")

        for col, weight in enumerate((2, 1, 1, 2, 0)):
            grid.grid_columnconfigure(col, weight=weight)
        self.name_entry.bind("<Return>", lambda _e: self.refresh())
        self.min_entry.bind("<Return>", lambda _e: self.refresh())
        self.max_entry.bind("<Return>", lambda _e: self.refresh())

    def _build_table(self) -> None:
        outer = card(self.body, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=16, pady=(14, 10))
        section(
            head,
            "Hasta Listesi",
            "Satıra çift tıklayarak klinik detayı açın.",
            icon="users",
            accent=theme.CYAN,
        )
        self.count_label = tk.Label(
            head, text="", font=theme.font(8, True), bg=theme.CARD_BG, fg=theme.MUTED
        )
        self.count_label.pack(side="right", padx=(8, 0), pady=(6, 0))
        self.tree, wrap = table(
            outer.body,
            ("ad", "tc", "tip", "son", "durum", "belirti", "tani"),
            ("Hasta", "T.C. Kimlik No", "Diyabet", "Son Ölçüm", "Durum", "Son Belirti", "Tanı"),
            (220, 130, 90, 120, 100, 240, 105),
            height=13,
            show_icon=True,
        )
        self._avatars: dict[str, object] = {}  # PhotoImage referansları (GC'ye karşı)
        wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tree.tag_configure("critical", background=theme.CRITICAL_BG)
        self.tree.tag_configure("warning", background=theme.WARNING_BG)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())
        self.tree.bind("<Return>", lambda _e: self.open_selected())
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_hint())

    def _clear(self) -> None:
        self.name_entry.delete(0, tk.END)
        self.min_entry.delete(0, tk.END)
        self.max_entry.delete(0, tk.END)
        self.symptom_var.set("(Tümü)")
        self.refresh()

    def _parse(self, text: str) -> float | None:
        try:
            return float((text or "").strip().replace(",", ".")) or None
        except ValueError:
            return None

    def refresh(self) -> None:
        selected_name = self.symptom_var.get()
        symptom_id = None
        for sid, name in self.symptom_options:
            if name == selected_name:
                symptom_id = sid
                break
        try:
            rows = doctors_db.search_patients_for_doctor(
                state.session.doctor_id,
                name_filter=self.name_entry.get(),
                min_bs=self._parse(self.min_entry.get()),
                max_bs=self._parse(self.max_entry.get()),
                symptom_id=symptom_id,
            )
        except Exception:
            messagebox.showerror(
                "Hasta listesi",
                "Hasta listesi şu anda yüklenemiyor. Lütfen tekrar deneyin.",
                parent=self,
            )
            return
        self.patients = {str(p["hasta_id"]): p for p in rows}
        self.tree.delete(*self.tree.get_children())
        self._avatars.clear()
        if self.empty_label is not None:
            self.empty_label.destroy()
            self.empty_label = None
        for idx, p in enumerate(rows):
            value = p.get("son_kan_sekeri")
            status, color = _status(value)
            tags = ["odd" if idx % 2 else "even"]
            if value is not None and (float(value) < 70 or float(value) > 140):
                tags = ["critical"] if float(value) > 200 or float(value) < 70 else ["warning"]
            iid = str(p["hasta_id"])
            avatar = ImageTk.PhotoImage(
                icons.avatar_image(_initials(p.get("ad"), p.get("soyad")), color, 28)
            )
            self._avatars[iid] = avatar  # GC'ye karşı referans
            self.tree.insert(
                "",
                "end",
                iid=iid,
                image=avatar,
                tags=tuple(tags),
                values=(
                    f"{p['ad']} {p['soyad']}",
                    p.get("tc_kimlik_no") or "—",
                    p.get("diyabet_tipi") or "—",
                    _value_text(value),
                    status,
                    p.get("son_belirtiler") or "—",
                    _date(p.get("tani_tarihi")),
                ),
            )
        self.count_label.configure(text=f"{len(rows)} hasta")
        if not rows:
            self.empty_label = empty(
                self.tree.master, "Filtrelere uyan hasta bulunamadı.", icon="users"
            )
            self.empty_label.place(relx=0.5, rely=0.52, anchor="center")

    def _show_hint(self) -> None:
        selection = self.tree.focus()
        if not selection:
            return
        p = self.patients.get(selection)
        if p:
            self.count_label.configure(text=f"Seçili: {p['ad']} {p['soyad']}")

    def open_selected(self) -> None:
        selection = self.tree.focus()
        if not selection:
            messagebox.showinfo("Hasta", "Önce bir hasta seçin.", parent=self)
            return
        self.app.navigate("patient_detail", patient_id=selection, back="patients")


class AddPatientPage(Page):
    title = "Yeni Hasta"
    subtitle = "Hasta hesabı ve klinik profilini birlikte oluşturun."
    icon = "plus"
    accent = theme.GREEN

    def build(self) -> None:
        self.page_head(
            actions=(
                theme.button(self, "Vazgeç", lambda: self.app.navigate("patients"), style="ghost"),
                theme.button(self, "Hastayı Kaydet", self.save, style="primary"),
            )
        )
        top = tk.Frame(self.body, bg=theme.APP_BG)
        top.pack(fill="x")
        left = card(top, padx=18, pady=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = card(top, padx=18, pady=16)
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))

        section(left.body, "Hesap Bilgileri", "Girişte kullanılacak temel bilgiler", icon="user", accent=theme.CYAN)
        form = tk.Frame(left.body, bg=theme.CARD_BG)
        form.pack(fill="x")
        self.tc = self._field(form, 0, "T.C. Kimlik No (11 hane)", theme.entry(form, width=30))
        self.ad = self._field(form, 1, "Ad", theme.entry(form, width=30))
        self.soyad = self._field(form, 2, "Soyad", theme.entry(form, width=30))
        self.eposta = self._field(form, 3, "E-posta", theme.entry(form, width=30))
        self.sifre = self._field(form, 4, "İlk şifre", theme.entry(form, width=30, show="•"))
        theme.muted_label(
            left.body,
            "Şifre en az 8 karakter olmalı; büyük harf, küçük harf, rakam ve özel karakter içermelidir.",
            8,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))
        notice(
            left.body,
            "Hasta ilk girişte bu şifreyle oturum açar. Şifre güvenli biçimde saklanır; düz metin tutulmaz.",
            accent=theme.GREEN,
            icon="shield",
            wraplength=620,
        ).pack(fill="x", pady=(14, 0))

        section(right.body, "Klinik Profil", "Takip aralığı ve tanı bilgileri", icon="stethoscope", accent=theme.TEAL)
        form2 = tk.Frame(right.body, bg=theme.CARD_BG)
        form2.pack(fill="x")
        self.dogum = self._field(form2, 0, "Doğum tarihi", theme.date_entry(form2))
        self.dogum.set_date(datetime.date(1990, 1, 1))
        self.cinsiyet = self._dropdown_field(form2, 1, "Cinsiyet", ("Kadın", "Erkek"))
        self.tip = self._dropdown_field(form2, 2, "Diyabet tipi", DIABET_TYPES)
        self.tani = self._field(form2, 3, "Tanı tarihi", theme.date_entry(form2))
        self.tani.set_date(datetime.date.today())
        target = tk.Frame(form2, bg=theme.CARD_BG)
        target.grid(row=8, column=0, sticky="ew", pady=(8, 0))
        target.grid_columnconfigure(0, weight=1)
        target.grid_columnconfigure(1, weight=1)
        field_label(target, "Hedef alt (mg/dL)").grid(row=0, column=0, sticky="w")
        field_label(target, "Hedef üst (mg/dL)").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.hedef_min = theme.spinbox(target, from_=40, to=200, width=10)
        self.hedef_min.delete(0, tk.END)
        self.hedef_min.insert(0, 70)
        self.hedef_min.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.hedef_max = theme.spinbox(target, from_=80, to=400, width=10)
        self.hedef_max.delete(0, tk.END)
        self.hedef_max.insert(0, 140)
        self.hedef_max.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))

        guide = card(self.body, padx=18, pady=14, accent=theme.GREEN)
        guide.pack(fill="both", expand=True, pady=(14, 0))
        section(
            guide.body,
            "Kayıt Sonrası",
            "Hasta hesabı hazır olduğunda klinik takip bu adımlarla başlar.",
            icon="check",
            accent=theme.GREEN,
        )
        steps = tk.Frame(guide.body, bg=theme.CARD_BG)
        steps.pack(fill="both", expand=True)
        for title, text, icon_name, color in (
            ("Hesap hazır", "Hasta, T.C. kimlik numarası ve ilk şifresiyle güvenli giriş yapar.", "user", theme.CYAN),
            ("Takip başlar", "Ölçümler, uyarılar ve uyum skoru otomatik olarak izlenir.", "target", theme.GREEN),
            ("Plan atayın", "Diyet, egzersiz ve belirti planlarını Plan / Belirti ekranından açın.", "clipboard", theme.PURPLE),
        ):
            step = tk.Frame(steps, bg=theme.CARD_2, highlightbackground=theme.BORDER, highlightthickness=1)
            step.pack(side="left", fill="both", expand=True, padx=5)
            tk.Frame(step, bg=theme.CARD_2).pack(expand=True)
            icons.badge(step, icon_name, color, size=42, bg=theme.CARD_2).pack()
            tk.Label(step, text=title, font=theme.font(11, True), bg=theme.CARD_2,
                     fg=theme.TEXT).pack(pady=(8, 3))
            tk.Label(step, text=text, font=theme.font(9), bg=theme.CARD_2, fg=theme.MUTED,
                     wraplength=380, justify="center").pack(padx=12)
            tk.Frame(step, bg=theme.CARD_2).pack(expand=True)

    def _field(self, form, row: int, text: str, widget):
        field_label(form, text).grid(row=row * 2, column=0, sticky="w", pady=(8, 0))
        widget.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(3, 0))
        form.grid_columnconfigure(0, weight=1)
        return widget

    def _dropdown_field(self, form, row: int, text: str, values):
        field_label(form, text).grid(row=row * 2, column=0, sticky="w", pady=(8, 0))
        var = tk.StringVar(value=values[0])
        menu = tk.OptionMenu(form, var, *values)
        menu.configure(
            font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
            activebackground=theme.PRIMARY_DARK, activeforeground="white",
            relief="flat", highlightthickness=1, highlightbackground=theme.BORDER,
            anchor="w",
        )
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        menu.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(3, 0))
        menu.var = var
        return menu

    def save(self) -> None:
        tc = self.tc.get().strip()
        if not (tc.isdigit() and len(tc) == 11):
            messagebox.showerror("Hasta", "T.C. Kimlik No 11 haneli sayı olmalıdır.", parent=self)
            return
        missing = auth_service.validate_password(self.sifre.get())
        if missing:
            messagebox.showerror(
                "Zayıf şifre",
                "Şifre şu kuralları sağlamıyor:\n• " + "\n• ".join(missing),
                parent=self,
            )
            return
        hedef_min = int(self.hedef_min.get())
        hedef_max = int(self.hedef_max.get())
        if hedef_min >= hedef_max:
            messagebox.showerror("Hasta", "Hedef alt sınır üst sınırdan küçük olmalıdır.", parent=self)
            return
        result = doctors_db.add_patient(
            state.session.doctor_id,
            tc,
            self.ad.get().strip(),
            self.soyad.get().strip(),
            self.eposta.get().strip(),
            self.sifre.get(),
            self.dogum.get_date(),
            self.cinsiyet.var.get(),
            self.tip.var.get(),
            self.tani.get_date(),
            hedef_min,
            hedef_max,
        )
        if result["ok"]:
            messagebox.showinfo("Hasta", result["mesaj"], parent=self)
            self.app.navigate("patients")
        else:
            messagebox.showerror("Hasta", result["mesaj"], parent=self)


class PatientDetailPage(Page):
    title = "Hasta Detayı"
    subtitle = "Klinik geçmiş, ölçümler ve doktor notları."
    icon = "user"
    accent = theme.CYAN

    def __init__(self, parent, app, patient_id: str, back: str = "patients") -> None:
        try:
            self.patient_id = ObjectId(patient_id) if isinstance(patient_id, str) else patient_id
        except Exception:
            self.patient_id = patient_id
        self.back = back
        super().__init__(parent, app)

    def build(self) -> None:
        db = get_db()
        if db is None:
            notice(self.body, "Hasta bilgilerine ulaşılamadı.", accent=theme.BLOOD).pack(fill="x")
            return
        self.profile = ref.find_patient_profile(db, self.patient_id) or {}
        self.user = db[B.USERS].find_one({"_id": self.profile.get("user_id")}) or {}
        name = f"{self.user.get('ad', '')} {self.user.get('soyad', '')}".strip() or "Hasta"
        back_label = "← Uyarılar" if self.back == "alerts" else "← Hastalarım"
        latest = records_db.recent_measurements(self.patient_id, limit=1)
        _, avatar_color = _status(latest[0]["kan_sekeri_degeri"] if latest else None)
        self.page_head(
            name,
            f"T.C. {self.user.get('tc_kimlik_no') or '—'}  ·  "
            f"{self.profile.get('diyabet_tipi') or 'Diyabet tipi yok'}  ·  "
            f"Tanı {_date(self.profile.get('tani_tarihi'))}",
            avatar=(_initials(self.user.get("ad"), self.user.get("soyad")), avatar_color),
            actions=(
                theme.button(self, back_label, lambda: self.app.navigate(self.back), style="ghost"),
                theme.button(
                    self, "Rapor Al",
                    lambda: self.app.navigate("reports", patient_id=self.patient_id),
                    style="primary",
                ),
            ),
        )
        self._build_summary()
        self._build_tabs()

    def _build_summary(self) -> None:
        measurement = records_db.recent_measurements(self.patient_id, limit=1)
        latest = measurement[0] if measurement else None
        avg = records_db.average_glucose(self.patient_id, 7)
        scores = records_db.compliance_history(self.patient_id, limit=1)
        score = scores[0]["genel_uyum_skoru"] if scores else None
        db = get_db()
        alerts = (
            db[B.ALERTS].count_documents({"hasta_id": self.patient_id, "okundu": False})
            if db is not None else 0
        )
        box = tk.Frame(self.body, bg=theme.APP_BG)
        box.pack(fill="x", pady=(0, 12))
        cards = [
            metric(box, icon="droplet", title="Son Kan Şekeri",
                   value=_value_text(latest["kan_sekeri_degeri"]) if latest else "—",
                   accent=theme.BLOOD, note=_when(latest["olcum_zamani"]) if latest else "Kayıt yok"),
            metric(box, icon="trend", title="7 Gün Ortalaması",
                   value=_value_text(avg), accent=theme.PRIMARY, note="Geçerli ölçümler"),
            metric(box, icon="target", title="Uyum Skoru",
                   value=f"%{score:.0f}" if score is not None else "—",
                   accent=theme.GREEN if (score or 0) >= 75 else theme.AMBER,
                   note="Son hesaplama"),
            metric(box, icon="alert", title="Açık Uyarı", value=alerts,
                   accent=theme.AMBER if alerts else theme.GREEN,
                   note="Okunmamış" if alerts else "Temiz"),
        ]
        stat_grid(box, cards, columns=4)

        target = (
            f"{self.profile.get('hedef_kan_sekeri_min', 70)} – "
            f"{self.profile.get('hedef_kan_sekeri_max', 140)} mg/dL"
        )
        info = card(self.body, padx=16, pady=11, accent=theme.CYAN)
        info.pack(fill="x", pady=(0, 12))
        line = tk.Frame(info.body, bg=theme.CARD_BG)
        line.pack(fill="x")
        icons.badge(line, "target", theme.CYAN, size=34, bg=theme.CARD_BG).pack(side="left", padx=(0, 10))
        tk.Label(
            line, text=f"Hedef aralık: {target}", font=theme.font(10, True),
            bg=theme.CARD_BG, fg=theme.TEXT,
        ).pack(side="left")
        tk.Label(
            line, text="  Kişiye özel takip aralığı", font=theme.font(8),
            bg=theme.CARD_BG, fg=theme.MUTED,
        ).pack(side="left")

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self.body, takefocus=False)
        self.notebook.pack(fill="both", expand=True)
        self._tab_measure()
        self._tab_lifestyle()
        self._tab_symptoms()
        self._tab_insulin()
        self._tab_notes()

    def _tab_measure(self) -> None:
        tab = tk.Frame(self.notebook, bg=theme.APP_BG)
        self.notebook.add(tab, text="Kan Şekeri")
        chart_box = card(tab, padx=8, pady=8, accent=theme.BLOOD)
        chart_box.pack(fill="both", expand=True, padx=0, pady=(0, 8))
        try:
            series = records_db.measurement_series(self.patient_id, limit=100)
            charts.plot_blood_sugar_trend(
                chart_box.body, series,
                target_range=(
                    self.profile.get("hedef_kan_sekeri_min", 70),
                    self.profile.get("hedef_kan_sekeri_max", 140),
                ),
            )
        except Exception:
            notice(chart_box.body, "Grafik çizilemedi.", accent=theme.BLOOD).pack(fill="x")
        table_card = card(tab, padx=12, pady=10)
        table_card.pack(fill="both", expand=True)
        tree, wrap = table(
            table_card.body,
            ("tarih", "saat", "tip", "deger", "gecerli", "not"),
            ("Tarih", "Saat", "Öğün", "Kan Şekeri", "Ortalamaya Dahil", "Not"),
            (95, 65, 85, 120, 140, 260), height=7,
        )
        wrap.pack(fill="both", expand=True)
        for idx, m in enumerate(records_db.recent_measurements(self.patient_id, limit=50)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                _date(m["olcum_tarihi"]), m["olcum_saati"].strftime("%H:%M") if m["olcum_saati"] else "—",
                m["olcum_tipi"], f"{m['kan_sekeri_degeri']:g} mg/dL",
                "Evet" if m["gecerli_olcum"] else "Hayır", m["notlar"] or "—",
            ))

    def _tab_lifestyle(self) -> None:
        tab = tk.Frame(self.notebook, bg=theme.APP_BG)
        self.notebook.add(tab, text="Diyet / Egzersiz")
        top = tk.Frame(tab, bg=theme.APP_BG)
        top.pack(fill="x", pady=(0, 8))
        diet = records_db.active_diet_plan(self.patient_id)
        exercise = records_db.active_exercise_plan(self.patient_id)
        for idx, (title, value, sub, accent, icon_name) in enumerate((
            ("Aktif Diyet", diet["diyet_adi"] if diet else "Plan yok",
             (diet or {}).get("aciklama") or "Doktorunuz henüz diyet planı atamadı.",
             theme.GREEN, "apple"),
            ("Aktif Egzersiz", exercise["egzersiz_adi"] if exercise else "Plan yok",
             f"Haftada {exercise['haftalik_siklik']} kez · {exercise['sure_dakika']} dk"
             if exercise else "Doktorunuz henüz egzersiz planı atamadı.",
             theme.ORANGE, "dumbbell"),
        )):
            c = card(top, padx=16, pady=13, accent=accent)
            c.pack(side="left", fill="both", expand=True, padx=(0, 6) if idx == 0 else (6, 0))
            row = tk.Frame(c.body, bg=theme.CARD_BG)
            row.pack(fill="x")
            icons.badge(row, icon_name, accent, size=36, bg=theme.CARD_BG).pack(side="left", padx=(0, 10))
            tk.Label(row, text=title, font=theme.font(8, True), bg=theme.CARD_BG,
                     fg=theme.MUTED).pack(anchor="w")
            tk.Label(row, text=value, font=theme.font(12, True), bg=theme.CARD_BG,
                     fg=theme.TEXT).pack(anchor="w")
            tk.Label(c.body, text=sub, font=theme.font(8), bg=theme.CARD_BG,
                     fg=theme.MUTED, anchor="w", wraplength=450, justify="left").pack(
                anchor="w", pady=(8, 0)
            )
        table_card = card(tab, padx=12, pady=10)
        table_card.pack(fill="both", expand=True)
        tree, wrap = table(
            table_card.body,
            ("tarih", "diyet", "egz", "sure"),
            ("Tarih", "Diyet Uygulandı", "Egzersiz Yapıldı", "Süre"),
            (110, 190, 190, 110), height=8,
        )
        wrap.pack(fill="both", expand=True)
        for idx, row in enumerate(records_db.diet_exercise_history(self.patient_id, limit=45)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                _date(row["takip_tarihi"]),
                "Evet" if row["diyet_uygulandimi"] else "—" if row["diyet_uygulandimi"] is None else "Hayır",
                "Evet" if row["egzersiz_yapildimi"] else "—" if row["egzersiz_yapildimi"] is None else "Hayır",
                f"{row['sure_dakika']} dk" if row["sure_dakika"] is not None else "—",
            ))

    def _tab_symptoms(self) -> None:
        tab = tk.Frame(self.notebook, bg=theme.APP_BG)
        self.notebook.add(tab, text="Belirtiler")
        outer = card(tab, padx=12, pady=10)
        outer.pack(fill="both", expand=True)
        tree, wrap = table(
            outer.body,
            ("tarih", "belirti", "siddet", "kaydeden", "not"),
            ("Tarih", "Belirti", "Şiddet", "Kaydeden", "Not"),
            (100, 200, 100, 170, 320), height=12,
        )
        wrap.pack(fill="both", expand=True)
        for idx, row in enumerate(records_db.symptom_history(self.patient_id, limit=60)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                _date(row["kayit_tarihi"]), row["belirti_adi"],
                row["siddet_seviyesi"] or "—", row["kaydeden"], row["notlar"] or "—",
            ))
        if not tree.get_children():
            empty(outer.body, "Belirti kaydı bulunmuyor.", icon="bandage").pack(
                fill="both", expand=True
            )

    def _tab_insulin(self) -> None:
        tab = tk.Frame(self.notebook, bg=theme.APP_BG)
        self.notebook.add(tab, text="İnsülin")
        outer = card(tab, padx=12, pady=10)
        outer.pack(fill="both", expand=True)
        tree, wrap = table(
            outer.body,
            ("tarih", "tip", "ort", "doz", "uygulandi"),
            ("Tarih", "Öğün", "Ortalama", "Önerilen Doz", "Uygulandı"),
            (110, 110, 140, 140, 120), height=11,
        )
        wrap.pack(fill="both", expand=True)
        for idx, row in enumerate(records_db.insulin_history(self.patient_id, limit=50)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                _date(row["tarih"]), row["olcum_tipi"],
                f"{row['ortalama_kan_sekeri']:g} mg/dL",
                f"{row['onerilen_doz_ml']:g} ml",
                "Evet" if row["uygulandi"] else "Hayır",
            ))

    def _tab_notes(self) -> None:
        tab = tk.Frame(self.notebook, bg=theme.APP_BG)
        self.notebook.add(tab, text="Notlar")
        form_card = card(tab, padx=14, pady=12, accent=theme.TEAL)
        form_card.pack(fill="x", pady=(0, 8))
        section(form_card.body, "Yeni Doktor Notu", "Hasta ile paylaşabilir veya yalnızca doktor görünürlüğünde bırakabilirsiniz.",
                icon="report", accent=theme.TEAL)
        row = tk.Frame(form_card.body, bg=theme.CARD_BG)
        row.pack(fill="x")
        field_label(row, "Başlık").pack(anchor="w")
        self.note_title = theme.entry(row, width=34)
        self.note_title.pack(side="left", fill="x", expand=True, pady=(4, 0))
        field_label(row, "Önem").pack(side="left", padx=(10, 0), anchor="s")
        self.note_importance = tk.StringVar(value="Orta")
        imp = tk.OptionMenu(row, self.note_importance, *IMPORTANCE)
        imp.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                      activebackground=theme.PRIMARY_DARK, relief="flat",
                      highlightthickness=1, highlightbackground=theme.BORDER, width=9)
        imp.pack(side="left", padx=(10, 0), pady=(4, 0))
        field_label(row, "Görünürlük").pack(side="left", padx=(10, 0), anchor="s")
        self.note_visibility = tk.StringVar(value="Doktor ve Hasta")
        vis = tk.OptionMenu(row, self.note_visibility, *VISIBILITY)
        vis.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                      activebackground=theme.PRIMARY_DARK, relief="flat",
                      highlightthickness=1, highlightbackground=theme.BORDER, width=16)
        vis.pack(side="left", padx=(10, 0), pady=(4, 0))
        self.note_text = tk.Text(
            form_card.body, height=3, font=theme.font(9), bg=theme.DARK_FIELD,
            fg=theme.TEXT, insertbackground=theme.TEXT, relief="flat",
            highlightthickness=1, highlightbackground=theme.BORDER, padx=8, pady=6,
        )
        self.note_text.pack(fill="x", pady=(8, 8))
        theme.button(form_card.body, "Notu Kaydet", self._save_note, style="primary").pack(anchor="e")

        list_card = card(tab, padx=14, pady=10)
        list_card.pack(fill="both", expand=True)
        self.notes_box = tk.Frame(list_card.body, bg=theme.CARD_BG)
        self.notes_box.pack(fill="both", expand=True)
        self._render_notes()

    def _render_notes(self) -> None:
        for widget in self.notes_box.winfo_children():
            widget.destroy()
        notes = doctors_db.doctor_notes_list(state.session.doctor_id, self.patient_id)
        if not notes:
            empty(self.notes_box, "Henüz doktor notu yok.", icon="report").pack(
                fill="both", expand=True
            )
            return
        for note in notes:
            row = tk.Frame(self.notes_box, bg=theme.CARD_2, highlightbackground=theme.BORDER,
                           highlightthickness=1)
            row.pack(fill="x", pady=3)
            top = tk.Frame(row, bg=theme.CARD_2)
            top.pack(fill="x", padx=12, pady=(8, 2))
            tk.Label(top, text=note["not_basligi"], font=theme.font(9, True),
                     bg=theme.CARD_2, fg=theme.TEXT).pack(side="left")
            badge(top, note.get("onem_seviyesi") or "Orta", theme.AMBER).pack(side="right")
            tk.Label(row, text=note["not_icerigi"], font=theme.font(8), bg=theme.CARD_2,
                     fg=theme.MUTED, anchor="w", wraplength=950, justify="left").pack(
                fill="x", padx=12, pady=(0, 8)
            )

    def _save_note(self) -> None:
        title = self.note_title.get().strip()
        content = self.note_text.get("1.0", "end").strip()
        if not title or not content:
            messagebox.showinfo("Not", "Başlık ve not içeriği boş olamaz.", parent=self)
            return
        doctors_db.save_doctor_note(
            state.session.doctor_id, self.patient_id, title, content,
            self.note_importance.get(), self.note_visibility.get(),
        )
        self.note_title.delete(0, tk.END)
        self.note_text.delete("1.0", "end")
        self._render_notes()
