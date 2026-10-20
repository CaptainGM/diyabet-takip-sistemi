"""Doktor — hasta listesi, filtreleme, hasta detayı ve yeni hasta ekleme."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import tkcalendar

from ... import state, theme
from ...db import doctors as doctors_db
from ...db import records as records_db
from ...db import reference as ref
from ...db.client import get_db
from .. import charts, helpers

MEAL_TIPS = ("Sabah", "Öğle", "İkindi", "Akşam", "Gece")


# ---------------------------------------------------------------------------
# Hasta listesi + filtreleme
# ---------------------------------------------------------------------------
def show_doctor_patients_with_filters() -> None:
    win = helpers.modal_window(None, "Hastalarım ve Filtreleme", "980x640")
    helpers.header(win, "👥 Hastalarım", "Ad/TC son kan şekeri aralığı ve belirtiye göre filtreleyin")

    # --- Filtre kartı -------------------------------------------------------
    filters = theme.frame(win, card=True)
    filters.pack(fill="x", padx=16, pady=(0, 10))
    inner = theme.frame(filters)
    inner.pack(padx=12, pady=10)

    theme.label(inner, "Ad / Soyad / T.C.:", 9).grid(row=0, column=0, sticky="w")
    name_entry = theme.entry(inner, width=20)
    name_entry.grid(row=0, column=1, padx=(4, 14), pady=6)

    theme.label(inner, "Min KŞ:", 9).grid(row=0, column=2, sticky="e")
    min_entry = theme.entry(inner, width=7)
    min_entry.grid(row=0, column=3, padx=(4, 14))

    theme.label(inner, "Max KŞ:", 9).grid(row=0, column=4, sticky="e")
    max_entry = theme.entry(inner, width=7)
    max_entry.grid(row=0, column=5, padx=(4, 14))

    theme.label(inner, "Semptom:", 9).grid(row=0, column=6, sticky="e")
    symptom_var = tk.StringVar(win)
    symptom_options = ref.get_symptom_options()
    symptom_menu = tk.OptionMenu(
        inner, symptom_var, *(["(Tümü)"] + [s[1] for s in symptom_options])
    )
    symptom_menu.config(width=22, font=theme.font(9), relief="flat")
    symptom_menu.grid(row=0, column=7, padx=(4, 0))

    # --- Liste -------------------------------------------------------------
    tree_frame = theme.frame(win, card=True)
    tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    columns = ("ad", "tc", "tip", "son_kan_sekeri", "son_belirtiler", "tani")
    tree = ttk.Treeview(
        tree_frame, columns=columns, show="headings", height=13, style="Card.Treeview"
    )
    headings = (
        ("ad", "Ad Soyad", 190),
        ("tc", "T.C. Kimlik No", 120),
        ("tip", "Diyabet Tipi", 110),
        ("son_kan_sekeri", "Son Kan Şekeri", 120),
        ("son_belirtiler", "Son Belirtiler", 220),
        ("tani", "Tanı Tarihi", 110),
    )
    for key, text, width in headings:
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    patients_by_id: dict = {}

    def refresh() -> None:
        min_bs = _parse_float(min_entry.get())
        max_bs = _parse_float(max_entry.get())
        selected = symptom_var.get()
        symptom_id = None
        for sid, sname in symptom_options:
            if sname == selected:
                symptom_id = sid
                break
        try:
            patients = doctors_db.search_patients_for_doctor(
                state.session.doctor_id,
                name_filter=name_entry.get(),
                min_bs=min_bs,
                max_bs=max_bs,
                symptom_id=symptom_id,
            )
        except Exception as exc:
            messagebox.showerror("Hata", f"Liste yüklenemedi: {exc}", parent=win)
            return
        patients_by_id.clear()
        rows = []
        for p in patients:
            patients_by_id[str(p["hasta_id"])] = p
            son = "—" if p["son_kan_sekeri"] is None else f"{p['son_kan_sekeri']:g} mg/dL"
            rows.append(
                (
                    str(p["hasta_id"]),
                    f"{p['ad']} {p['soyad']}",
                    p["tc_kimlik_no"] or "",
                    p["diyabet_tipi"] or "",
                    son,
                    p["son_belirtiler"] or "—",
                    helpers.date_label(p.get("tani_tarihi")),
                )
            )
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", iid=row[0], values=row[1:])

    def open_detail(_event=None) -> None:
        selection = tree.focus()
        if not selection:
            return
        show_patient_detail_window(patients_by_id[selection], on_changed=refresh)

    theme.button(filters, "Yenile", refresh, style="ghost").pack(side="bottom", pady=(0, 10))
    theme.button(filters, "Hasta Detayını Aç", open_detail, style="primary").pack(
        side="bottom", pady=10
    )

    name_entry.bind("<Return>", lambda e: refresh())
    tree.bind("<Double-1>", open_detail)
    refresh()


def _parse_float(text: str) -> float | None:
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Hasta detayı (sekmeli pencere) — hem liste hem uyarı/kritik ekranlarından
# ---------------------------------------------------------------------------
def show_patient_detail_window(patient: dict, on_changed=None) -> None:
    hasta_id = patient["hasta_id"]
    db = get_db()
    if db is None:
        return
    profile = ref.find_patient_profile(db, hasta_id) or patient
    title = f"{profile['ad']} {profile['soyad']} — Hasta Detayı"

    win = helpers.modal_window(None, title, "960x680")
    helpers.header(
        win,
        f"🩺 {profile['ad']} {profile['soyad']}",
        f"T.C.: {profile.get('tc_kimlik_no') or '—'} · "
        f"Diyabet Tipi: {profile.get('diyabet_tipi') or '—'} · "
        f"Tanı: {helpers.date_label(profile.get('tani_tarihi'))}",
    )

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    # --- Sekme 1: Son ölçümler + grafik -------------------------------------
    tab_meas = theme.frame(notebook, card=True)
    notebook.add(tab_meas, text="📈 Kan Şekeri")

    chart_box = theme.frame(tab_meas, card=True)
    chart_box.pack(fill="both", padx=12, pady=10)
    charts.plot_blood_sugar_trend(
        chart_box,
        records_db.measurement_series(hasta_id, limit=100),
        target_range=(profile.get("hedef_kan_sekeri_min", 70), profile.get("hedef_kan_sekeri_max", 110)),
    )

    tree, _ = _make_tree(
        tab_meas, ("tarih", "saat", "tip", "deger", "gecerli", "not"),
        ("Tarih", "Saat", "Ölçüm Tipi", "Kan Şekeri", "Geçerli?", "Notlar"),
        (100, 70, 90, 110, 80, 180),
    )
    for m in records_db.recent_measurements(hasta_id, limit=50):
        tree.insert(
            "",
            "end",
            values=(
                helpers.date_label(m["olcum_tarihi"]),
                m["olcum_saati"].strftime("%H:%M") if m["olcum_saati"] else "—",
                m["olcum_tipi"],
                f"{m['kan_sekeri_degeri']:g} mg/dL",
                "Evet" if m["gecerli_olcum"] else "Hayır",
                m["notlar"] or "—",
            ),
        )

    # --- Sekme 2: Diyet / egzersiz geçmişi -----------------------------------
    tab_plan = theme.frame(notebook, card=True)
    notebook.add(tab_plan, text="🥗 Diyet/Egzersiz")

    plan_info = theme.frame(tab_plan, card=True)
    plan_info.pack(fill="x", padx=12, pady=10)
    diet_plan = records_db.active_diet_plan(hasta_id)
    ex_plan = records_db.active_exercise_plan(hasta_id)
    theme.label(
        plan_info,
        "Aktif Diyet: " + (diet_plan["diyet_adi"] if diet_plan else "Kayıt yok"),
        10, bold=True,
    ).pack(anchor="w", padx=12, pady=(8, 0))
    if diet_plan:
        theme.muted_label(
            plan_info,
            f"{helpers.date_label(diet_plan['baslangic_tarihi'])} → "
            f"{helpers.date_label(diet_plan['bitis_tarihi'])}:"
            f" {diet_plan['aciklama'] or ''}",
            9,
        ).pack(anchor="w", padx=12, pady=(0, 6))
    theme.label(
        plan_info,
        "Aktif Egzersiz: " + (ex_plan["egzersiz_adi"] if ex_plan else "Kayıt yok"),
        10, bold=True,
    ).pack(anchor="w", padx=12, pady=(4, 0))
    if ex_plan:
        theme.muted_label(
            plan_info,
            f"Haftada {ex_plan['haftalik_siklik']} kez / {ex_plan['sure_dakika']} dk · "
            f"{helpers.date_label(ex_plan['baslangic_tarihi'])} → "
            f"{helpers.date_label(ex_plan['bitis_tarihi'])}",
            9,
        ).pack(anchor="w", padx=12, pady=(0, 8))

    tree, _ = _make_tree(
        tab_plan, ("tarih", "diyet", "egz", "sure"),
        ("Tarih", "Diyet Uygulandı", "Egzersiz Yapıldı", "Süre (dk)"),
        (110, 160, 160, 110),
    )
    for row in records_db.diet_exercise_history(hasta_id, limit=45):
        tree.insert(
            "",
            "end",
            values=(
                helpers.date_label(row["takip_tarihi"]),
                _yes_no(row["diyet_uygulandimi"]),
                _yes_no(row["egzersiz_yapildimi"]),
                row["sure_dakika"] if row["sure_dakika"] is not None else "—",
            ),
        )

    # --- Sekme 3: Belirtiler -------------------------------------------------
    tab_sym = theme.frame(notebook, card=True)
    notebook.add(tab_sym, text="🤕 Belirtiler")
    tree, _ = _make_tree(
        tab_sym, ("tarih", "belirti", "siddet", "kaydeden", "not"),
        ("Tarih", "Belirti", "Şiddet", "Kaydeden", "Not"),
        (95, 210, 90, 170, 260),
    )
    for row in records_db.symptom_history(hasta_id, limit=60):
        tree.insert(
            "",
            "end",
            values=(
                helpers.date_label(row["kayit_tarihi"]),
                row["belirti_adi"],
                row["siddet_seviyesi"] or "—",
                row["kaydeden"],
                row["notlar"] or "—",
            ),
        )

    # --- Sekme 4: İnsülin önerileri ------------------------------------------
    tab_ins = theme.frame(notebook, card=True)
    notebook.add(tab_ins, text="💉 İnsülin")
    tree, _ = _make_tree(
        tab_ins, ("tarih", "tip", "ort", "doz", "uygulandi"),
        ("Tarih", "Ölçüm Tipi", "Ortalama KŞ", "Önerilen Doz", "Uygulandı mı"),
        (100, 100, 120, 120, 120),
    )
    for row in records_db.insulin_history(hasta_id, limit=50):
        tree.insert(
            "",
            "end",
            values=(
                helpers.date_label(row["tarih"]),
                row["olcum_tipi"],
                f"{row['ortalama_kan_sekeri']:g} mg/dL",
                f"{row['onerilen_doz_ml']:g} ml",
                "Evet" if row["uygulandi"] else "Hayır",
            ),
        )

    # --- Sekme 5: Doktor notları ---------------------------------------------
    tab_notes = theme.frame(notebook, card=True)
    notebook.add(tab_notes, text="📝 Notlar")
    notes_list = records_db.shared_doctor_notes(hasta_id)
    if not notes_list:
        theme.muted_label(tab_notes, "Görünür doktor notu yok.", 10).pack(pady=16)
    for note in notes_list:
        note_card = theme.frame(tab_notes, card=True)
        note_card.pack(fill="x", padx=14, pady=6)
        theme.label(
            note_card,
            f"{note['not_basligi']}  ({note['onem_seviyesi']} · "
            f"{helpers.date_label(note['olusturma_tarihi'])})",
            10, bold=True,
        ).pack(anchor="w", padx=10, pady=(8, 2))
        theme.label(note_card, note["not_icerigi"], 9).pack(anchor="w", padx=10, pady=(0, 8))

    win.protocol("WM_DELETE_WINDOW", lambda: _close(win, on_changed))


def _close(win, on_changed) -> None:
    win.destroy()
    if on_changed:
        on_changed()


def _yes_no(value) -> str:
    if value is None:
        return "Kayıt yok"
    return "Evet" if value else "Hayır"


def _make_tree(parent, columns, headings, widths):
    """Card içine Treeview kurar; (tree, frame) döner."""
    frame = theme.frame(parent, card=True)
    frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=9, style="Card.Treeview")
    for key, text, width in zip(columns, headings, widths, strict=False):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    return tree, frame


# ---------------------------------------------------------------------------
# Yeni hasta ekleme
# ---------------------------------------------------------------------------
DIABET_TYPES = ("Tip 1", "Tip 2", "Gestasyonel", "Ön Diyabet")

def add_patient_screen() -> None:
    win = helpers.modal_window(None, "Yeni Hasta Ekle", "560x640")
    helpers.header(win, "➕ Yeni Hasta Ekle", "Kullanıcı + hasta profili birlikte oluşturulur")

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=18, pady=(0, 12))
    form = theme.frame(card)
    form.pack(padx=10, pady=10)

    tc_entry = theme.entry(form)
    ad_entry = theme.entry(form)
    soyad_entry = theme.entry(form)
    eposta_entry = theme.entry(form)
    sifre_entry = theme.entry(form, show="•")
    dogum_entry = tkcalendar.DateEntry(
        form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday"
    )
    cinsiyet_menu, cinsiyet_var = helpers.dropdown(form, ("Erkek", "Kadın"))
    tip_menu, tip_var = helpers.dropdown(form, DIABET_TYPES)
    tani_entry = tkcalendar.DateEntry(
        form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday"
    )
    target_min = tk.Spinbox(form, from_=40, to=200, width=10, font=theme.font(10))
    target_min.delete(0, tk.END)
    target_min.insert(0, 70)
    target_max = tk.Spinbox(form, from_=80, to=400, width=10, font=theme.font(10))
    target_max.delete(0, tk.END)
    target_max.insert(0, 110)

    for row, (caption, widget) in enumerate(
        [
            ("Hasta T.C. Kimlik No (11 hane):", tc_entry),
            ("Ad:", ad_entry),
            ("Soyad:", soyad_entry),
            ("E-posta:", eposta_entry),
            ("Şifre (6-40 karakter):", sifre_entry),
            ("Doğum Tarihi:", dogum_entry),
            ("Cinsiyet:", cinsiyet_menu),
            ("Diyabet Tipi:", tip_menu),
            ("Tanı Tarihi:", tani_entry),
            ("Hedef Alt Sınır (mg/dL):", target_min),
            ("Hedef Üst Sınır (mg/dL):", target_max),
        ]
    ):
        helpers.form_row(form, row, caption, widget)

    def save() -> None:
        tc = tc_entry.get().strip()
        if not (tc.isdigit() and len(tc) == 11):
            messagebox.showerror("Hata", "T.C. Kimlik No 11 haneli sayı olmalıdır.", parent=win)
            return
        sifre = sifre_entry.get()
        if len(sifre) < 6 or len(sifre) > 40:
            messagebox.showerror("Hata", "Şifre 6-40 karakter olmalıdır.", parent=win)
            return
        hedef_min = int(target_min.get())
        hedef_max = int(target_max.get())
        if hedef_min >= hedef_max:
            messagebox.showerror(
                "Hata", "Hedef alt sınır üst sınırdan küçük olmalıdır.", parent=win
            )
            return
        result = doctors_db.add_patient(
            doktor_id=state.session.doctor_id,
            tc_no=tc,
            ad=ad_entry.get().strip(),
            soyad=soyad_entry.get().strip(),
            eposta=eposta_entry.get().strip(),
            plain_password=sifre,
            dogum_tarihi=dogum_entry.get_date(),
            cinsiyet=cinsiyet_var.get(),
            diyabet_tipi=tip_var.get(),
            tani_tarihi=tani_entry.get_date(),
            hedef_min=hedef_min,
            hedef_max=hedef_max,
        )
        if result["ok"]:
            messagebox.showinfo("Başarı", result["mesaj"], parent=win)
            win.destroy()
        else:
            messagebox.showerror("Hata", result["mesaj"], parent=win)

    theme.button(card, "Hastayı Kaydet", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)
    theme.muted_label(
        card,
        "Hasta ilk girişte kendi şifresiyle giriş yapabilir; şifre PBKDF2 ile saklanır.",
        8,
    ).pack(anchor="w", padx=16, pady=(0, 10))
