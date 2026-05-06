# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_hcwrd_mod.py
# Authors:        Christian Klose <cklose@intevation.de>
#                 Raimund Renkert <rrenkert@intevation.de>
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)
# Copyright (c) 2024-2026 by Intevation GmbH
# SPDX-License-Identifier: GPL-2.0-or-later
#
# File version:   1.0.2
# 
# This file is part of "hcwr - heco Weekly Report"
# Do not remove this header.
# Wochenfazit URL:
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------------------
import sys
import datetime
from datetime import datetime, timedelta, date
from decimal import Decimal
from decimal import Decimal, InvalidOperation
import re

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_config_mod import get_calendar_week
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route, debug_sql
from hcwr_utils_mod import progress_bar, input_with_prefill, parse_timestamp

def validate_date(date_string):
    fname = get_function_name()
    # Definieren Sie einen regulären Ausdruck, um das Format YYYY-MM-DD zu überprüfen
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    if pattern.match(date_string):
        return True
    else:
        return False

def get_date(days_ago):
    fname = get_function_name()
    if validate_date(days_ago):
        today = date.fromisoformat(args.date)
        return today.strftime("%Y-%m-%d")
    else:
        if days_ago:
            days_ago = int(days_ago)
            if days_ago > 0:
                today = date.today()
                return today.strftime("%Y-%m-%d")
            else:
                today = date.today()
                delta = timedelta(days=abs(days_ago))
                return (today - delta).strftime("%Y-%m-%d")
        else:
            return date.today().strftime("%Y-%m-%d")

def get_total_time(project_id, date_str, cursor):
    fname = get_function_name()
    # Datum in datetime-Objekt konvertieren
    date = datetime.strptime(date_str, "%Y-%m-%d")

    # Alle Einträge aus der Tabelle entries mit passender project_id und Datum auswählen
    cursor.execute(HCWR_GLOBALS.DB_QUERIES.hcwrd_select, 
                   (project_id, date, date + timedelta(days=1)))

    # Ergebnis abrufen
    entries = cursor.fetchall()

    # Gesamtzeit in Sekunden berechnen
    #total_time = int(sum((datetime.strptime(entry[3][:19], '%Y-%m-%d %H:%M:%S') - datetime.strptime(entry[2][:19], '%Y-%m-%d %H:%M:%S')).total_seconds() for entry in entries))
    total_time = int(sum(
        (parse_timestamp(entry[3]) - parse_timestamp(entry[2])).total_seconds()
        for entry in entries
    ))

    if HCWR_GLOBALS.DBG_BREAK_POINT:
        dbg_res = debug_sql(HCWR_GLOBALS.DB_QUERIES.hcwrd_select, [project_id, date, date + timedelta(days=1)])
        info (f"{dbg_res}")
        info (f"entries = {entries};")
        info (f"total_time = {total_time};")

    return total_time


def get_weekly_total_time(project_id, start_date, kw, cursor):
    fname = get_function_name()
    # Wenn kein Startdatum angegeben ist, setze das Startdatum auf Montag der Kalenderwoche
    if not start_date:
        date = datetime.strptime(kw + "-1", "%Y-%W-%w")
        start_date = (date - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\start_date = {start_date}")        
    # Gesamtzeit von Montag bis Sonntag berechnen
    total_time = 0
    for i in range(7):
        day = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        tresult = get_total_time(project_id, day.strftime("%Y-%m-%d"), cursor)
        total_time += tresult
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"day = {day}")        
            info(f"Before: total_time = {total_time}")        
            info(f"{day} => tresult: {tresult}")
            info(f"After: total_time = {total_time}")        
    
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"total_time = {total_time}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            sys.exit(0)

    return total_time


def to_seconds(time_str):
    fname = get_function_name()
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

def to_time_format(total_seconds):
    fname = get_function_name()
    hours, remainder = divmod(total_seconds, 3600)
    debug (f"hours, remainder => {hours}, {remainder}")
    minutes, seconds = divmod(remainder, 60)
    debug (f"minutes, seconds => {minutes}, {seconds}")
    result = f'{hours:02}:{minutes:02}:{seconds:02}'
    debug (f"result to_time_format => {total_seconds} = result")
    return result

def get_monday_of_week(kw, year):
    fname = get_function_name()
    # Monday is 1, Sunday is 7 in ISO format
    monday = date.fromisocalendar(year, kw, 1)
    return monday.strftime("%Y-%m-%d")


def get_kw_overhours(conn=None, kw=None):
    fname = get_function_name()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nkw = {kw}")

    times = []

    # KW des 1. Arbeitstages
    firstday = HCWR_GLOBALS.CFG.get('Onboarding', 'firstday')
    year, week = get_calendar_week(firstday)
    year_now = date.today().year
    if year != year_now:
        first_kw = 1
    else:
        first_kw = week
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info (f"first_kw = {first_kw}")
    for i in range(first_kw, kw + 1):
        result = get_kw_overhours_add(conn, i, None, True, None, None)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info (f"result = {result}")
        for line in result:
            if 'KW Zeitkonto' in line:
                time_str = line.split()[2]
                debug (time_str)
                times.append(time_str)
        progress_bar(HCWR_GLOBALS.PBAR_VAL,HCWR_GLOBALS.PBAR_MAX)
        HCWR_GLOBALS.PBAR_VAL += 1

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"times = {times}")

    sum_seconds = 0

    for t in times:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"t => {t} => t Seconds=> {t}")
        sum_seconds += int(t)

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"sum_seconds => {sum_seconds}")

    sign = "+"
    if sum_seconds < 0:
        sign = "-"
    result = (sum_seconds*int(str(f"{sign}1")))
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"sign = {sign}, result = {result}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()
            sys.exit(0)
    return sign, result

def get_kw_overhours_add(conn=None, kw=None, zk=None, za=None, date=None, t=None):
    fname = get_function_name()

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}: kw={kw}, zk={zk}, za={za}, date={date}, t={t}")

    if kw:
        year = datetime.now().year
        monday_str = get_monday_of_week(kw, year)
        if not date:
            date = monday_str
    else:
        if not date:
            date = datetime.today().strftime("%Y-%m-%d")
        else:
            date = get_date(date)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    total_work_time = 0
    total_zeitkonto_adjust = 0

    for project in projects:

        project_id = project[0]
        project_name = project[2]

        if kw:
            total_time = get_weekly_total_time(project_id, date, kw, cursor)
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"--------------------------------------------------------\nkw {kw}")
                info(f"kw = {kw}")
                info(f"date = {date}")
                info(f"project_id = {project_id}")
                info(f"total_time = {total_time}")
                prompt = "Enter für fortfahren oder N für Nein "
                answer = input_with_prefill(prompt, "", '')
                if answer in ("N", "n"):
                    show_process_route()
                    sys.exit(0)
        else:
            total_time = get_total_time(project_id, date)
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"########################################################\nkw {kw}")
                info(f"kw = {kw}")
                info(f"date = {date}")
                info(f"project_id = {project_id}")
                info(f"total_time = {total_time}")
                prompt = "Enter für fortfahren oder N für Nein "
                answer = input_with_prefill(prompt, "", '')
                if answer in ("N", "n"):
                    show_process_route()
                    sys.exit(0)

        # ------------------------------------------------------
        # BUGFIX: ZKA Zeitkonto Abzug/Auszahlung
        # Arbeitszeit vs Zeitkonto-Korrektur trennen
        # ZKA wird in hcwr über zk_minus bei >0 von
        # kw_stundenkonto -= zk_minus abgezogen
        # wird hier in HCWR_GLOBALS.ZKA_ADDJUSTMENT
        # gespeichert und erst in hcwr bei zk_minus
        # Berechnung berücksichtig, wenn zk_minus == 0 ist,
        # weil man gerade in einer späteren KW als der,
        # wo ZKA eingetragen wurde, ein Wochenfazit erstellt.
        # Sonst falsche Werte rauskommen !!!
        # Ist ein Workaround, das funktioniert!!!
        # ------------------------------------------------------
        if "Zeitkonto Abzug" in project_name:
            total_zeitkonto_adjust -= total_time
            HCWR_GLOBALS.ZKA_ADDJUSTMENT += total_time
        else:
            total_work_time += total_time

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{project_name} -> {total_time}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"total_time = {total_time}")
        info(f"total_work_time = {total_work_time}")
        info(f"total_zeitkonto_adjust = {total_zeitkonto_adjust}")

    weekhours = int(float(HCWR_GLOBALS.CFG.get('General', 'weekhours')) * 3600)

    if kw:
        overhours = total_work_time - weekhours

        p = "+" if overhours >= 0 else "-"

        lines = []

        if not t and not zk:
            lines.append(f"KW {kw}: {int(total_work_time)}")
            lines.append(f"KW Zeitkonto: {int(overhours)}")
            result = lines

        elif t and not zk:
            lines.append(f"KW {kw}: {int(total_work_time)}")
            result = lines

        elif not t and zk:
            result = [p, overhours]

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"result = {result}")
        else:
            return result
                
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            prompt = "Enter für fortfahren oder N für Nein "
            answer = input_with_prefill(prompt, "", '')
            if answer in ("N", "n"):
                show_process_route()
                sys.exit(0)
            else:
                return result

    else:
        print(f"{date} Total: {int(total_work_time)}")

    conn.close()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()
            sys.exit(0)
