"""Profil ve hesap güvenliği sayfası (tek pencere içinde)."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

from ... import state, theme
from ...db import bootstrap as B
from ...db import reference as ref
from ...db.client import get_db
from ...services import auth_service
from .base import Page, badge, card, field_label, kv, notice, section

RULES = (
    ("len", "En az 8 karakter"),
    ("upper", "Bir büyük harf"),
    ("lower", "Bir küçük harf"),
    ("digit", "Bir rakam"),
    ("special", "Bir özel karakter"),
)


def _initials(first: str, last: str) -> str:
    first = (first or "").removeprefix("Dr.").strip()
    letters = [x[0] for x in (first, last) if x]
    return "".join(letters).upper() or "DT"


class ProfilePage(Page):
    title = "Profilim"
    subtitle = "Hesap bilgileriniz ve güvenlik ayarlarınız."
    icon = "user"
    accent = theme.SLATE

    def build(self) -> None:
        self.page_head()
        db = get_db()
        self.user = db[B.USERS].find_one({"_id": state.session.user_id}) if db is not None else None
        if not self.user:
            notice(self.body, "Profil bilgileri yüklenemedi.", accent=theme.BLOOD).pack(fill="x")
            return
        body = tk.Frame(self.body, bg=theme.APP_BG)
        body.pack(fill="both", expand=True)
        left = card(body, padx=20, pady=18, accent=theme.PRIMARY)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = card(body, padx=20, pady=18, accent=theme.GREEN)
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))

        self._profile_card(left.body)
        self._password_card(right.body)

    def _profile_card(self, parent) -> None:
        hero = tk.Frame(parent, bg=theme.CARD_BG)
        hero.pack(fill="x", pady=(0, 16))
        avatar = tk.Canvas(hero, width=74, height=74, bg=theme.CARD_BG, highlightthickness=0)
        avatar.pack(side="left", padx=(0, 16))
        avatar.create_oval(2, 2, 72, 72, fill=theme.PRIMARY_SOFT, outline=theme.PRIMARY, width=1)
        avatar.create_text(
            37, 37, text=_initials(self.user.get("ad", ""), self.user.get("soyad", "")),
            font=theme.font(20, True), fill=theme.TEXT,
        )
        text = tk.Frame(hero, bg=theme.CARD_BG)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=f"{self.user.get('ad', '')} {self.user.get('soyad', '')}".strip(),
                 font=theme.font(17, True), bg=theme.CARD_BG, fg=theme.TEXT,
                 anchor="w").pack(anchor="w")
        badge(text, state.session.user_role or "Kullanıcı",
              theme.CYAN if state.session.user_role == "Hasta" else theme.PRIMARY).pack(anchor="w", pady=(5, 0))
        tk.Label(text, text=self.user.get("eposta") or "E-posta kayıtlı değil",
                 font=theme.font(9), bg=theme.CARD_BG, fg=theme.MUTED, anchor="w").pack(anchor="w", pady=(7, 0))

        section(parent, "Hesap Bilgileri", "Kimlik ve iletişim bilgileri", icon="user", accent=theme.PRIMARY)
        kv(parent, "T.C. Kimlik No", self.user.get("tc_kimlik_no") or "—").pack(fill="x", pady=3)
        kv(parent, "E-posta", self.user.get("eposta") or "—").pack(fill="x", pady=3)
        kv(parent, "Rol", state.session.user_role or "—").pack(fill="x", pady=3)
        birth = self.user.get("dogum_tarihi")
        kv(parent, "Doğum Tarihi", birth.strftime("%d.%m.%Y") if isinstance(birth, datetime.datetime) else "—").pack(fill="x", pady=3)

        db = get_db()
        if state.session.user_role == "Hasta" and db is not None:
            profile = ref.find_patient_profile(db, state.session.patient_id) or {}
            tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=12)
            section(parent, "Sağlık Profili", "Kişisel takip bilgileri", icon="heart", accent=theme.BLOOD)
            kv(parent, "Diyabet Tipi", profile.get("diyabet_tipi") or "—").pack(fill="x", pady=3)
            diagnosis = profile.get("tani_tarihi")
            kv(parent, "Tanı Tarihi", diagnosis.strftime("%d.%m.%Y") if isinstance(diagnosis, datetime.date) else "—").pack(fill="x", pady=3)
            target = f"{profile.get('hedef_kan_sekeri_min', 70)} – {profile.get('hedef_kan_sekeri_max', 140)} mg/dL"
            kv(parent, "Hedef Aralık", target).pack(fill="x", pady=3)
        elif state.session.user_role == "Doktor" and db is not None:
            profile = db[B.DOCTOR_PROFILES].find_one({"user_id": state.session.user_id}) or {}
            tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=12)
            section(parent, "Mesleki Bilgiler", "Klinik profil", icon="stethoscope", accent=theme.TEAL)
            kv(parent, "Uzmanlık", profile.get("uzmanlik_alani") or "—").pack(fill="x", pady=3)
            kv(parent, "Hastane", profile.get("hastane_adi") or "—").pack(fill="x", pady=3)

        notice(parent, "Hesap bilgileriniz güvenli biçimde saklanır; oturumunuz yalnızca size ait verileri gösterir.",
               accent=theme.CYAN, icon="shield", wraplength=620).pack(fill="x", pady=(18, 0))

    def _password_card(self, parent) -> None:
        section(parent, "Şifre Değiştir", "Güvenli bir şifre seçin; hesabınızı koruyun.", icon="shield", accent=theme.GREEN)
        field_label(parent, "Mevcut şifre").pack(anchor="w", pady=(4, 0))
        self.current = theme.entry(parent, width=30, show="•")
        self.current.pack(fill="x", pady=(4, 10))
        field_label(parent, "Yeni şifre").pack(anchor="w")
        self.new = theme.entry(parent, width=30, show="•")
        self.new.pack(fill="x", pady=(4, 10))
        self.new.bind("<KeyRelease>", lambda _e: self._update_rules())
        field_label(parent, "Yeni şifre (tekrar)").pack(anchor="w")
        self.repeat = theme.entry(parent, width=30, show="•")
        self.repeat.pack(fill="x", pady=(4, 10))
        row = tk.Frame(parent, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(0, 10))
        self.show_btn = theme.button(row, "Şifreyi Göster", self._toggle, style="ghost")
        self.show_btn.pack(side="left")
        self.match_label = tk.Label(row, text="", font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED)
        self.match_label.pack(side="left", padx=(12, 0))

        rule_box = tk.Frame(parent, bg=theme.CARD_2, highlightbackground=theme.BORDER, highlightthickness=1)
        rule_box.pack(fill="x", pady=(4, 14))
        self.rule_rows: dict[str, tuple[tk.Canvas, tk.Label]] = {}
        for key, text in RULES:
            line = tk.Frame(rule_box, bg=theme.CARD_2)
            line.pack(fill="x", padx=12, pady=3)
            canvas = tk.Canvas(line, width=16, height=16, bg=theme.CARD_2, highlightthickness=0)
            canvas.pack(side="left")
            label = tk.Label(line, text=text, font=theme.font(8), bg=theme.CARD_2, fg=theme.MUTED, anchor="w")
            label.pack(side="left", padx=(6, 0))
            self.rule_rows[key] = (canvas, label)
        self._update_rules()

        theme.button(parent, "Şifreyi Güncelle", self._change, style="primary").pack(fill="x")
        notice(parent, "Yeni şifre en az 8 karakter; büyük/küçük harf, rakam ve özel karakter içermelidir. Şifreniz güvenli biçimde saklanır.",
               accent=theme.GREEN, icon="shield").pack(fill="x", pady=(14, 0))
        tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=16)
        tk.Label(parent, text="Uygulama Sürümü", font=theme.font(8), bg=theme.CARD_BG,
                 fg=theme.MUTED, anchor="w").pack(anchor="w")
        tk.Label(parent, text="Diyabet Takip Sistemi · v2.4.0", font=theme.font(9, True),
                 bg=theme.CARD_BG, fg=theme.TEXT, anchor="w").pack(anchor="w", pady=(2, 0))

    def _toggle(self) -> None:
        show = self.current.cget("show") == "•"
        value = "" if show else "•"
        for widget in (self.current, self.new, self.repeat):
            widget.configure(show=value)
        self.show_btn.configure(text="Şifreyi Gizle" if show else "Şifreyi Göster")

    def _update_rules(self) -> None:
        value = self.new.get()
        flags = {
            "len": len(value) >= 8,
            "upper": any(c.isupper() for c in value),
            "lower": any(c.islower() for c in value),
            "digit": any(c.isdigit() for c in value),
            "special": any(not c.isalnum() and not c.isspace() for c in value),
        }
        for key, (canvas, label) in self.rule_rows.items():
            ok = flags[key]
            canvas.delete("all")
            if ok:
                canvas.create_oval(2, 2, 14, 14, fill=theme.SUCCESS, outline="")
                canvas.create_line(5, 8, 7, 10, 11, 5, fill="#06170f", width=1.5, capstyle="round")
                label.configure(fg=theme.TEXT)
            else:
                canvas.create_oval(3, 3, 13, 13, outline=theme.MUTED, width=1)
                label.configure(fg=theme.MUTED)
        if self.repeat.get():
            self.match_label.configure(
                text="Şifreler eşleşiyor" if self.new.get() == self.repeat.get() else "Şifreler eşleşmiyor",
                fg=theme.SUCCESS if self.new.get() == self.repeat.get() else theme.BLOOD,
            )
        else:
            self.match_label.configure(text="")

    def _change(self) -> None:
        if self.new.get() != self.repeat.get():
            messagebox.showerror("Şifre", "Yeni şifreler eşleşmiyor.", parent=self)
            return
        result = auth_service.change_password(
            state.session.user_id, self.current.get(), self.new.get()
        )
        if not result["ok"]:
            messagebox.showerror("Şifre", result["mesaj"], parent=self)
            return
        messagebox.showinfo("Şifre", result["mesaj"], parent=self)
        self.current.delete(0, tk.END)
        self.new.delete(0, tk.END)
        self.repeat.delete(0, tk.END)
        self._update_rules()

    def _logout(self) -> None:
        from .. import navigation

        navigation.go_login()

    def refresh(self) -> None:
        self.app.navigate("profile")
