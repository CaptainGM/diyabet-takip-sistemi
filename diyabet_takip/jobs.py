"""Günlük toplu işler — v1'deki 3 adet MySQL EVENT'in karşılığı.

Kullanım::

    python -m diyabet_takip.jobs                     # dün için çalıştır
    python -m diyabet_takip.jobs --date 2026-10-19   # belirli gün
    python -m diyabet_takip.jobs --all-patients      # uyum+istatistik doldur
"""

from __future__ import annotations

import argparse
import datetime
import sys

from .db import bootstrap
from .services import alert_service, compliance_service


def run_daily_jobs(day: datetime.date) -> dict:
    """Ölçüm eksik uyarıları + uyum skorları (v1 event'leri)."""
    bootstrap.ensure_schema()
    alerts = alert_service.check_daily_measurement_count(day)
    scores = compliance_service.compute_for_all(day)
    return {"date": day.isoformat(), "uyari_eklendi": alerts, "skor_yenilendi": scores}


def backfill_compliance(days: int = 0) -> int:
    from .db import bootstrap as B
    from .db.client import get_db_strict
    from .services import stats_service

    db = get_db_strict()
    bootstrap.ensure_schema(db)
    n = 0
    for profile in db[B.PATIENT_PROFILES].find({}, {"_id": 1}):
        for offset in range(days, -1, -1):
            day = datetime.date.today() - datetime.timedelta(days=offset)
            if compliance_service.compute_for(profile["_id"], day):
                n += 1
                stats_service.compute_for(profile["_id"], day)
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="Günlük toplu işler (v1 event karşılığı)")
    parser.add_argument("--date", type=str, default=None, help="AAAA-AA-GG (varsayılan: dün)")
    parser.add_argument(
        "--all-patients", action="store_true",
        help="Belirtilen gün yerine tüm hastaların son 30 gününü hesaplar",
    )
    args = parser.parse_args()

    if args.all_patients:
        n = backfill_compliance(30)
        print(f"{n} hasta-günlük skor/istatistik hesaplandı.")
        sys.exit(0)

    if args.date:
        day = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        day = datetime.date.today() - datetime.timedelta(days=1)
    result = run_daily_jobs(day)
    print(result)


if __name__ == "__main__":
    main()
