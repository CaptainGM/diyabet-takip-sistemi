"""Hasta rolünün tek pencere içindeki modern çalışma sayfaları.

Sayfalar işlev alanına göre ayrı modüllerde: ``measure``, ``history``,
``compliance``, ``insulin``, ``notifications``, ``plans``, ``appointments``,
``lifestyle``. Ortak sabitler ``_common`` içindedir. ``main_menu.py`` bu
paketten ``from .pages.patient import (...)`` ile içe aktarır.
"""

from __future__ import annotations

from .appointments import PatientAppointmentsPage
from .compliance import CompliancePage
from .history import HistoryPage
from .insulin import InsulinPage
from .lifestyle import LifestylePage
from .measure import MeasurePage
from .notifications import NotificationsPage
from .plans import PatientPlansPage

__all__ = [
    "CompliancePage",
    "HistoryPage",
    "InsulinPage",
    "LifestylePage",
    "MeasurePage",
    "NotificationsPage",
    "PatientAppointmentsPage",
    "PatientPlansPage",
]
