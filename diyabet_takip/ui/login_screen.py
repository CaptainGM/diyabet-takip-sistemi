"""Giriş ekranı: ışıklı lacivert zemin, cam benzeri kart, giriş ve kayıt formu.

v2.4: Sol tarafta marka mesajı ve öne çıkan özellikler, sağda yuvarlatılmış
form kartı. Arka plan ve kart kenarları Pillow ile çizilir (``ui/surface.py``);
form alanları ve düğmeler Tk bileşenleridir. Pencere daraldığında sol sütun
gizlenir ve kart ortalanır.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageTk

from .. import __version__, state, theme
from ..db import bootstrap as B
from ..db.client import get_db
from ..services import auth_service
from . import icons, surface

DIYABET_TIPLERI = ("Tip 1", "Tip 2", "Gestasyonel", "Ön Diyabet")
UZMANLIKLAR = (
    "Dahiliye",
    "Endokrinoloji",
    "Aile Hekimliği",
    "İç Hastalıkları",
    "Diyetisyen",
)

PASSWORD_RULE_LABELS = (
    ("len", "En az 8 karakter"),
    ("upper", "Bir büyük harf"),
    ("lower", "Bir küçük harf"),
    ("digit", "Bir rakam"),
    ("special", "Bir özel karakter"),
)

#: Tek tıkla demo girişi; seed hesapları ``db/bootstrap.py`` içinde tanımlıdır.
DEMO_ACCOUNTS = (
    ("11111111111", "doktor123"),
    ("22222222222", "hasta123"),
    ("33333333333", "hasta123"),
    ("44444444444", "hasta123"),
    ("55555555555", "hasta123"),
)

FEATURES = (
    ("droplet", theme.BLOOD, "Takip edin", "Kan şekeri ölçümlerinizi kolayca kaydedin."),
    ("shield", theme.GREEN, "Kontrol altında tutun", "Değerlerinizi analiz edin, riskleri önceden görün."),
    ("user", theme.PURPLE, "Daha sağlıklı yaşayın", "Doktorunuzla birlikte süreci yönetin."),
)

WIDE_MIN = 1180     # bu genişliğin üstünde sol tanıtım sütunu gösterilir
MARGIN = 64
CARD_INNER = 388    # kart içerik genişliği
CARD_PAD = 26
CARD_RADIUS = 22
FIELD_ICON_COLORS = {"user": theme.CYAN, "shield": theme.GREEN, "mail": theme.PURPLE}


def _show_login_success(result: dict, on_authenticated: Callable[[], None]) -> None:
    state.session.user_id = result["user_id"]
    state.session.user_ad = result["ad"]
    state.session.user_soyad = result["soyad"]
    state.session.user_role = result["rol"]
    state.session.patient_id = result.get("patient_id")
    state.session.doctor_id = result.get("doctor_id")
    on_authenticated()


def _measure(text: str, font: tuple) -> int:
    return tkfont.Font(font=font).measure(text)


class _LoginScreen:
    """Giriş/kayıt ekranının durumu ve yerleşimi."""

    def __init__(self, window: tk.Tk, on_authenticated: Callable[[], None], start_tab: str) -> None:
        self.window = window
        self.on_authenticated = on_authenticated
        self.role = "Hasta"
        self.tip = DIYABET_TIPLERI[1]
        self.specialty = UZMANLIKLAR[0]
        self.backdrop = None
        self.images: list = []
        self.pending: str | None = None
        self.tab_buttons: dict[str, surface.Button] = {}
        self.role_buttons: dict[str, surface.Button] = {}
        self.choice_buttons: dict[str, surface.Button] = {}

        self.canvas = tk.Canvas(window, highlightthickness=0, bd=0, bg=theme.APP_BG)
        self.canvas.pack(fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=theme.CARD_BG, highlightthickness=0, bd=0)
        self.body_window = self.canvas.create_window(
            0, 0, window=self.body, anchor="nw", width=CARD_INNER
        )

        self._build_header()
        self._build_tabs()
        self.login_body = self._build_login()
        self.register_body = self._build_register()
        self._build_footer()
        self.select_tab(start_tab)

        self.canvas.bind("<Configure>", lambda _e: self.schedule())
        self.canvas.bind("<Destroy>", lambda _e: self._cancel_render())
        self.body.bind("<Configure>", lambda _e: self.schedule())
        self.schedule()

    # --- Bileşen yardımcıları ------------------------------------------------
    def _label(self, parent, text: str, *, fg: str = theme.DARK_MUTED, size: int = 8) -> tk.Label:
        return tk.Label(parent, text=text, font=theme.font(size, True), bg=parent["bg"], fg=fg)

    def _field(self, parent, icon: str, *, show: str | None = None, eye: bool = False,
               placeholder: str = ""):
        panel = surface.Panel(
            parent, radius=12, fill=theme.DARK_FIELD, border=theme.DARK_FIELD_BORDER, pad=10,
        )
        row = panel.body
        icons.icon(row, icon, size=16, color=FIELD_ICON_COLORS.get(icon, theme.DARK_MUTED),
                   bg=theme.DARK_FIELD).pack(side="left", padx=(4, 8))
        entry = tk.Entry(
            row, font=theme.font(11), bg=theme.DARK_FIELD, fg=theme.DARK_TEXT,
            insertbackground=theme.DARK_TEXT, relief="flat", bd=0, highlightthickness=0,
            show=show or "", width=28,
        )
        if eye:  # göz düğmesi girişten önce paketlenir; yoksa giriş alanı onu iter
            self._eye(row, entry).pack(side="right", padx=(6, 2))
        entry.pack(side="left", fill="x", expand=True, ipady=5)
        entry.bind("<FocusIn>", lambda _e: panel.set_border(theme.PRIMARY), add="+")
        entry.bind("<FocusOut>", lambda _e: panel.set_border(theme.DARK_FIELD_BORDER), add="+")
        panel.entry = entry
        panel.sync_hint = self._placeholder(row, entry, placeholder)
        return panel

    def _placeholder(self, row: tk.Frame, entry: tk.Entry, text: str):
        """Boş alanda soluk ipucu. Yer tutucu bir etiket olduğu için ``entry.get()`` her
        zaman gerçek değeri döndürür."""
        hint = tk.Label(row, text=text, font=theme.font(11), bg=theme.DARK_FIELD,
                        fg="#5f6f92", bd=0, cursor="xterm")

        def sync(_event=None) -> None:
            if entry.get():
                hint.place_forget()
            else:
                hint.place(in_=entry, x=1, rely=0.5, anchor="w")

        hint.bind("<Button-1>", lambda _e: entry.focus_set())
        entry.bind("<KeyRelease>", sync, add="+")
        entry.bind("<FocusIn>", sync, add="+")
        entry.bind("<FocusOut>", sync, add="+")
        sync()
        return sync

    def _eye(self, parent, entry: tk.Entry) -> tk.Canvas:
        canvas = tk.Canvas(parent, width=24, height=24, bg=theme.DARK_FIELD,
                           highlightthickness=0, bd=0, cursor="hand2")
        item = canvas.create_image(12, 12, anchor="center")

        def draw(color: str = theme.DARK_MUTED) -> None:
            name = "eye" if entry.cget("show") else "eye_off"
            photo = ImageTk.PhotoImage(icons.icon_image(name, 20, color))
            canvas.itemconfigure(item, image=photo)
            canvas._photo = photo  # GC'ye karşı referans

        def toggle(_event=None) -> None:
            entry.config(show="" if entry.cget("show") else "•")
            draw(theme.DARK_TEXT)

        canvas.bind("<Button-1>", toggle)
        canvas.bind("<Enter>", lambda _e: draw(theme.DARK_TEXT))
        canvas.bind("<Leave>", lambda _e: draw(theme.DARK_MUTED))
        draw()
        return canvas

    def _divider(self, parent, text: str) -> tk.Frame:
        row = tk.Frame(parent, bg=parent["bg"])
        tk.Frame(row, bg=theme.CARD_EDGE, height=1).pack(side="left", fill="x", expand=True)
        tk.Label(row, text=text, font=theme.font(8), bg=parent["bg"], fg=theme.DARK_MUTED,
                 padx=12).pack(side="left")
        tk.Frame(row, bg=theme.CARD_EDGE, height=1).pack(side="left", fill="x", expand=True)
        return row

    # --- Kart içeriği ----------------------------------------------------------
    def _build_header(self) -> None:
        head = tk.Frame(self.body, bg=theme.CARD_BG)
        head.pack(fill="x")
        brand = icons.brand_image(38)
        if brand is not None:
            tk.Label(head, image=brand, bg=theme.CARD_BG, bd=0).pack(side="left")
            head.brand = brand
        else:
            icons.badge(head, "droplet", theme.PRIMARY, size=38, bg=theme.CARD_BG).pack(side="left")
        text = tk.Frame(head, bg=theme.CARD_BG)
        text.pack(side="left", padx=(12, 0))
        tk.Label(text, text="Diyabet Takip Sistemi", font=theme.display(14),
                 bg=theme.CARD_BG, fg=theme.TEXT).pack(anchor="w")
        tk.Label(text, text="Hesabınızla giriş yapın", font=theme.font(9),
                 bg=theme.CARD_BG, fg=theme.DARK_MUTED).pack(anchor="w")

    def _build_tabs(self) -> None:
        tabs = tk.Frame(self.body, bg=theme.CARD_BG)
        tabs.pack(fill="x", pady=(20, 18))
        for key, text in (("login", "Giriş Yap"), ("register", "Kayıt Ol")):
            button = surface.Button(
                tabs, text, lambda k=key: self.select_tab(k), style="chip",
                height=38, font=theme.font(10, True), padx=18, bg=theme.CARD_BG,
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 6) if key == "login" else 0)
            self.tab_buttons[key] = button

    def _build_login(self) -> tk.Frame:
        box = tk.Frame(self.body, bg=theme.CARD_BG)
        self._label(box, "T.C. KİMLİK NO").pack(anchor="w", pady=(0, 6))
        self.tc_field = self._field(box, "user", placeholder="T.C. kimlik numaranızı girin")
        self.tc_field.pack(fill="x")
        self._label(box, "ŞİFRE").pack(anchor="w", pady=(14, 6))
        self.password_field = self._field(box, "shield", show="•", eye=True,
                                          placeholder="Şifrenizi girin")
        self.password_field.pack(fill="x")

        surface.Button(box, "Giriş Yap  →", self.do_login, style="primary", height=48,
                       bg=theme.CARD_BG).pack(fill="x", pady=(22, 0))
        self._divider(box, "veya").pack(fill="x", pady=(20, 14))
        self._label(box, "TEK TIKLA DEMO GİRİŞİ", fg="#9aa7c9").pack()
        chips = tk.Frame(box, bg=theme.CARD_BG)
        chips.pack(fill="x", pady=(10, 0))
        self._demo_chips(chips)

        self.tc_field.entry.bind("<Return>", self.do_login)
        self.password_field.entry.bind("<Return>", self.do_login)
        return box

    def _demo_chips(self, holder: tk.Frame) -> None:
        db = get_db()
        if db is None:
            self._label(holder, "Demo hesaplar yüklenemedi", fg=theme.DANGER).pack()
            return
        users = {
            user["tc_kimlik_no"]: user
            for user in db[B.USERS].find(
                {"tc_kimlik_no": {"$in": [tc for tc, _ in DEMO_ACCOUNTS]}}
            )
        }
        chips = [
            (users[tc]["ad"], users[tc], password)
            for tc, password in DEMO_ACCOUNTS
            if tc in users
        ]
        for index, (text, user, password) in enumerate(chips):
            row, col = divmod(index, 3)
            surface.Button(
                holder, text, lambda u=user, p=password: self.demo_login(u, p),
                style="chip", height=34, font=theme.font(9, True), padx=14, bg=theme.CARD_BG,
            ).grid(row=row, column=col, padx=3, pady=3, sticky="ew")
        for col in range(3):
            holder.grid_columnconfigure(col, weight=1)

    def _build_register(self) -> tk.Frame:
        box = tk.Frame(self.body, bg=theme.CARD_BG)

        role_row = tk.Frame(box, bg=theme.CARD_BG)
        role_row.pack(fill="x", pady=(0, 6))
        for role in ("Hasta", "Doktor"):
            button = surface.Button(
                role_row, role, lambda r=role: self.set_role(r), style="chip",
                height=34, font=theme.font(9, True), padx=18, bg=theme.CARD_BG,
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 6) if role == "Hasta" else 0)
            self.role_buttons[role] = button

        names = tk.Frame(box, bg=theme.CARD_BG)
        names.pack(fill="x", pady=(12, 0))
        names.grid_columnconfigure(0, weight=1)
        names.grid_columnconfigure(1, weight=1)
        first = tk.Frame(names, bg=theme.CARD_BG)
        first.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._label(first, "AD").pack(anchor="w", pady=(0, 6))
        self.name_field = self._field(first, "user", placeholder="Adınız")
        self.name_field.pack(fill="x")
        last = tk.Frame(names, bg=theme.CARD_BG)
        last.grid(row=0, column=1, sticky="ew")
        self._label(last, "SOYAD").pack(anchor="w", pady=(0, 6))
        self.surname_field = self._field(last, "user", placeholder="Soyadınız")
        self.surname_field.pack(fill="x")

        self._label(box, "T.C. KİMLİK NO").pack(anchor="w", pady=(12, 6))
        self.reg_tc_field = self._field(box, "user", placeholder="11 haneli T.C. kimlik no")
        self.reg_tc_field.pack(fill="x")
        self._label(box, "E-POSTA").pack(anchor="w", pady=(12, 6))
        self.mail_field = self._field(box, "mail", placeholder="ornek@eposta.com")
        self.mail_field.pack(fill="x")
        self._label(box, "ŞİFRE").pack(anchor="w", pady=(12, 6))
        self.reg_password_field = self._field(box, "shield", show="•", eye=True,
                                              placeholder="En az 8 karakter")
        self.reg_password_field.pack(fill="x")
        self.reg_password_field.entry.bind(
            "<KeyRelease>", lambda _e: self._rule_status(self.reg_password_field.entry.get())
        )

        rules = tk.Frame(box, bg=theme.CARD_BG)
        rules.pack(fill="x", pady=(8, 0))
        rules.grid_columnconfigure(0, weight=1)
        rules.grid_columnconfigure(1, weight=1)
        self.rule_labels: dict[str, tk.Label] = {}
        for index, (key, text) in enumerate(PASSWORD_RULE_LABELS):
            label = tk.Label(rules, text=f"○ {text}", font=theme.font(8), bg=theme.CARD_BG,
                             fg="#5a6a8d", anchor="w")
            row, col = divmod(index, 2)
            label.grid(row=row, column=col, sticky="w", pady=1)
            self.rule_labels[key] = label

        self.extra = tk.Frame(box, bg=theme.CARD_BG)
        self.extra.pack(fill="x")
        self._refresh_extra()

        surface.Button(box, "Hesabımı Oluştur", self.do_register, style="primary", height=46,
                       bg=theme.CARD_BG).pack(fill="x", pady=(16, 0))
        return box

    def _build_footer(self) -> None:
        self.footer = tk.Frame(self.body, bg=theme.CARD_BG)
        self.footer.pack(fill="x", pady=(18, 0))
        dot = tk.Canvas(self.footer, width=8, height=8, bg=theme.CARD_BG,
                        highlightthickness=0, bd=0)
        dot.create_oval(1, 1, 7, 7, fill=theme.SUCCESS, outline="")
        dot.pack(side="left", padx=(0, 6))
        tk.Label(self.footer, text="Güvenli oturum", font=theme.font(8, True),
                 bg=theme.CARD_BG, fg=theme.SUCCESS).pack(side="left")
        tk.Label(self.footer, text=f"v{__version__}", font=theme.font(8),
                 bg=theme.CARD_BG, fg=theme.DARK_MUTED).pack(side="right")

    def _refresh_extra(self) -> None:
        for child in self.extra.winfo_children():
            child.destroy()
        self.choice_buttons = {}
        if self.role == "Hasta":
            title, options, current, attr, columns = (
                "DİYABET TİPİ", DIYABET_TIPLERI, self.tip, "tip", 4,
            )
        else:
            title, options, current, attr, columns = (
                "UZMANLIK ALANI", UZMANLIKLAR, self.specialty, "specialty", 3,
            )
        self._label(self.extra, title).pack(anchor="w", pady=(14, 6))
        grid = tk.Frame(self.extra, bg=theme.CARD_BG)
        grid.pack(fill="x")
        for index, value in enumerate(options):
            row, col = divmod(index, columns)
            button = surface.Button(
                grid, value, lambda v=value, a=attr: self._pick(a, v),
                style="chip_on" if value == current else "chip",
                height=34, font=theme.font(9, True), padx=6, bg=theme.CARD_BG,
            )
            button.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.choice_buttons[value] = button
        for col in range(columns):
            grid.grid_columnconfigure(col, weight=1)

    def _pick(self, attr: str, value: str) -> None:
        setattr(self, attr, value)
        for name, button in self.choice_buttons.items():
            button.set_active(name == value)

    def set_role(self, role: str) -> None:
        self.role = role
        for name, button in self.role_buttons.items():
            button.set_active(name == role)
        self._refresh_extra()
        self.schedule()

    def select_tab(self, target: str) -> None:
        self.login_body.pack_forget()
        self.register_body.pack_forget()
        for key, button in self.tab_buttons.items():
            button.set_active(key == target)
        if target == "login":
            self.login_body.pack(fill="x", before=self.footer)
            self.tc_field.entry.focus_set()
        else:
            self.register_body.pack(fill="x", before=self.footer)
            self.set_role(self.role)
            self.name_field.entry.focus_set()
        self.schedule()

    # --- Eylemler --------------------------------------------------------------
    def do_login(self, _event=None) -> None:
        result = auth_service.authenticate(
            self.tc_field.entry.get().strip(), self.password_field.entry.get().strip()
        )
        if result["ok"]:
            _show_login_success(result, self.on_authenticated)
        else:
            messagebox.showerror("Giriş Başarısız", result["mesaj"])
            self.password_field.entry.delete(0, tk.END)
            self.password_field.sync_hint()
            self.password_field.entry.focus_set()

    def demo_login(self, user: dict, password: str) -> None:
        result = auth_service.authenticate(user["tc_kimlik_no"], password)
        if result["ok"]:
            _show_login_success(result, self.on_authenticated)
        else:
            messagebox.showerror("Demo Girişi", result["mesaj"])

    def _rule_status(self, password: str) -> dict[str, bool]:
        status = {
            "len": len(password) >= 8,
            "upper": any(c.isupper() for c in password),
            "lower": any(c.islower() for c in password),
            "digit": any(c.isdigit() for c in password),
            "special": any(not c.isalnum() for c in password),
        }
        for key, text in PASSWORD_RULE_LABELS:
            ok = status[key]
            self.rule_labels[key].config(
                text=f"{'●' if ok else '○'} {text}",
                fg=theme.SUCCESS if ok else "#5a6a8d",
            )
        return status

    def do_register(self) -> None:
        ad = self.name_field.entry.get().strip()
        soyad = self.surname_field.entry.get().strip()
        sifre = self.reg_password_field.entry.get().strip()
        if not ad or not soyad:
            messagebox.showerror("Eksik Bilgi", "Ad ve soyad boş bırakılamaz.")
            return
        status = self._rule_status(sifre)
        if not all(status.values()):
            eksikler = "\n".join(
                f"  • {text}" for key, text in PASSWORD_RULE_LABELS if not status[key]
            )
            messagebox.showerror("Zayıf Şifre", "Şifreniz şu kuralları sağlamıyor:\n" + eksikler)
            return
        tc_no = self.reg_tc_field.entry.get().strip()
        result = auth_service.register_user(
            tc_no, ad, soyad, self.mail_field.entry.get().strip(), sifre, self.role,
            diyabet_tipi=self.tip, uzmanlik=self.specialty,
        )
        if not result["ok"]:
            messagebox.showerror("Kayıt Başarısız", result["mesaj"])
            return
        messagebox.showinfo("Kayıt Başarılı", result["mesaj"])
        login_result = auth_service.authenticate(tc_no, sifre)
        if login_result["ok"]:
            _show_login_success(login_result, self.on_authenticated)

    # --- Çizim -----------------------------------------------------------------
    def schedule(self) -> None:
        """Yeniden çizimi birleştirir (pencere sürükleme sırasında titremeyi önler)."""
        self._cancel_render()
        self.pending = self.canvas.after(30, self.render)

    def _cancel_render(self) -> None:
        if self.pending is not None:
            try:
                self.canvas.after_cancel(self.pending)
            except tk.TclError:  # zaten yok edilmiş pencere
                pass
            self.pending = None

    def render(self) -> None:
        self.pending = None
        canvas = self.canvas
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 200 or h < 200:
            return
        wide = w >= WIDE_MIN
        self.backdrop = surface.backdrop_image(w, h)
        canvas.delete("bgfx")
        self.images = []
        self._image(0, 0, self.backdrop)
        if wide:
            self._draw_intro(h)
        self._draw_footer(w, h, wide)
        self._place_card(w, h, wide)

    def _image(self, x: int, y: int, pil_image) -> None:
        photo = ImageTk.PhotoImage(pil_image)
        self.images.append(photo)
        self.canvas.create_image(x, y, anchor="nw", image=photo, tags="bgfx")

    def _float(self, x: int, y: int, w: int, h: int, radius: int, fill: str, border=None) -> None:
        """Arka planın üstünde yüzen yuvarlatılmış yüzey (köşeleri arka planla kaynaşır)."""
        crop = self.backdrop.crop((x, y, x + w, y + h))
        photo = surface.composite_card(crop, radius, fill, border)
        self.images.append(photo)
        self.canvas.create_image(x, y, anchor="nw", image=photo, tags="bgfx")

    def _text(self, x: int, y: int, text: str, font: tuple, fill: str, *, anchor: str = "nw",
              width: int | None = None) -> int:
        options = {"text": text, "font": font, "fill": fill, "anchor": anchor, "tags": "bgfx"}
        if width is not None:
            options["width"] = width
        return self.canvas.create_text(x, y, **options)

    def _pulse(self, cx: float, cy: float, color: str) -> None:
        """Kalp atışı (EKG) simgesi; kan şekeri uygulamasının işareti."""
        size = 28
        ss = 4
        big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
        shape = ((-12, 0), (-6, 0), (-3, -9), (1, 9), (4, -4), (7, 0), (12, 0))
        pts = [((size / 2 + dx) * ss, (size / 2 + dy) * ss) for dx, dy in shape]
        ImageDraw.Draw(big).line(pts, fill=color, width=2 * ss, joint="curve")
        photo = ImageTk.PhotoImage(big.resize((size, size), Image.Resampling.LANCZOS))
        self.images.append(photo)
        self.canvas.create_image(cx, cy, anchor="center", image=photo, tags="bgfx")

    def _icon(self, name: str, cx: float, cy: float, size: float, color: str) -> None:
        """Anti-aliased ikonu arka plan üzerine şeffaf olarak basar."""
        px = max(8, round(size / 0.82))
        photo = ImageTk.PhotoImage(icons.icon_image(name, px, color))
        self.images.append(photo)
        self.canvas.create_image(cx, cy, anchor="center", image=photo, tags="bgfx")

    def _draw_intro(self, h: int) -> None:
        x, y = MARGIN, 44
        brand = icons.brand_image(40)
        if brand is not None:
            self.images.append(brand)
            self.canvas.create_image(x, y, anchor="nw", image=brand, tags="bgfx")
        self._text(x + 54, y + 4, "Diyabet Takip Sistemi", theme.display(13), theme.TEXT)
        self._text(x + 54, y + 26, "Hasta & doktor alanı", theme.font(9), theme.MUTED)

        pill_font = theme.font(9, True)
        label = "Akıllı diyabet takibi"
        pill_h = 32
        pill_w = _measure(label, pill_font) + 48
        pill_y = int(h * 0.20)
        self._float(x, pill_y, pill_w, pill_h, pill_h // 2, "#13234b", "#24427e")
        self._icon("droplet", x + 20, pill_y + pill_h / 2, 13, theme.PRIMARY)
        self._text(x + 36, pill_y + pill_h // 2, label, pill_font, "#cfe0ff", anchor="w")

        headline_y = pill_y + pill_h + 36
        self._text(x, headline_y, "Diyabetinizi", theme.display(48), "#ffffff")
        self._text(x, headline_y + 64, "birlikte takip edelim.", theme.display(48), theme.PRIMARY)
        subtitle_y = headline_y + 64 + 84
        self._text(
            x, subtitle_y,
            "Kan şekerinizi kaydedin, değerlerinizi analiz edin, doktorunuzla daha sağlıklı "
            "bir yaşam için adım atın.",
            theme.font(12), theme.MUTED, width=540,
        )

        feature_y = subtitle_y + 92
        column = 216
        for index, (icon_name, color, title, text) in enumerate(FEATURES):
            fx = x + index * column
            if index:
                self.canvas.create_line(fx - 18, feature_y, fx - 18, feature_y + 82,
                                        fill=theme.CARD_EDGE, tags="bgfx")
            self._float(fx, feature_y, 46, 46, 13, theme.dark_soft(color, 0.24),
                        theme.mix(color, theme.CARD_BG, 0.55))
            self._icon(icon_name, fx + 23, feature_y + 23, 20, color)
            title_id = self._text(fx + 60, feature_y + 1, title, theme.font(10, True),
                                  theme.TEXT, width=130)
            bottom = self.canvas.bbox(title_id)[3]
            self._text(fx + 60, bottom + 5, text, theme.font(9), theme.MUTED, width=130)

        quote_y = h - 176
        self._float(x, quote_y, 452, 88, 18, "#0e1a33", "#1f2f55")
        self._float(x + 18, quote_y + 20, 48, 48, 15, "#1a2b52", "#2a4278")
        self._pulse(x + 42, quote_y + 44, theme.BLOOD)
        self._text(x + 82, quote_y + 24, "Diyabet yönetimi, hayat kalitenizi artırır.",
                   theme.font(11, True), theme.TEXT)
        self._text(x + 82, quote_y + 50, "Küçük adımlar, büyük farklar yaratır.",
                   theme.font(9), theme.MUTED)

    def _draw_footer(self, w: int, h: int, wide: bool) -> None:
        self._text(MARGIN if wide else 24, h - 30,
                   "© 2026 Diyabet Takip Sistemi  ·  Sağlığınız bizim için önemli",
                   theme.font(9), "#7f90b3")

    def _place_card(self, w: int, h: int, wide: bool) -> None:
        self.body.update_idletasks()
        card_w = CARD_INNER + 2 * CARD_PAD
        card_h = self.body.winfo_reqheight() + 2 * CARD_PAD
        x = w - MARGIN - card_w if wide else (w - card_w) // 2
        y = max(16, (h - card_h) // 2)
        x = max(8, x)
        crop = self.backdrop.crop((x, y, x + card_w, y + card_h))
        photo = surface.composite_card(crop, CARD_RADIUS, theme.CARD_BG, theme.CARD_EDGE)
        self.images.append(photo)
        self.canvas.create_image(x, y, anchor="nw", image=photo, tags="bgfx")
        self.canvas.itemconfigure(self.body_window, width=CARD_INNER)
        self.canvas.coords(self.body_window, x + CARD_PAD, y + CARD_PAD)
        self.canvas.tag_raise(self.body_window)


def show_login_screen(
    on_authenticated: Callable[[], None], *, start_tab: str = "login"
) -> None:
    """Koyu, responsive giriş/kayıt ekranı."""
    state.session.reset()
    window = state.session.window
    try:
        window.attributes("-fullscreen", False)
        if window.state() == "zoomed":
            window.state("normal")
    except tk.TclError:
        pass
    for widget in window.winfo_children():
        widget.destroy()
    window.title("Diyabet Takip Sistemi · Giriş")
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    width = min(1560, max(1040, sw - 140))
    height = min(980, max(800, sh - 100))
    window.geometry(f"{width}x{height}")
    window.minsize(980, 800)
    window.resizable(True, True)
    window.configure(bg=theme.APP_BG)
    window._login_screen = _LoginScreen(window, on_authenticated, start_tab)
