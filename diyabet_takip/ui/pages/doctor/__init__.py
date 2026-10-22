"""Doktor rolünün tek pencere içindeki modern çalışma sayfaları.

Sayfalar işlev alanına göre ayrı modüllerde: ``patients`` (liste, ekleme,
detay), ``alerts``, ``appointments``, ``reports``, ``plans``. Ortak sabit ve
biçimlendiriciler ``_common`` içindedir. ``main_menu.py`` bu paketten
``from .pages.doctor import (...)`` ile içe aktarır.
"""

from __future__ import annotations

from .alerts import AlertsPage
from .appointments import AppointmentsPage
from .patients import AddPatientPage, PatientDetailPage, PatientsPage
from .plans import PlansPage
from .reports import ReportsPage

__all__ = [
    "AddPatientPage",
    "AlertsPage",
    "AppointmentsPage",
    "PatientDetailPage",
    "PatientsPage",
    "PlansPage",
    "ReportsPage",
]
