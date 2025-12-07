# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_utils_mod.py
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
import readline
import shutil
import locale
import os
import grp
import getpass
import sys
import time
import itertools
from colorama import init, Fore, Style
init()

from datetime import datetime, date, timedelta
from decimal import Decimal
from decimal import Decimal, InvalidOperation

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route

# Set locale for decimal formatting
locale.setlocale(locale.LC_ALL, '')
HCWR_GLOBALS.DECIMAL_POINT = locale.localeconv()['decimal_point']

def hours_to_hms(hours_str, MODE=2):
    fname = get_function_name()

    hours = float(hours_str.replace(",", "."))
    td = timedelta(hours=hours)
    total_seconds = int(td.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if MODE == 3:
        return f"{h:02d}:{m:02d}:{s:02d}"
    elif MODE == 2:
        return f"{h:02d}:{m:02d}"
    elif MODE == 0:
        return f"{h:02d}"

def check_directory_exists(file_path):
    """Prüft ob ein Verzeichnis Pfad exsistiert und ein wirklich ein Verzeichnis ist!"""
    fname = get_function_name()
    directory = os.path.dirname(file_path)
    return os.path.isdir(directory)

def command_exists(cmd: str) -> bool:
    """Prüft, ob ein Shell‑Befehl im PATH vorhanden ist."""
    fname = get_function_name()
    return shutil.which(cmd) is not None

def which_path(cmd: str) -> str | None:
    """Gibt den absoluten Pfad zum Befehl zurück oder None."""
    fname = get_function_name()
    return shutil.which(cmd)

def format_decimal(value):
    """Formatiert einen Dezimalwert entsprechend dem Gebietsschema, entfernt unnötige Nullen und gibt ‚0‘ für Null zurück."""
    fname = get_function_name()
    if value == 0 or value == 0.0:
        return "0"

    formatted_value = f"{value:.1f}".replace(".", HCWR_GLOBALS.DECIMAL_POINT)
    if int(HCWR_GLOBALS.DBG_LEVEL)==1:
        debug(f"from format_decimal: formatted_value = {formatted_value}")
    if formatted_value.endswith(f"{HCWR_GLOBALS.DECIMAL_POINT}0"):
        if int(HCWR_GLOBALS.DBG_LEVEL)==1:
            debug(f"from format_decimal (endswith 0): formatted_value = {formatted_value}")
        return formatted_value[:-2]
    return formatted_value

def add_decimal_hours(datetime_str, dec_hours):
    fname = get_function_name()
    # Datum string → datetime Objekt
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    # Decimal → float, aber genau genug für Stunden/Minuten
    h = Decimal(dec_hours)

    # Ganze Stunden & Minuten extrahieren
    hours = int(h)                       # z.B. 8
    minutes = int((h - hours) * 60)      # z.B. 0

    return dt + timedelta(hours=hours, minutes=minutes)
    
def is_valid_ymd(date_str):
    """
    Prüft, ob date_str exakt dem Format YYYY-MM-DD entspricht.
    Liefert True/False.
    """
    fname = get_function_name()
    if not isinstance(date_str, str):
        return False
    
    try:
        # strptime akzeptiert nur exakte Formate
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        # zusätzlich strftime vergleichen, um führende Nullen zu erzwingen
        return parsed.strftime("%Y-%m-%d") == date_str
    except ValueError:
        return False

def get_wday_short_name(date_str):
    fname = get_function_name()
    # datum_str z. B. "2025-12-01"
    d = datetime.strptime(date_str, "%Y-%m-%d")
    tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    return tage[d.weekday()]

def input_with_prefill(prompt, prefill, end='\n'):
    fname = get_function_name()
    """Input Prompt, der die Möglichkeit bietet, das Value zu setzen umd es bearbeiten zu können."""
    def hook():
        fname = get_function_name()
        readline.insert_text(prefill)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    try:
        print(prompt, end=end, file=sys.stderr, flush=True)  # über stderr ausgeben
        return input()  # ohne Argument – sonst landet Prompt in stdout
    finally:
        readline.set_pre_input_hook()

def check_user_in_group(group_name):
    """
    Prüft, ob der aktuelle Benutzer Mitglied einer bestimmten Unix-Gruppe ist.

    Parameter:
        group_name (str): Der Name der zu überprüfenden Gruppe.

    Rückgabe:
        True, wenn der Benutzer Mitglied der Gruppe ist.

    Raises:
        ValueError: Wenn die Gruppe nicht existiert oder der Benutzer kein Mitglied ist.
    """
    fname = get_function_name()
    try:
        grp.getgrnam(group_name)  # Prüft, ob Gruppe existiert
    except KeyError:
        raise ValueError(f"❌ Gruppe '{group_name}' existiert nicht.")

    user = getpass.getuser()
    try:
        group_ids = os.getgrouplist(user, os.getgid())
    except OSError as e:
        raise ValueError(f"Fehler beim Abrufen der Gruppen für Benutzer '{user}': {e}")

    user_groups = [grp.getgrgid(gid).gr_name for gid in group_ids]

    if group_name in user_groups:
        return True
    else:
        raise ValueError(
            f"❌ Die Operation ist nicht erlaubt!\n"
            f"Benutzer '{user}' ist **nicht** Mitglied der Gruppe '{group_name}'."
        )

def version():
    """
    Gibt Versionsinformationen zum hecokwreport-Skript aus.

    Die Ausgabe enthält:
    - Die aktuelle Versionsnummer (aus der globalen VERSION-Variable)
    - Copyright-Hinweis
    - Lizenzinformation (GNU GPL >= v2)
    - Autorenangabe
    - Beschreibung des Skripts und seiner Abhängigkeiten

    Die Ausgabe erfolgt direkt auf die Standardausgabe.
    """
    fname = get_function_name()

    print(f"""\
Version: {HCWR_GLOBALS.VERSION}
Copyright (C) 2025 by Intevation GmbH
This program is free software under the GNU GPL (>=v2)
Authors:
  Christian Klose <cklose@intevation.de>
About:
  hecokwreport for weekly report generation from heco time.db
  in conjunction with hkwdreport, overhours
  Python3 Based Executable Script
""")

#  if wday is Krank, Urlaub, Feiertag
def has_wday_absence(conn, weekday_num, year, week):
    """
    Checks if there are any entries for 'Krank', 'Urlaub' or 'Feiertag' on a given weekday.

    :param conn: db connection
    :param weekday_num: '1' = Mo, '2' = Di, ..., '7' = So
    :param year: ISO year
    :param week: ISO calendar week
    :return: True if there are any such entries on that weekday
    """
    fname = get_function_name()

    sql = HCWR_GLOBALS.DB_QUERIES.wday_absence
    cursor = conn.cursor()
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        cursor.execute(sql, [week, week, weekday_num])
    else:
        cursor.execute(sql, [year, week, year, week, weekday_num])
    count = cursor.fetchone()[0]
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\ncount = {count}")
        show_process_route()
        sys.exit(0)

    return count > 0


def get_wday_diff(conn, wdays, year, week):
    """Collect and print weekday deviations only if there are any."""
    fname = get_function_name()

    lines = [""]
    default_comment = HCWR_GLOBALS.REMINDER_TXT

    for dayname, stunden in wdays.items():
        try:
            stunden = Decimal(stunden)
        except (InvalidOperation, TypeError):
            stunden = Decimal("0.0")

	# Map German weekday names to SQLite weekday numbers
        weekday_map = HCWR_GLOBALS.WEEKDAY_MAP
        weekday_num = weekday_map[dayname]

        # Skip if the day has only absence entries
        if has_wday_absence(conn, weekday_num, year, week):
            continue

        # Check for deviation from expected hours
        expected = Decimal(HCWR_GLOBALS.WDAYHOURS_MAP[dayname])

        # Prüfen ob Abweichung größer als ±HCWR_GLOBALS.WD_TOLERANCE
        lower_bound = expected * Decimal(1 - HCWR_GLOBALS.WD_TOLERANCE)
        upper_bound = expected * Decimal(1 + HCWR_GLOBALS.WD_TOLERANCE)

        if stunden < lower_bound or stunden > upper_bound:
            if stunden < 10 and stunden > 0:
                hourstr = f" {format_decimal(round(stunden, 2))}  {default_comment}"
            elif stunden == 0:
                hourstr = f" {format_decimal(round(stunden, 0))}  * Überstundenabbau ???"
            else:
                hourstr = f"{format_decimal(round(stunden, 2))}  {default_comment}"
            lines.append(f"Tagabweichung: {dayname}: {hourstr}")

    if lines:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            result = "\n".join(lines)
            info(f"{fname}:\nlines = {result}")
            show_process_route()
            sys.exit(0)
        return "\n".join(lines)

def chgrp(path, group_name):
    """
    Setzt die Gruppenberechtigung für die Berichtsdatei "path" auf die eingestelle Gruppe Default "intevation"
    """
    fname = get_function_name()
    try:
        gid = grp.getgrnam(group_name).gr_gid  # GID der Gruppe holen
        stat_info = os.stat(path)
        os.chown(path, stat_info.st_uid, gid)  # Besitzer bleibt gleich, Gruppe ändern
        os.chmod(path, 0o644)
        info(f"Gruppe von '{path}'geändert auf: ", group_name)
    except KeyError:
        print(f"Gruppe '{group_name}' existiert nicht.")
    except PermissionError:
        print("Keine Berechtigung, um die Gruppenzugehörigkeit zu ändern.")
    except Exception as e:
        print("Fehler:", e)


def progress_bar(pos, maxval, msg=""):
    """
    Zeichnet eine farbige Progressbar mit animiertem Spinner.
    Gesamtlänge: max 80 Zeichen
    Prozentzahl vorne, optionaler Text am Ende.
    """
    if not HCWR_GLOBALS.args.verbose and not HCWR_GLOBALS.args.dry_run:
        return

    SPINNER = itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"])
    # Sicherheitskorrektur
    if maxval <= 0:
        maxval = 1
    pct = (pos / maxval) * 100
    if pct > 100:
        pct = 100
    percent_str = f"{pct:6.2f}% "  # z.B. " 45.30% "
    
    spinner = next(SPINNER)

    # Reservierte Breite
    max_width = 73

    # Wie viel Platz bleibt für msg?
    msg_str = f" {msg}" if msg else ""

    # Breite der Progressbar
    bar_width = max_width - len(percent_str) - 4 # 2 Klammern + 2 Spaces

    if bar_width < 5:
        bar_width = 5  # Mindestbreite

    filled = int((pos / maxval) * bar_width)
    empty = bar_width - filled

    # Farbige Bereiche
    bar = (
        Fore.GREEN + "█" * filled +
        Fore.RED + "." * empty +
        Style.RESET_ALL
    )

    out = f"\r{percent_str}[{bar}  ]"

    # Kürzen falls >80 Zeichen
    out = out[:80]

    sys.stdout.write(out)
    sys.stdout.flush()
        
