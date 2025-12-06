# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_extexec_mod.py
# Authors:        Christian Klose <cklose@intevation.de>                                      
#                 Raimund Renkert <rrenkert@intevation.de>                                    
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)           
# Copyright (c) 2024-2026 by Intevation GmbH                                                  
# SPDX-License-Identifier: GPL-2.0-or-later                                                   
#
# File version:   1.0.0
# 
# This file is part of "hcwr - heco Weekly Report"                                            
# Do not remove this header.                                                                  
# Wochenfazit URL:                                                                            
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit    
# Header added by https://github.com/GhostCoder74/Set-Project-Headers                         
# -----------------------------------------------------------------------------------------
import re
import sys
import datetime
import subprocess
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_fore_color, get_function_name
from hcwr_config_mod import get_calendar_week
from hcwr_config_mod import get_weekday_hours_per_day, get_week_hours

def run_wochenfazit(file_path):
    """
    Führt wochenfazit.py mit der übergebenen Datei aus und gibt die Ausgabe auf stderr aus.
    """
    fname = get_function_name()
    try:
        result = subprocess.run(
            [HCWR_GLOBALS.WF_CHECK_PATH, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            text=True  # für str statt bytes
        )
        print(result.stdout, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Ausführen von {HCWR_GLOBALS.WF_CHECK_PATH}: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        sys.exit(0)

def get_kw_overhours(kw, conn=None):
    # TODO: overhours hier implementieren
    """
    Berechnnet die Überstunden zur angegebenen Kalendarwochen "kw"
    """
    fname = get_function_name()
    cmd = ["overhours", "-kw", str(kw)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    match = re.search(r"Summe:\s*([+-]?\d+):(\d+):\d+", result.stdout)
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        value = 0
        if match:
            h, m = match.groups()
            result = Decimal(h) + Decimal(m) / 60
            info(f"get_kw_overhours: {result}")
            sys.exit(0)
        else:
            info(f"get_kw_overhours: 0.0")
            sys.exit(0)

    if match:
        h, m = match.groups()
        return Decimal(h) + Decimal(m) / 60
    return Decimal("0")

def NEWget_kw_overhours(kw, conn):
    """
    Berechnnet die Überstunden zur angegebenen Kalendarwochen "kw"
    """
    fname = get_function_name()
    if HCWR_GLOBALS.CFG.has_option('Onboarding', 'firstday'): 
        firstday = HCWR_GLOBALS.CFG.get('Onboarding', 'firstday')
    if not firstday:
        warning(f"First day of Work is not set","","ERROR")
        sys.exit(1)
    year, week = get_calendar_week(firstday)
    year_now = datetime.date.today().year
    if year != year_now:
        first_kw = 1
    else:
        first_kw = week
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nyear_now = {year_now}")
        info(f"kw = {kw}")
        info(f"first_kw = {first_kw}")
        info(f"week = {week}")

    last_kw_total = Decimal(0).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    #for i in range(first_kw, kw + 1):
    kw_total = get_week_hours(conn, int(year_now), int(kw + 1), int(first_kw)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"WEEK {first_kw}-{kw}/{year_now}:\n          kw_total = {kw_total}\n          last_kw_total = {last_kw_total}")
        #info(f"kw_diff = {kw_diff}")

    contract_hours = Decimal(str(HCWR_GLOBALS.CONTRACT_HOURS))
    contract_hours_rounded = contract_hours.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    overhours = (kw_total - contract_hours)
    overhours_rounded = overhours.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    sign = "+"
    if overhours_rounded < 0:
        sign = "-"

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"    sign = {sign}, overhours_rounded = {overhours_rounded}, kw_total = {kw_total}")
    last_kw_total = kw_total

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        sys.exit(0)

def get_kw_overhours_add(wdayhours=None, overhours_day=None, week_total=None):
    """
    day_overhours = True  -> überstunden für target_day zurückgeben (1 Nachkommastelle)
    day_overhours = False -> Wochenwerte zurückgeben (wie bisher)
    """
    fname = get_function_name()
    if isinstance(week_total, tuple):
        week_total = week_total[0]

    # Falls Tagesüberstunden abgefragt werden
    if overhours_day:
        if overhours_day not in wdayhours:
            raise ValueError(f"Unbekannter Tag '{target_day}', erlaubt: {list(wdayhours.keys())}")

        # Wochenarbeitszeit pro Tag aus Global
        daily_contract = Decimal(HCWR_GLOBALS.WDAYHOURS_MAP[overhours_day])

        # Stunden des Tages
        hours = wdayhours[overhours_day]

        # Tagesüberstunden
        over = hours - daily_contract

        # 1 Nachkommastelle runden
        over_rounded = over.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        sign = "+"
        if over_rounded < 0:
            sign = "-"

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fname}:")
            info(f"Day: {overhours_day}")
            info(f"Sign: {sign}")
            info(f"overhours_day: {over_rounded}")
            info(f"Hours: {hours.quantize(Decimal('0.1'))}")
            sys.exit(0)

        return sign, over_rounded, hours.quantize(Decimal("0.1")),

    # ------------------------------------------------------------
    # Normal: Wochenüberstunden berechnen (bestehendes Verhalten)
    # ------------------------------------------------------------


    total = Decimal("0")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:")

    if week_total is None:
        for day, hours in wdayhours.items():
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"Day {day}: {hours} h")
            total += hours
        total_rounded = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    else:
        total = week_total
        total_rounded = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    contract_hours = Decimal(str(HCWR_GLOBALS.CONTRACT_HOURS))
    contract_hours_rounded = contract_hours.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    overhours = (total - contract_hours)
    overhours_rounded = overhours.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    sign = "+"
    if overhours_rounded < 0:
        sign = "-"

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"wdayhours         = {wdayhours}")
        info(f"Sign              = {sign}")
        info(f"Overhours         = {overhours_rounded}")
        info(f"Total hours       = {total_rounded}")
        sys.exit(0)

    return sign, overhours_rounded, total_rounded

