"""Matplotlib grafikleri (Tkinter içine gömülü) — koyu tema uyumlu.

v1'de grafikler doğrudan DB'den bağlantı içinde çekiyordu; v2'de veri
reposuyla gelir, bu modül sadece çizim yapar. v2.2'den itibaren figür zemini
koyu kart rengine boyanır.
"""

from __future__ import annotations

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure

from .. import theme


def _style_figure(fig: Figure, ax) -> None:
    """Koyu tema: figür/eksen zeminleri, tikler, çizgiler."""
    fig.patch.set_facecolor(theme.CARD_BG)
    ax.set_facecolor(theme.CARD_BG)
    ax.tick_params(colors=theme.MUTED, labelsize=8)
    ax.title.set_color(theme.TEXT)
    ax.yaxis.label.set_color(theme.MUTED)
    ax.xaxis.label.set_color(theme.MUTED)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(theme.BORDER)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


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
    ax.plot(
        timestamps, values, marker="o", markersize=4, linestyle="-",
        color=theme.BLOOD, linewidth=1.8, label="Kan Şekeri",
    )
    ax.fill_between(timestamps, values, 40, color=theme.BLOOD, alpha=0.10)

    if target_range:
        ax.axhspan(
            target_range[0],
            target_range[1],
            color=theme.SUCCESS,
            alpha=0.12,
            label=f"Hedef ({target_range[0]:g}-{target_range[1]:g})",
        )

    ax.set_ylabel("Kan Şekeri (mg/dL)", fontsize=9, color=theme.MUTED)
    ax.grid(True, linestyle=":", color=theme.BORDER, alpha=0.6)
    formatter = DateFormatter("%d.%m %H:%M")
    ax.xaxis.set_major_formatter(formatter)
    _style_figure(fig, ax)
    legend = fig.legend(loc="upper right", fontsize=8, frameon=False)
    for text in legend.get_texts():
        text.set_color(theme.MUTED)
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().configure(bg=theme.CARD_BG, highlightthickness=0)
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=6)
    canvas.draw()


def plot_dashboard_trend(
    parent,
    points: list[tuple],
    *,
    color: str = theme.CYAN,
    target_range: tuple[float, float] = (70, 140),
) -> None:
    """Dashboard kartı için kompakt, alan dolgulu trend grafiği.

    ``points``: ``(tarih, ortalama)`` çiftleri; ``ortalama`` None olabilir.
    """
    for widget in parent.winfo_children():
        widget.destroy()
    valid = [(d, float(v)) for d, v in points if v is not None]
    if not valid:
        theme.muted_label(parent, "Bu aralıkta ölçüm bulunamadı.", 10).pack(pady=30)
        return

    dates = [d for d, _ in valid]
    values = [v for _, v in valid]
    y_min = min(40.0, min(values) - 15)
    y_max = max(200.0, max(values) + 20)

    fig = Figure(figsize=(6.4, 2.25), dpi=100)
    ax = fig.add_subplot(111)
    ax.fill_between(dates, values, y_min, color=color, alpha=0.13, linewidth=0)
    ax.plot(
        dates, values, color=color, linewidth=2.0, marker="o", markersize=4,
        markerfacecolor=color, markeredgecolor=theme.CARD_BG, markeredgewidth=1.4,
    )
    ax.axhspan(
        target_range[0], target_range[1], color=theme.GREEN, alpha=0.07, linewidth=0,
    )
    ax.set_ylim(y_min, y_max)
    ax.grid(True, linestyle=":", color=theme.BORDER, alpha=0.55, axis="y")
    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))
    ax.set_ylabel("mg/dL", fontsize=8, color=theme.MUTED)
    _style_figure(fig, ax)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout(pad=0.6)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.96, bottom=0.18)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().configure(bg=theme.CARD_BG, highlightthickness=0)
    canvas.get_tk_widget().pack(fill="both", expand=True)
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
    ax.plot(dates, diet, marker="o", linestyle="-", label="Diyet Uyum (%)", color=theme.GREEN)
    ax.plot(dates, exercise, marker="x", linestyle="-", label="Egzersiz Uyum (%)", color=theme.ORANGE)
    ax.plot(dates, measurement, marker="s", linestyle="-", label="Ölçüm Uyum (%)", color=theme.BLOOD)
    ax.plot(
        dates, overall, marker="^", linestyle="--", color=theme.TEXT,
        linewidth=1.8, label="Genel Skor (%)",
    )

    ax.set_title(f"{role_for_title} — Son 30 Günlük Uyum Skorları (%)", fontsize=10, color=theme.TEXT)
    ax.set_ylim(0, 105)
    ax.grid(True, linestyle=":", color=theme.BORDER, alpha=0.6)
    _style_figure(fig, ax)
    fig.autofmt_xdate(rotation=45, ha="right")
    fig.tight_layout()
    fig.subplots_adjust(top=0.80, bottom=0.24)
    legend = fig.legend(
        loc="upper center", ncol=4, fontsize=8, frameon=False,
        bbox_to_anchor=(0.5, 0.99),
    )
    for text in legend.get_texts():
        text.set_color(theme.MUTED)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().configure(bg=theme.CARD_BG, highlightthickness=0)
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=6)
    canvas.draw()
