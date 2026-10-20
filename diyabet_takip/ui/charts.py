"""Matplotlib grafikleri (Tkinter içine gömülü).

v1'de grafikler doğrudan DB'den bağlantı içinde çekiyordu; v2'de veri
repotosuyla gelir, bu modül sadece çizim yapar.
"""

from __future__ import annotations

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure

from .. import theme


def plot_blood_sugar_trend(
    parent,
    series: list[dict],
    target_range: tuple[float, float] | None = None,
) -> None:
    """Son ölçümlerin zaman grafiği + hedef aralığı bantı."""
    for widget in parent.winfo_children():
        widget.destroy()
    if not series:
        theme.muted_label(parent, "Grafik için yeterli geçerli ölçüm yok.", 10).pack(pady=14)
        return

    timestamps = [item["olcum_zamani"] for item in series]
    values = [float(item["kan_sekeri_degeri"]) for item in series]

    fig = Figure(figsize=(9, 3.5), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(timestamps, values, marker="o", linestyle="-", color=theme.PRIMARY, label="Kan Şekeri")

    if target_range:
        ax.axhspan(
            target_range[0],
            target_range[1],
            color="#bde3a8",
            alpha=0.45,
            label=f"Hedef ({target_range[0]:g}-{target_range[1]:g})",
        )

    ax.set_title("Kan Şekeri Değişim Grafiği (Son 100 Geçerli Ölçüm)", fontsize=10)
    ax.set_ylabel("Kan Şekeri (mg/dL)", fontsize=9)
    ax.grid(True, linestyle=":", color=theme.BORDER)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    formatter = DateFormatter("%d.%m %H:%M")
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=6)
    canvas.draw()


def plot_compliance_percentages(parent, rows: list[dict], role_for_title: str = "Hasta") -> None:
    """Uyum skorları çizgi grafiği."""
    for widget in parent.winfo_children():
        widget.destroy()
    if not rows:
        theme.muted_label(parent, "Uyum skorları grafiği için yeterli veri yok.", 10).pack(pady=14)
        return

    rows = sorted(rows, key=lambda d: d["hesaplama_tarihi"])
    dates = [d["hesaplama_tarihi"].strftime("%d.%m") for d in rows]
    diet = [d["diyet_uyum_orani"] for d in rows]
    exercise = [d["egzersiz_uyum_orani"] for d in rows]
    measurement = [d["olcum_uyum_orani"] for d in rows]
    overall = [d["genel_uyum_skoru"] for d in rows]

    fig = Figure(figsize=(9, 3.5), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(dates, diet, marker="o", linestyle="-", label="Diyet Uyum (%)", color=theme.PRIMARY)
    ax.plot(dates, exercise, marker="x", linestyle="-", label="Egzersiz Uyum (%)", color="#e07b39")
    ax.plot(dates, measurement, marker="s", linestyle="-", label="Ölçüm Uyum (%)", color="#7b5ea7")
    ax.plot(dates, overall, marker="^", linestyle="--", color="#333", linewidth=1.6, label="Genel Skor (%)")

    ax.set_title(f"{role_for_title} — Son 30 Günlük Uyum Skorları (%)", fontsize=10)
    ax.set_ylim(0, 105)
    ax.grid(True, linestyle=":", color=theme.BORDER, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.legend(loc="upper left", fontsize=8, frameon=False)
    fig.autofmt_xdate(rotation=45, ha="right")
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=6)
    canvas.draw()
