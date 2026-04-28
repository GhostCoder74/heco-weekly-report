# -----------------------------------------------------------------------------
# Project:        GaussEasterAlgorithm
# File:           easter.py
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

from datetime import datetime, timedelta

def easter_sunday(year: int) -> str:
    """Return Easter Sunday as YYYY-MM-DD (Gauss algorithm 1816)."""
    format = "%Y-%m-%d"

    a = year % 19
    b = year % 4
    c = year % 7
    k = year // 100
    p = (8 * k + 13) // 25
    q = k // 4
    m = (15 + k - p - q) % 30
    d = (19 * a + m) % 30
    n = (4 + k - q) % 7
    e = (2 * b + 4 * c + 6 * d + n) % 7

    day = 22 + d + e

    if d == 29 and e == 6:
        day = 50
    if d == 28 and e == 6 and a > 10:
        day = 49

    date = datetime(year, 3, 1) + timedelta(days=day - 1)
    return date.strftime(format)


def good_friday(year: int) -> str:
    date = datetime.strptime(easter_sunday(year), "%Y-%m-%d")
    return (date - timedelta(days=2)).strftime("%Y-%m-%d")

def easter_monday(year: int) -> str:
    date = datetime.strptime(easter_sunday(year), "%Y-%m-%d")
    return (date + timedelta(days=1)).strftime("%Y-%m-%d")

def ascension_day(year: int) -> str:
    date = datetime.strptime(easter_sunday(year), "%Y-%m-%d")
    return (date + timedelta(days=39)).strftime("%Y-%m-%d")

def pentecost_monday(year: int) -> str:
    date = datetime.strptime(easter_sunday(year), "%Y-%m-%d")
    return (date + timedelta(days=50)).strftime("%Y-%m-%d")

