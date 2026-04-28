# -----------------------------------------------------------------------------
# Project:        GaussEasterAlgorithm
# File:           holidays.py
# Author:         Christian Klose
# Email:          ghostcoder@gmx.de
# GitHub:         https://github.com/GhostCoder74/Set-Project-Headers (GhostCoder74)
# Copyright (c) 2025 Christian Klose
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of GaussEasterAlgorithm.
# Do not remove this header.
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------

from geaCal_translator_mod import t
from datetime import datetime
from geaCal_easter_mod import (
    good_friday, easter_sunday, easter_monday,
    ascension_day, pentecost_monday
)
from geaCal_utils_mod import mid, right

_cached_year = None
_mov_days = []
_mov_months = []

# ---------------------------------------------------------------
# Intern: Berechnet bewegliche Feiertage für ein Jahr
# ---------------------------------------------------------------
def load_movable_holidays(year: int):
    global _cached_year, _mov_days, _mov_months

    if year == _cached_year:
        return

    _cached_year = year
    _mov_days = []
    _mov_months = []

    holiday_funcs = [
        good_friday,
        easter_sunday,
        easter_monday,
        ascension_day,
        pentecost_monday,
    ]

    for func in holiday_funcs:
        date_str = func(year)
        _mov_months.append(int(mid(date_str, 5, 2)))
        _mov_days.append(int(right(date_str, 2)))


# ---------------------------------------------------------------
# Einzelnen Feiertag abfragen
# ---------------------------------------------------------------
def get_holiday(year: int, month: int, day: int) -> str:
    load_movable_holidays(year)

    # Fixed holidays
    if month == 1 and day == 1:
        return t("New Year's Day")
    if month == 5 and day == 1:
        return t("Labor Day")
    if month == 10:
        if day == 3: return t("German Unity Day")
        if day == 31: return t("Reformation Day")
    if month == 12:
        if day == 25: return t("Christmas Day")
        if day == 26: return t("Second Christmas Day")
    

    names = [
        t("Good Friday"),
        t("Easter Sunday"),
        t("Easter Monday"),
        t("Ascension Day"),
        t("Pentecost Monday")
    ]


    for i in range(len(names)):
        if month == _mov_months[i] and day == _mov_days[i]:
            return names[i]

    return ""


# ---------------------------------------------------------------
# NEU:
# Liste aller Feiertage eines Jahres zurückgeben
# (für CLI: --year → --list / -y -l)
# ---------------------------------------------------------------
def list_holidays_for_year(year: int):
    """Return a list of (date, name) for all fixed + movable holidays."""
    load_movable_holidays(year)

    holidays = []

    # Fixed holidays
    fixed = [
        ("{}-01-01".format(year), t("New Year's Day")),
        ("{}-05-01".format(year), t("Labor Day")),
        ("{}-10-03".format(year), t("German Unity Day")),
        ("{}-10-31".format(year), t("Reformation Day")),
        ("{}-12-25".format(year), t("Christmas Day")),
        ("{}-12-26".format(year), t("Second Christmas Day")),
    ]
    holidays.extend(fixed)

    # Movable
    movable_funcs = [
        (good_friday,      t("Good Friday")),
        (easter_sunday,    t("Easter Sunday")),
        (easter_monday,    t("Easter Monday")),
        (ascension_day,    t("Ascension Day")),
        (pentecost_monday, t("Pentecost Monday"))
    ]

    for func, name in movable_funcs:
        date = func(year)
        holidays.append((date, name))

    # Sort ascending
    holidays.sort(key=lambda x: x[0])

    return holidays

