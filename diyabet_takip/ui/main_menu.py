"""Ana kabuk: sabit sol menü, üst bar ve tek pencere içinde çalışan sayfalar.

v2.4: Sol menüdeki tüm ekranlar ayrı pencere (Toplevel) olarak değil, bu
kabuğun sağ tarafındaki çalışma alanında açılır. Böylece uygulama tek pencere
olarak kalır; sayfa geçişlerinde masaüstünde ikinci bir pencere oluşmaz.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from .. import __version__, state, theme
from . import dashboard_home, icons, navigation, surface

VERSION = __version__

DOCTOR_NAV = [
    ("home", "Ana Sayfa", "home", theme.PRIMARY),
    ("patients", "Hastalarım", "users", theme.CYAN),
    ("alerts", "Uyarılar", "alert", theme.BLOOD),
    ("appointments", "Randevular", "calendar", theme.AMBER),
    ("reports", "Raporlar", "report", theme.TEAL),
    ("plans", "Plan / Belirti", "clipboard", theme.PURPLE),
    ("profile", "Profilim", "user", theme.SLATE),
]

PATIENT_NAV = [
    ("home", "Ana Sayfa", "home", theme.PRIMARY),
    ("measure", "Ölçüm Gir", "droplet", theme.BLOOD),
    ("history", "Geçmiş & Grafik", "chart", theme.CYAN),
    ("compliance", "Uyum Takibi", "target", theme.GREEN),
    ("insulin", "İnsülin", "syringe", theme.PURPLE),
    ("notifications", "Bildirimler", "bell", theme.AMBER),
    ("patient_plans", "Planlarım", "clipboard", theme.ORANGE),
    ("patient_appointments", "Randevularım", "calendar", theme.INDIGO),
    ("profile", "Profilim", "user", theme.SLATE),
]

PAGE_META = {
    "home": ("Genel Bakış", "Hasta verileriniz ve günlük özet"),
    "patients": ("Hasta Yönetimi", "Kayıtlar, riskler ve klinik detaylar"),
    "add_patient": ("Hasta Yönetimi", "Yeni hesap ve klinik profil"),
    "patient_detail": ("Hasta Yönetimi", "Klinik geçmiş ve notlar"),
    "alerts": ("Klinik Takip", "Uyarılar ve risk durumu"),
    "appointments": ("Randevu Takvimi", "Muayene planlama ve takip"),
    "reports": ("Raporlama", "Tarih aralığına göre analiz"),
    "plans": ("Tedavi Planlama", "Diyet, egzersiz ve belirti"),
    "profile": ("Hesap", "Profil ve güvenlik"),
    "measure": ("Hasta Paneli", "Günlük sağlık takibi"),
    "history": ("Hasta Paneli", "Ölçüm analizi ve geçmiş"),
    "compliance": ("Hasta Paneli", "Uyum ve yaşam takibi"),
    "insulin": ("Hasta Paneli", "İnsülin önerileri"),
    "notifications": ("Hasta Paneli", "Bildirimler"),
    "patient_plans": ("Hasta Paneli", "Tedavi planlarım"),
    "patient_appointments": ("Hasta Paneli", "Randevularım"),
    "lifestyle": ("Hasta Paneli", "Günlük takip"),
}


def _unread_count() -> int:
    try:
        if state.session.user_role == "Doktor":
            from ..db import doctors as doctors_db

            stats = doctors_db.doctor_dashboard(state.session.doctor_id)
            return int(stats.get("okunmamis_uyari_sayisi", 0))
        from ..db import patients as patients_db

        rows = patients_db.notifications_for_user(state.session.user_id, limit=200)
        return sum(1 for row in rows if not row["okundu"])
    except Exception:
        return 0


def _initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p and not p.lower().startswith("dr")]
    if not parts:
        return "DT"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _action_button_image(name: str, color: str, hover: bool):
    """Yuvarlatılmış ikon düğmesi zemini (anti-aliased, önbellekli PIL görüntüsü)."""
    base = surface.rounded_image(
        38, 38, 11, theme.CARD_HOVER if hover else theme.CARD_BG,
        border=theme.BORDER, bg=theme.APP_BG,
    ).copy()
    icon = icons.icon_image(name, 20, color)
    base.paste(icon, (9, 9), icon)
    return base


def _icon_button(parent, name: str, command, *, badge: int = 0) -> tk.Canvas:
    canvas = tk.Canvas(
        parent, width=38, height=38, bg=theme.APP_BG,
        highlightthickness=0, bd=0, cursor="hand2",
    )
    item = canvas.create_image(0, 0, anchor="nw")

    def draw(hover: bool = False) -> None:
        photo = ImageTk.PhotoImage(
            _action_button_image(name, theme.TEXT if hover else theme.MUTED, hover)
        )
        canvas.itemconfigure(item, image=photo)
        canvas._photo = photo  # GC'ye karşı referans
        canvas.delete("badge")
        if badge:
            canvas.create_oval(22, 2, 37, 17, fill=theme.BLOOD, outline=theme.APP_BG,
                               width=1, tags="badge")
            canvas.create_text(
                29, 9, text=str(min(badge, 9)) if badge <= 9 else "9+",
                font=theme.font(7, True), fill="white", tags="badge",
            )

    draw()
    canvas.bind("<Enter>", lambda _e: draw(True))
    canvas.bind("<Leave>", lambda _e: draw(False))
    canvas.bind("<Button-1>", lambda _e: command())
    return canvas


def _bell_button(parent, command, initial: int) -> tuple[tk.Canvas, dict]:
    canvas = tk.Canvas(
        parent, width=38, height=38, bg=theme.APP_BG,
        highlightthickness=0, bd=0, cursor="hand2",
    )
    item = canvas.create_image(0, 0, anchor="nw")
    state_box = {"count": initial}

    def draw(hover: bool = False) -> None:
        photo = ImageTk.PhotoImage(
            _action_button_image("bell", theme.TEXT if hover else theme.AMBER, hover)
        )
        canvas.itemconfigure(item, image=photo)
        canvas._photo = photo  # GC'ye karşı referans
        canvas.delete("dot")
        if state_box["count"]:
            canvas.create_oval(
                26, 3, 36, 13, fill=theme.BLOOD, outline=theme.APP_BG, width=2, tags="dot"
            )

    draw()
    canvas.bind("<Enter>", lambda _e: draw(True))
    canvas.bind("<Leave>", lambda _e: draw(False))
    canvas.bind("<Button-1>", lambda _e: command())
    return canvas, state_box


class _Router:
    def __init__(self, navigate) -> None:
        self.navigate = navigate


def show_main_app_screen() -> None:
    """Ana kabuğu ve sayfa yönlendiricisini kurar."""
    window = state.session.window
    for widget in window.winfo_children():
        widget.destroy()
    window.unbind("<Return>")
    window.unbind("<F11>")
    window.title(f"Diyabet Takip Sistemi · {state.session.user_role}")
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    width = min(2200, max(1180, sw - 140))
    height = min(1260, max(660, sh - 90))
    window.geometry(f"{width}x{height}")
    window.minsize(1080, 660)
    window.configure(bg=theme.APP_BG)
    window.resizable(True, True)

    window.grid_columnconfigure(0, weight=0)
    window.grid_columnconfigure(1, weight=1)
    window.grid_rowconfigure(0, weight=1)

    is_doctor = state.session.user_role == "Doktor"
    unread = _unread_count()
    nav_items = DOCTOR_NAV if is_doctor else PATIENT_NAV
    badge_labels: dict[str, tk.Label] = {}
    nav_state: dict[str, dict] = {}
    current = {"key": "home", "kwargs": {}}
    page_host = {"page": None}

    # ------------------------------------------------------------- sidebar
    sidebar = tk.Frame(window, bg=theme.SIDEBAR_BG, width=246)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)

    logo = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
    logo.pack(fill="x", padx=18, pady=(20, 14))
    brand = icons.brand_image(42)
    if brand is not None:
        brand_label = tk.Label(logo, image=brand, bg=theme.SIDEBAR_BG, bd=0)
        brand_label.image = brand
        brand_label.pack(side="left")
    else:
        icons.badge(logo, "droplet", theme.PRIMARY, size=42, bg=theme.SIDEBAR_BG).pack(side="left")
    logo_text = tk.Frame(logo, bg=theme.SIDEBAR_BG)
    logo_text.pack(side="left", padx=(11, 0))
    tk.Label(
        logo_text, text="Diyabet", font=theme.font(15, True),
        bg=theme.SIDEBAR_BG, fg=theme.TEXT,
    ).pack(anchor="w")
    tk.Label(
        logo_text, text="Takip Sistemi", font=theme.font(8),
        bg=theme.SIDEBAR_BG, fg=theme.MUTED,
    ).pack(anchor="w")

    tk.Frame(sidebar, bg=theme.BORDER, height=1).pack(fill="x", padx=18)
    tk.Label(
        sidebar, text="ÇALIŞMA ALANI", font=theme.font(7, True),
        bg=theme.SIDEBAR_BG, fg="#5c6b8a", anchor="w",
    ).pack(fill="x", padx=22, pady=(14, 6))

    def _paint_row(widget, color) -> None:
        """Gezinme satırının zeminini (ve çocuklarını) boyar."""
        if getattr(widget, "_keep_bg", False):
            return
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            _paint_row(child, color)

    def _paint_nav(item, color) -> None:
        item.set_fill(color)
        _paint_row(item.body, color)

    def _make_nav_item(key, label, icon_name, accent) -> None:
        active = key == "home"
        base = theme.PRIMARY_SOFT if active else theme.SIDEBAR_BG
        item = surface.Panel(sidebar, radius=12, fill=base, border=None, pad=4, bg=theme.SIDEBAR_BG)
        item.configure(cursor="hand2")
        item.pack(fill="x", padx=12, pady=2)
        icon_canvas = icons.icon(item.body, icon_name, size=19, color=accent, bg=base)
        icon_canvas.pack(side="left", padx=(10, 12), pady=8)
        text = tk.Label(
            item.body, text=label, font=theme.font(10, active),
            bg=base, fg=theme.TEXT if active else theme.MUTED, anchor="w",
        )
        text.pack(side="left", fill="x", expand=True)
        if key in ("alerts", "notifications"):
            badge = tk.Label(
                item.body, text=str(unread) if unread else "", font=theme.font(7, True),
                bg=theme.BLOOD, fg="white", padx=6, pady=1,
            )
            badge._keep_bg = True
            badge_labels[key] = badge
            if unread:
                badge.pack(side="right", padx=8)
        nav_state[key] = {
            "frame": item, "text": text, "icon": icon_canvas,
            "accent": accent, "active": active,
        }

        def enter():
            if not nav_state[key]["active"]:
                _paint_nav(item, theme.CARD_2)
                text.configure(fg=theme.TEXT)

        def leave():
            is_active = nav_state[key]["active"]
            _paint_nav(item, theme.PRIMARY_SOFT if is_active else theme.SIDEBAR_BG)
            text.configure(fg=theme.TEXT if is_active else theme.MUTED)

        dashboard_home._bind_hover(item, enter, leave)
        dashboard_home._bind_tree(item, "<Button-1>", lambda _e, k=key: route(k))

    for key, label, icon_name, accent in nav_items:
        _make_nav_item(key, label, icon_name, accent)

    tk.Frame(sidebar, bg=theme.SIDEBAR_BG).pack(fill="both", expand=True)

    user_card = surface.Panel(sidebar, radius=16, fill=theme.CARD_BG, border=theme.BORDER,
                              pad=12, bg=theme.SIDEBAR_BG)
    user_card.configure(cursor="hand2")
    user_card.pack(fill="x", padx=12, pady=(8, 8))
    user_inner = tk.Frame(user_card.body, bg=theme.CARD_BG)
    user_inner.pack(fill="x")
    av_color = theme.TEAL if is_doctor else theme.BLOOD
    surface.Avatar(
        user_inner, _initials(state.session.full_name), av_color, size=36, bg=theme.CARD_BG,
    ).pack(side="left")
    info = tk.Frame(user_inner, bg=theme.CARD_BG)
    info.pack(side="left", fill="x", expand=True, padx=(9, 0))
    tk.Label(info, text=state.session.full_name, font=theme.font(9, True), bg=theme.CARD_BG,
             fg=theme.TEXT, anchor="w").pack(anchor="w")
    tk.Label(info, text=state.session.user_role or "Kullanıcı", font=theme.font(8), bg=theme.CARD_BG,
             fg=av_color, anchor="w").pack(anchor="w")
    status_dot = tk.Canvas(user_inner, width=9, height=9, bg=theme.CARD_BG, highlightthickness=0)
    status_dot.pack(side="right")
    status_dot.create_oval(2, 2, 8, 8, fill=theme.SUCCESS, outline="")
    dashboard_home._bind_tree(user_card, "<Button-1>", lambda _e: route("profile"))

    tk.Label(
        sidebar, text=f"v{VERSION}  ·  F11 tam ekran", font=theme.font(8),
        bg=theme.SIDEBAR_BG, fg=theme.MUTED, anchor="w",
    ).pack(fill="x", padx=22, pady=(2, 14))

    # --------------------------------------------------------------- main
    main = tk.Frame(window, bg=theme.APP_BG)
    main.grid(row=0, column=1, sticky="nsew")

    topbar = tk.Frame(main, bg=theme.APP_BG, height=78)
    topbar.pack(side="top", fill="x")
    topbar.pack_propagate(False)
    tk.Frame(topbar, bg=theme.BORDER, height=1).pack(side="bottom", fill="x")

    title_box = tk.Frame(topbar, bg=theme.APP_BG)
    title_box.pack(side="left", padx=(24, 0), pady=(12, 0))
    title_label = tk.Label(
        title_box, text="Genel Bakış", font=theme.font(17, True),
        bg=theme.APP_BG, fg=theme.TEXT, anchor="w",
    )
    title_label.pack(anchor="w")
    subtitle_label = tk.Label(
        title_box, text=PAGE_META["home"][1], font=theme.font(9),
        bg=theme.APP_BG, fg=theme.MUTED, anchor="w",
    )
    subtitle_label.pack(anchor="w", pady=(2, 0))

    right = tk.Frame(topbar, bg=theme.APP_BG)
    right.pack(side="right", padx=(0, 18), pady=13)

    logout = theme.button(right, "Çıkış Yap", navigation.go_login, style="ghost")
    logout.pack(side="right", padx=(10, 0))
    user = tk.Frame(right, bg=theme.APP_BG, cursor="hand2")
    user.pack(side="right", padx=(8, 0))
    surface.Avatar(
        user, _initials(state.session.full_name), av_color, size=38, bg=theme.APP_BG,
    ).pack(side="left", padx=(0, 9))
    user_text = tk.Frame(user, bg=theme.APP_BG)
    user_text.pack(side="left")
    tk.Label(user_text, text=state.session.full_name, font=theme.font(9, True), bg=theme.APP_BG,
             fg=theme.TEXT, anchor="e").pack(anchor="e")
    tk.Label(user_text, text=state.session.user_role, font=theme.font(8), bg=theme.APP_BG,
             fg=av_color, anchor="e").pack(anchor="e")
    dashboard_home._bind_tree(user, "<Button-1>", lambda _e: route("profile"))

    def _toggle_fullscreen(_event=None):
        top = window.winfo_toplevel()
        top.attributes("-fullscreen", not top.attributes("-fullscreen"))
        return "break"

    fullscreen = _icon_button(right, "fullscreen", _toggle_fullscreen)
    fullscreen.pack(side="right", padx=(6, 0))
    refresh = _icon_button(right, "refresh", lambda: refresh_current())
    refresh.pack(side="right", padx=(6, 0))
    bell, bell_state = _bell_button(
        right, lambda: route("alerts" if is_doctor else "notifications"), unread,
    )
    bell.pack(side="right")
    window.bind("<F11>", _toggle_fullscreen)

    footer = tk.Frame(main, bg=theme.CARD_BG, height=28)
    footer.pack(side="bottom", fill="x")
    footer.pack_propagate(False)
    tk.Label(
        footer, text=f"Diyabet Takip Sistemi  ·  v{VERSION}",
        font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED,
    ).pack(side="left", padx=20)
    tk.Label(
        footer, text="Sağlığınız bizim için önemli", font=theme.font(8),
        bg=theme.CARD_BG, fg=theme.MUTED,
    ).pack(side="right", padx=(2, 20))

    content_wrap = tk.Frame(main, bg=theme.APP_BG)
    content_wrap.pack(fill="both", expand=True)
    content_wrap.grid_columnconfigure(0, weight=1)
    content_wrap.grid_rowconfigure(0, weight=1)
    canvas = tk.Canvas(content_wrap, bg=theme.APP_BG, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(content_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    scrollbar.grid_remove()
    inner = tk.Frame(canvas, bg=theme.APP_BG)
    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _sync_scroll(_event=None) -> None:
        canvas.update_idletasks()
        target_height = max(inner.winfo_reqheight(), canvas.winfo_height())
        if abs(inner.winfo_height() - target_height) > 2:
            canvas.itemconfigure(inner_id, height=target_height)
            canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        need = inner.winfo_reqheight() > canvas.winfo_height() + 2
        if need and not scrollbar.winfo_ismapped():
            scrollbar.grid(row=0, column=1, sticky="ns")
        elif not need and scrollbar.winfo_ismapped():
            scrollbar.grid_remove()

    def _on_canvas_configure(event) -> None:
        canvas.itemconfigure(inner_id, width=event.width)
        _sync_scroll()

    def _on_wheel(event) -> None:
        if inner.winfo_reqheight() > canvas.winfo_height() + 2:
            canvas.yview_scroll(int(-event.delta / 120), "units")

    def _bind_wheel(widget) -> None:
        widget.bind("<MouseWheel>", _on_wheel)
        for child in widget.winfo_children():
            _bind_wheel(child)

    canvas.bind("<Configure>", _on_canvas_configure)
    inner.bind("<Configure>", lambda _e: _sync_scroll())

    def _set_active(key: str) -> None:
        for nav_key, item in nav_state.items():
            is_active = nav_key == key
            item["active"] = is_active
            _paint_nav(item["frame"], theme.PRIMARY_SOFT if is_active else theme.SIDEBAR_BG)
            item["text"].configure(
                fg=theme.TEXT if is_active else theme.MUTED,
                font=theme.font(10, is_active),
            )

    def _set_title(title: str, subtitle: str) -> None:
        title_label.configure(text=title)
        subtitle_label.configure(text=subtitle)

    def _refresh_badges() -> None:
        count = _unread_count()
        bell_state["count"] = count
        bell.event_generate("<Leave>")
        for label in badge_labels.values():
            label.configure(text=str(count) if count else "")
            if count and not label.winfo_ismapped():
                label.pack(side="right", padx=8)
            elif not count and label.winfo_ismapped():
                label.pack_forget()

    def _error_page(message: str) -> None:
        from .pages.base import notice

        for widget in inner.winfo_children():
            widget.destroy()
        page = tk.Frame(inner, bg=theme.APP_BG)
        page.pack(fill="both", expand=True, padx=24, pady=24)
        notice(page, message, accent=theme.BLOOD, icon="alert").pack(fill="x")
        theme.button(page, "Ana sayfaya dön", lambda: route("home"), style="primary").pack(
            anchor="w", pady=(14, 0)
        )

    def _build_page(key: str, **kwargs):
        from .pages.doctor import (
            AddPatientPage,
            AlertsPage,
            AppointmentsPage,
            PatientDetailPage,
            PatientsPage,
            PlansPage,
            ReportsPage,
        )
        from .pages.patient import (
            CompliancePage,
            HistoryPage,
            InsulinPage,
            LifestylePage,
            MeasurePage,
            NotificationsPage,
            PatientAppointmentsPage,
            PatientPlansPage,
        )
        from .pages.profile import ProfilePage

        if is_doctor:
            factories = {
                "patients": lambda: PatientsPage(inner, router),
                "add_patient": lambda: AddPatientPage(inner, router),
                "patient_detail": lambda: PatientDetailPage(
                    inner, router, str(kwargs.get("patient_id")), kwargs.get("back", "patients")
                ),
                "alerts": lambda: AlertsPage(inner, router, tab=kwargs.get("tab", "alerts")),
                "appointments": lambda: AppointmentsPage(inner, router),
                "reports": lambda: ReportsPage(inner, router, patient_id=kwargs.get("patient_id")),
                "plans": lambda: PlansPage(inner, router),
                "profile": lambda: ProfilePage(inner, router),
            }
        else:
            factories = {
                "measure": lambda: MeasurePage(inner, router),
                "history": lambda: HistoryPage(inner, router),
                "compliance": lambda: CompliancePage(inner, router),
                "insulin": lambda: InsulinPage(inner, router),
                "notifications": lambda: NotificationsPage(inner, router, tab=kwargs.get("tab", "all")),
                "patient_plans": lambda: PatientPlansPage(inner, router),
                "patient_appointments": lambda: PatientAppointmentsPage(inner, router),
                "lifestyle": lambda: LifestylePage(inner, router, tab=kwargs.get("tab", "diet")),
                "profile": lambda: ProfilePage(inner, router),
            }
        factory = factories.get(key)
        if factory is None:
            return None
        return factory()

    def route(key: str, **kwargs) -> None:
        if key == "home":
            for widget in inner.winfo_children():
                widget.destroy()
            current.update(key="home", kwargs={})
            dashboard_home.build_dashboard(inner, route)
            _set_active("home")
            _set_title(*PAGE_META["home"])
            page_host["page"] = None
            window.after(60, lambda: _bind_wheel(inner))
            window.after(100, _sync_scroll)
            canvas.yview_moveto(0)
            _refresh_badges()
            return
        if key == "critical":
            key = "alerts"
            kwargs.setdefault("tab", "critical")
        elif key == "diet":
            key = "lifestyle"
            kwargs.setdefault("tab", "diet")
        elif key == "symptoms":
            key = "lifestyle"
            kwargs.setdefault("tab", "symptom")
        for widget in inner.winfo_children():
            widget.destroy()
        try:
            page = _build_page(key, **kwargs)
        except Exception:  # kullanıcıya pencere çökmesi yerine görünür durum
            import os
            import traceback

            if os.environ.get("DIYABET_DEBUG"):
                traceback.print_exc()
            _error_page("Bu ekran şu anda açılamadı. Lütfen tekrar deneyin.")
            return
        if page is None:
            _error_page("Bu ekran şu anda görüntülenemiyor.")
            return
        page.pack(fill="both", expand=True)
        page_host["page"] = page
        current.update(key=key, kwargs=kwargs)
        active_key = {
            "add_patient": "patients",
            "patient_detail": "patients",
            "lifestyle": "compliance",
        }.get(key, key)
        _set_active(active_key)
        meta = PAGE_META.get(key, (page.title, page.subtitle))
        _set_title(meta[0], meta[1])
        canvas.yview_moveto(0)
        window.after(60, lambda: _bind_wheel(inner))
        window.after(100, _sync_scroll)
        _refresh_badges()

    router = _Router(route)
    window._app_router = router

    def refresh_current() -> None:
        if current["key"] == "home":
            route("home")
        else:
            route(current["key"], **current["kwargs"])

    route("home")
