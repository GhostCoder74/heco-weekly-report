# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_hcwrd_mod.py
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
import sys
import datetime
from datetime import datetime, timedelta, date
from decimal import Decimal
from decimal import Decimal, InvalidOperation
import re

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_config_mod import get_calendar_week
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route
from hcwr_utils_mod import progress_bar

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
    total_time = sum((datetime.strptime(entry[3][:19], '%Y-%m-%d %H:%M:%S') - datetime.strptime(entry[2][:19], '%Y-%m-%d %H:%M:%S')).total_seconds() for entry in entries)

    # Zeit in Stunden, Minuten und Sekunden umwandeln
    hours, remainder = divmod(total_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Ausgabe der Gesamtzeit als String im Format "hh:mm:ss"
    total_time_str = '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))
    return total_time


def get_weekly_total_time(project_id, start_date, kw, cursor):
    fname = get_function_name()
    # Wenn kein Startdatum angegeben ist, setze das Startdatum auf Montag der Kalenderwoche
    if not start_date:
        date = datetime.strptime(kw + "-1", "%Y-%W-%w")
        #date = datetime.strptime(kw, "%Y-%W-%w")
        start_date = (date - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Gesamtzeit von Montag bis Sonntag berechnen
    total_time = 0
    for i in range(7):
        day = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        tresult = get_total_time(project_id, day.strftime("%Y-%m-%d"), cursor)
        total_time += tresult
        debug(f"{day} => tresult: {tresult}")
    

    debug(f"total_time = {total_time}")

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
        debug (f"t => {t} => t Seconds=> {to_seconds(t)}")
        if t.startswith('-'):
            t = t[1:]
            debug (t)
            sum_seconds -= to_seconds(t)
        else:
            t = t[1:]
            debug (t)
            sum_seconds += to_seconds(t)

        debug (f"sum_seconds => {sum_seconds}")

    sign = "+"
    hours, remainder = divmod(sum_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if sum_seconds < 0:
        sign = "-"
    result = float(Decimal(hours)+Decimal(minutes)/60*int(str(f"{sign}1")))
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"sign, result = {sign}, {result}")
        show_process_route()
        sys.exit(0)
    return sign, result

def get_kw_overhours_add(conn=None,kw=None,zk=None,za=None,date=None,t=None):
    fname = get_function_name()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nkw = {kw}, zk = {zk}, za = {za}, date = {date}, t = {t}")
    if kw:
        # Wenn keine Startdatum angegeben ist, setze das Startdatum auf Montag der Kalenderwoche
        # Definiere das Jahr und die Kalenderwoche
        year = datetime.now().year
        
        # Berechne den Montag der Kalenderwoche
        monday = datetime.strptime(f"{year}-W{kw}-1", "%Y-W%W-%w").date()

        # Gib das Datum im Format "Y-m-d" zurück
        monday_str = get_monday_of_week(kw, year)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"monday = {monday}")
            info(f"monday_str = {monday_str}")
            
        if not date:
            date = monday_str
    else:
        if not date:
            date = datetime.today().strftime("%Y-%m-%d")
        else:
            date = get_date(date)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"date = {date}")        

    # Cursor-Objekt erstellen
    cursor = conn.cursor()

    # Alle Einträge aus der Tabelle projects auswählen
    cursor.execute("SELECT * FROM projects")

    # Ergebnis abrufen
    projects = cursor.fetchall()

    total_kw_time = 0
    # Ausgabe der Projekte
    day_total_time = 0
    for project in projects:
        project_id = project[0]
        project_name = project[2]
        if kw:
            total_time = get_weekly_total_time(project_id, date, kw, cursor)
        else:
            total_time = get_total_time(project_id, date)
            day_total_time += total_time

        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        if "Zeitkonto Abzug" in project_name:
            sign = "-"
        else:
            sign = ""

        #if total_time >= 3600:
        #if not t and not zk:
        #    print(f"{project_name}: {sign}{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        if not "Zeitkonto Abzug" in project_name:
            total_kw_time += total_time
        if za and "Zeitkonto Abzug" in project_name:
            total_kw_time -= total_time

    weekhours = float(HCWR_GLOBALS.CFG.get('General', 'weekhours')) * 3600
    firstday = HCWR_GLOBALS.CFG.get('Onboarding', 'firstday') 
    if kw:
        #weekhours = 144000    # 40 Stunden Woche in Sekunden
        if total_kw_time > weekhours:
            p = '+'
            overhours = total_kw_time - weekhours # Ueberstunden in Sekunden
            whours, wremainder = divmod(overhours, 3600)
            wminutes, wseconds = divmod(wremainder, 60)
        else:
            p = '-'
            overhours = weekhours - total_kw_time # um Ueberstunden in Sekunden fuer minus Zeiten zu erhalten
            whours, wremainder = divmod(overhours, 3600)
            wminutes, wseconds = divmod(wremainder, 60)

        hours, remainder = divmod(total_kw_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        lines = []
        if not t and not zk:    
            lines.append(f"KW {kw}: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            lines.append(f"KW Zeitkonto: {p}{int(whours):02d}:{int(wminutes):02d}:{int(wseconds):02d}")
            return lines
        elif t and not zk:
            lines.append(f"KW {kw}: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            return lines
        elif not t and zk:
            return p, float(Decimal(whours)+Decimal(wminutes)/60*int(str(f"{p}1")))
        
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            show_process_route()
            sys.exit(0)
    else:
        hours, remainder = divmod(day_total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"{date} Total: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")

    # Datenbankverbindung schließen
    conn.close()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)