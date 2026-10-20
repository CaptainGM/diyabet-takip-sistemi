"""Servis katmanı.

v1'de iş mantığının büyük kısmı MySQL trigger'ları, stored procedure'leri ve
fonksiyonlarındaydı. v2'de tüm bunlar applicaion katmanındaki servis
modüllerine taşındı:

- alert_service: kan şekeri eşiği uyarıları (trigger karşılığı)
- insulin_service: insülin doz önerisi (procedür + fonksiyon karşılığı)
- compliance_service: uyum skoru (procedür + event karşılığı)
- stats_service: günlük ölçüm istatistikleri (event karşılığı)
- recommendation_service: kural tabanlı diyet/egzersiz önerisi (procedür)
- report_service: hasta raporu (procedür)
- jobs: geceleyin çalışacak toplu işler (event karşılığı; ``python -m diyabet_takip.jobs``)
"""

from __future__ import annotations
