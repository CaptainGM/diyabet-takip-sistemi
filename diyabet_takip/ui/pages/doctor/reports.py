"""Doktor — tarih aralığına göre hasta raporu üretimi."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

from .... import state, theme
from ....db import doctors as doctors_db
from ....services import report_service
from ... import helpers
from ..base import Page, card, field_label, notice, section


class ReportsPage(Page):
    title = "Raporlar"
    subtitle = "Hasta verilerini tarih aralığına göre tek metin raporunda toplayın."
    icon = "report"
    accent = theme.TEAL

    def __init__(self, parent, app, patient_id: str | None = None) -> None:
        self.preselect = patient_id
        super().__init__(parent, app)

    def build(self) -> None:
        self.page_head()
        patients = doctors_db.list_patients_for_doctor(state.session.doctor_id)
        self.patient_map = {f"{p['ad']} {p['soyad']} · {p['tc_kimlik_no']}": p for p in patients}
        left = card(self.body, padx=16, pady=14, accent=theme.TEAL)
        left.pack(side="left", fill="both", padx=(0, 6))
        left.configure(width=390)
        left.pack_propagate(False)
        section(left.body, "Rapor Parametreleri", "Hasta ve tarih aralığı seçin.",
                icon="report", accent=theme.TEAL)
        labels = list(self.patient_map)
        selected = labels[0] if labels else "Hasta yok"
        if self.preselect is not None:
            for label, patient in self.patient_map.items():
                if str(patient["hasta_id"]) == str(self.preselect):
                    selected = label
                    break
        self.patient_var = tk.StringVar(value=selected)
        menu = tk.OptionMenu(left.body, self.patient_var, *(labels or ["Hasta yok"]))
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER)
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        field_label(left.body, "Hasta").pack(anchor="w", pady=(4, 0))
        menu.pack(fill="x", pady=(3, 10))
        field_label(left.body, "Başlangıç Tarihi").pack(anchor="w")
        self.start = theme.date_entry(left.body)
        self.start.set_date(datetime.date.today() - datetime.timedelta(days=30))
        self.start.pack(fill="x", pady=(3, 10))
        field_label(left.body, "Bitiş Tarihi").pack(anchor="w")
        self.end = theme.date_entry(left.body)
        self.end.set_date(datetime.date.today())
        self.end.pack(fill="x", pady=(3, 12))
        theme.button(left.body, "Raporu Oluştur", self._generate, style="primary").pack(fill="x")
        theme.button(left.body, "Metin Dosyası Olarak Kaydet", self._save, style="ghost").pack(fill="x", pady=(8, 0))
        notice(left.body, "Rapor; ölçüm, uyum, uyarı ve plan özetlerini içerir.",
               accent=theme.TEAL, icon="shield", wraplength=300).pack(fill="x", pady=(12, 0))

        right = card(self.body, padx=0, pady=0)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        head = tk.Frame(right.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Rapor Önizleme", "Oluşturduğunuz metin burada görünür.",
                icon="clipboard", accent=theme.TEAL)
        self.text = tk.Text(
            right.body, wrap="word", font=theme.font(9), bg=theme.DARK_FIELD,
            fg=theme.TEXT, insertbackground=theme.TEXT, relief="flat",
            highlightthickness=1, highlightbackground=theme.BORDER, padx=12, pady=12,
        )
        self.text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.text.tag_configure("placeholder", foreground=theme.MUTED, font=theme.font(10))
        self.text.insert(
            "1.0",
            "RAPOR ÖNİZLEMESİ\n\n"
            "Soldaki formdan hasta ve tarih aralığı seçip “Raporu Oluştur”a basın.\n\n"
            "Rapor şunları içerir:\n"
            "  •  Kan şekeri ölçümleri ve günlük dağılım\n"
            "  •  Diyet / egzersiz uyum skoru\n"
            "  •  Uyarı geçmişi ve kritik kayıtlar\n"
            "  •  Aktif diyet, egzersiz ve belirti planları",
            "placeholder",
        )
        self.text.configure(state="disabled")

    def _generate(self) -> None:
        patient = self.patient_map.get(self.patient_var.get())
        if not patient:
            messagebox.showinfo("Rapor", "Önce bir hasta seçin.", parent=self)
            return
        start, end = self.start.get_date(), self.end.get_date()
        if end < start:
            messagebox.showerror("Rapor", "Bitiş tarihi başlangıçtan önce olamaz.", parent=self)
            return
        try:
            sections = report_service.build_report(patient["hasta_id"], start, end)
        except Exception:
            messagebox.showerror(
                "Rapor",
                "Rapor şu anda oluşturulamıyor. Lütfen tekrar deneyin.",
                parent=self,
            )
            return
        if not sections:
            messagebox.showinfo("Rapor", "Bu aralıkta raporlanacak kayıt yok.", parent=self)
            return
        lines = [
            "DİYABET TAKİP SİSTEMİ — HASTA RAPORU",
            f"Rapor Tarihi: {datetime.date.today().strftime('%d.%m.%Y')}",
            "=" * 70,
            "",
        ]
        for section_data in sections:
            lines.append(section_data["bolum"])
            for key, value in section_data["veri"].items():
                lines.append(f"  {helpers.REPORT_LABELS.get(key, key)}: {helpers.format_report_value(key, value)}")
            lines.append("")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")

    def _save(self) -> None:
        content = self.text.get("1.0", "end").strip()
        if not content or content.startswith("Rapor oluşturmak"):
            messagebox.showinfo("Rapor", "Önce bir rapor oluşturun.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Metin Dosyası", "*.txt")],
            initialfile="hasta_raporu.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)
            messagebox.showinfo("Rapor", f"Rapor kaydedildi:\n{path}", parent=self)
