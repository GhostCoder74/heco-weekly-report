# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_config_mod.py
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
import re
import os
import configparser
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP
import inspect

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route, debug_sql
from hcwr_utils_mod import  input_with_prefill

def update_config_comments():

    fname = get_function_name()
    # Neuen Dateiinhalt als Liste von Zeilen aufbauen
    new_lines = []
    added = False
    for section, comments in HCWR_GLOBALS.CONFIG_EXAMPLES.items():
        if not HCWR_GLOBALS.CFG.has_section(section):
            HCWR_GLOBALS.CFG.add_section(section)
            added = True

        # Kommentarblock schreiben
        new_lines.append(f"[{section}]\n")
        for line in comments:
            new_lines.append(f"{line}\n")

        # Key-Value-Paare, wenn vorhanden
        for key, value in HCWR_GLOBALS.CFG.items(section):
            new_lines.append(f"{key} = {value}\n")

        new_lines.append("\n")  # Leerzeile zwischen Sektionen

    # Datei überschreiben
    with open(HCWR_GLOBALS.CFG_FILE,"w") as f:
        f.writelines(new_lines)

    if added:
        info(f"Example-Kommentare in {HCWR_GLOBALS.CFG_FILE} aktualisiert!")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nnew_lines = {new_lines}")
        show_process_route()
        sys.exit(0)


def extract_name():
    """
    Holt den Namen aus der Umgebungsvariable "EMAIL"

    TODO: get_name_from_config()
    """
    fname = get_function_name()
    email_string = os.environ.get('EMAIL')
    if email_string and not HCWR_GLOBALS.CFG.has_option("General", "fullname"):
        match = re.match(r"([\w\s]+)", email_string)
        if not fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            if match:
                return match.group(1).strip()
        else:
            info(f"{fname}:\nName = {match.group(1).strip()}")
            show_process_route()
            sys.exit(0)
    else:
        if not fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            # TODO: get_name_from_config()
            return get_name_from_config()
        else:
            info(f"{fname}:\nName = {get_name_from_config()}")
            show_process_route()
            sys.exit(0)

# TODO: Hole den Namen aus der Config "~.config/hkwreport.conf"
#       Siehe auch "get_config()"
#
def get_name_from_config():
    """
    Holt den Namen aus der Config "HCWR_GLOBALS.CFG_FILE"
    """
    fname = get_function_name()
    # ....
    if HCWR_GLOBALS.CFG.has_option("General", "fullname"):
        HCWR_GLOBALS.FULLNAME = HCWR_GLOBALS.CFG.get("General", "fullname")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info("{fname}:\nHCWR_GLOBALS.FULLNAME = {HCWR_GLOBALS.FULLNAME}")
        show_process_route()
        sys.exit(0)
    return HCWR_GLOBALS.FULLNAME

def get_or_create_projects_id_map():
    """
    Erstellt oder holt sich die ID Map zu den Projects für heco time.db und speichert sie in die Config
    """
    fname = get_function_name()

    if os.path.exists(HCWR_GLOBALS.CFG_FILE):
        HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)
    else:
        HCWR_GLOBALS.CFG['ProjectIDs'] = {}

    if 'ProjectIDs' not in HCWR_GLOBALS.CFG:
        info("Es fehlen noch Config Einträge zu : ", 'ProjectIDs')
        HCWR_GLOBALS.CFG['ProjectIDs'] = {}

    # Wenn Map-Einträge fehlen, abfragen
    pids = HCWR_GLOBALS.PROJECTS_ID_MAP
    updated = False
    set_default_map = False
    missing_map = False
    for ptitel, pid in pids.items():
        if ptitel not in HCWR_GLOBALS.CFG['ProjectIDs']:
            missing_map = True
    if missing_map:
        prompt  = (f"Möchten sie die Default Map-Einträg für die Projekt IDs verwenden? [J/n]: ")
        answer = input_with_prefill(prompt, "", "")
        print("\n")
        if answer in ("", "j", "ja", "y", "yes"):
            set_default_map = True
    else:
        set_default_map = True

    for ptitel, pid in pids.items():
        if ptitel not in HCWR_GLOBALS.CFG['ProjectIDs']:
            if set_default_map == False:
                prompt = (f"Titel: {ptitel} = ID: ")
                value = input_with_prefill(prompt, str(pid)).strip()
                HCWR_GLOBALS.CFG['ProjectIDs'][ptitel] = value
            else:
                HCWR_GLOBALS.CFG['ProjectIDs'][ptitel] = str(pid)
            updated = True

    # Falls etwas geändert wurde, Config schreiben
    if updated:
        update_config(HCWR_GLOBALS.CFG)

    # Map in Float-Werte konvertieren und zurückgeben
    new_projects_id_map = {
        ptitel: int(HCWR_GLOBALS.CFG['ProjectIDs'][ptitel])
        for ptitel in HCWR_GLOBALS.CFG['ProjectIDs']
    }
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug(f"new_projects_id_map = {new_projects_id_map}")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nnew_projects_id_map = {new_projects_id_map}")
        show_process_route()
        sys.exit(0)

    return new_projects_id_map

def get_or_create_wdayhours_map():
    """
    Erstellt oder holt sich die Wochentag-Arbeitsstunden-Map, wird benötigt umd Tageabweichungen zu prüfen.
    """

    fname = get_function_name()

    if os.path.exists(HCWR_GLOBALS.CFG_FILE):
        HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)
    else:
        HCWR_GLOBALS.CFG['Workdays'] = {}

    if 'Workdays' not in HCWR_GLOBALS.CFG:
        info("Es fehlen noch Config Einträge zu : ", 'Workdays')
        HCWR_GLOBALS.CFG['Workdays'] = {}

    # Wenn Map-Einträge fehlen, abfragen
    weekdays = HCWR_GLOBALS.WEEKDAYS
    updated = False
    for day in weekdays:
        default_hours = 8.0
        if day not in HCWR_GLOBALS.CFG['Workdays']:
            while True:
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"day = {day}")
                    prompt = "Enter für fortfahren oder N für Nein "
                    answer = input_with_prefill(prompt, "", '')
                    if answer in ("N", "n"):
                        show_process_route()
                if day in ["Sa", "So"]:
                    default_hours = 0.0
                    value = default_hours
                else:
                    prompt = (f"Wieviele Stunden arbeiten Sie am {day}? (z. B. 8.0): ")
                    value = input_with_prefill(prompt, str(default_hours)).strip()
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"value = {value}")
                    prompt = "Enter für fortfahren oder N für Nein "
                    answer = input_with_prefill(prompt, "", '')
                    if answer in ("N", "n"):
                        show_process_route()
                if value == None:
                    print("Eingabe darf nicht leer sein.")
                    continue
                try:
                    float_val = float(value)
                    HCWR_GLOBALS.CFG['Workdays'][day] = str(float_val)
                    updated = True
                    break
                except ValueError:
                    print("Bitte eine gültige Zahl eingeben (z. B. 8.0 oder 7.5).")

    # Falls etwas geändert wurde, Config schreiben
    if updated:
        update_config(HCWR_GLOBALS.CFG)
    # Map in Float-Werte konvertieren und zurückgeben
    wdayhours_map = {day: float(HCWR_GLOBALS.CFG['Workdays'][day]) for day in weekdays}
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nwdayhours_map = {wdayhours_map}")
        show_process_route()

    return wdayhours_map

def set_default_cons(interactive=False):
    """
    Setzt die Path Kosntanten in der Config (Default oder interaktiv)
    """
    fname = get_function_name()

    HCWR_GLOBALS.CFG['Database']['db_keyword_id_path'] = HCWR_GLOBALS.DB_KEYWORD_ID_PATH
    HCWR_GLOBALS.CFG['General']['kw_report_base_dir'] = HCWR_GLOBALS.KW_REPORT_BASE_DIR
    HCWR_GLOBALS.CFG['General']['sql_template'] = HCWR_GLOBALS.SQL_TEMPLATE
    HCWR_GLOBALS.CFG['General']['wf_check_path'] = HCWR_GLOBALS.WF_CHECK_PATH
    if interactive:
        for sec, cons_path in [
            ("Database", "db_keyword_id_path"),
            ("General", "kw_report_base_dir"),
            ("General", "sql_template"),
            ("General", "wf_check_path")
        ]:
            prompt = (f"['{sec}']['{cons_path}']: ")
            value = input_with_prefill(prompt, HCWR_GLOBALS.CFG[sec].get(cons_path, ''))
            HCWR_GLOBALS.CFG[sec][cons_path] = value
            # globale Variable aktualisieren
            globals()[HCWR_GLOBALS.CONFIG_KEY_TO_GLOBAL_VAR[cons_path]] = value

    update_config(HCWR_GLOBALS.CFG)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nHCWR_GLOBALS.CFG = {HCWR_GLOBALS.CFG}")
        show_process_route()
        sys.exit(0)

def get_config(call_from=None):
    """
    Ließt bzw. initialisiert die Config "HCWR_GLOBALS.CFG_FILE"
    """
    fname = get_function_name()

    if int(HCWR_GLOBALS.DBG_LEVEL)<=0:
        stack = inspect.stack()
        caller = stack[1]  # Der direkte Aufrufer
        debug(f"Aufgerufen von: Zeile {caller.lineno}")
        if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
            debug(f"get_config was called from: {call_from}")
    if not os.path.exists(HCWR_GLOBALS.CFG_FILE):
        set_weekhours()
        set_first_workday()

    HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)

    if 'Onboarding' not in HCWR_GLOBALS.CFG or 'firstday' not in HCWR_GLOBALS.CFG['Onboarding']:
        info("Es fehlt noch Eintrag zum 1. Arbeitstag bzw. 1. Tag der Nutzung", '')
        set_first_workday()

    if 'General' not in HCWR_GLOBALS.CFG or 'weekhours' not in HCWR_GLOBALS.CFG['General']:
        info("Es fehlt noch Eintrag zu den Arbeitsstunden pro Kalendarwoche", '')
        set_weekhours()

    if 'Database' not in HCWR_GLOBALS.CFG or 'dbpath' not in HCWR_GLOBALS.CFG['Database']:
        info("Es fehlt noch der Pfad zur heco Datenbank", '')
        set_heco_db_path()

    # Nach den möglichen Änderungen nochmal lesen
    HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)

    # Konstanten einlesen, wenn vorhanden:
    # Konstante Pfade:
    if 'General' in HCWR_GLOBALS.CFG and 'Database' in HCWR_GLOBALS.CFG:
        if "db_keyword_id_path" in HCWR_GLOBALS.CFG['Database']:
            HCWR_GLOBALS.DB_KEYWORD_ID_PATH = os.path.expanduser(HCWR_GLOBALS.CFG['Database']['db_keyword_id_path'])
            if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
                debug(f"db_keyword_id_path = {HCWR_GLOBALS.DB_KEYWORD_ID_PATH}")
        if "kw_report_base_dir" in HCWR_GLOBALS.CFG['General']:
            HCWR_GLOBALS.KW_REPORT_BASE_DIR = os.path.expanduser(HCWR_GLOBALS.CFG['General']['kw_report_base_dir'])
            if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
                debug(f"kw_report_base_dir = {HCWR_GLOBALS.KW_REPORT_BASE_DIR}")
        if "sql_template" in HCWR_GLOBALS.CFG['General']:
            HCWR_GLOBALS.SQL_TEMPLATE = os.path.expanduser(HCWR_GLOBALS.CFG['General']['sql_template'])
            if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
                debug(f"sql_template = {HCWR_GLOBALS.SQL_TEMPLATE}")
        if "wf_check_path" in HCWR_GLOBALS.CFG['General']:
            HCWR_GLOBALS.WF_CHECK_PATH = os.path.expanduser(HCWR_GLOBALS.CFG['General']['wf_check_path'])
            if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
                debug(f"wf_check_path = {HCWR_GLOBALS.WF_CHECK_PATH}")

        if (
                call_from == "no_config"
                and not "kw_report_base_dir" in HCWR_GLOBALS.CFG['Database']
                and not "sql_template" in HCWR_GLOBALS.CFG['General']
                and not "wf_check_path" in HCWR_GLOBALS.CFG['General']
        ):
            prompt  = (f"Möchten sie die Default Path Konstanten für hecokwreport verwenden oder interaktiv setzen? [J / n /i = interactive]: ")
            answer = input_with_prefill(prompt, "", "")
            print("\n")
            if answer in ("", "i", "j", "ja", "y", "yes"):
                if answer == "i":
                    set_default_cons(True)
                else:
                    set_default_cons(False)

    weekhours = int(HCWR_GLOBALS.CFG['General']['weekhours'])
    HCWR_GLOBALS.args.database = os.path.expanduser(HCWR_GLOBALS.CFG['Database']['dbpath'])
    firstday = HCWR_GLOBALS.CFG['Onboarding']['firstday']
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug (f"firstday = {firstday}")
    year, week = get_calendar_week(firstday)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        if year != date.today().year:
             info(f"{fname}:\nweekhours = {weekhours}, week = 1")
        else:
             info(f"{fname}:\nweekhours = {weekhours}, week = {week}")
        show_process_route()
        sys.exit(0)

    if year != date.today().year:
        return weekhours, 1
    else:
        return weekhours, week

def set_weekhours():
    """
    Setzt in der Config die Wochenarbeitsstunden, wird zur Berechung von Über- bzw. Unterstunden benötigt.
    """
    fname = get_function_name()

    # Benutzer nach den Wochenstunden fragen
    weekhours = input("Bitte ihre Wochenarbeitsstunden eingeben: ")

    # Wochenstunden in Sekunden umwandeln
    weekhours_seconds = int(weekhours) * 3600

    # Neue Konfigurationsdatei erstellen
    if not "General" in HCWR_GLOBALS.CFG:
        HCWR_GLOBALS.CFG['General'] = {}
    if not "weekhours" in HCWR_GLOBALS.CFG['General']:
        HCWR_GLOBALS.CFG['General']['weekhours'] = str(weekhours_seconds // 3600)  # In Stunden speichern
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nweekhours = {HCWR_GLOBALS.CFG['General']['weekhours']}")
        show_process_route()
        sys.exit(0)
    # Konfigurationsdatei speichern
    update_config(HCWR_GLOBALS.CFG)

def set_heco_db_path():
    """
    Setzt den Pfad zur heco time.db -> "db_path"
    """
    fname = get_function_name()
    # Benutzer nach dem Pfad zur Datenbank fragen
    db_path = input_with_prefill("Bitte Pfad zu heco Datenbank eintragen: ", HCWR_GLOBALS.args.database)
    debug(f"db_path = {db_path}")

    if not "Database" in HCWR_GLOBALS.CFG:
        HCWR_GLOBALS.CFG['Database'] = {}
    if not "dbpath" in HCWR_GLOBALS.CFG['Database']:
        HCWR_GLOBALS.CFG['Database']['dbpath'] = db_path

    # Konfigurationsdatei speichern
    update_config(HCWR_GLOBALS.CFG)
    info(f"Config file updated with path: ", db_path)
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

def configure_interactive():
    """
    Gibt dem Benutzer die Config interaktive zu bearbeiten bzw. sich anzeigen zu lassen.
    """
    fname = get_function_name()
    info("Interaktive Konfigurationsbearbeitung:\n", "(Enter-Taste, um Wert zu behalten)\n")
    get_config("configure_interactive")
    HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)

    for section in HCWR_GLOBALS.CFG:
        set_val = True
        prompt = None
        if "ProjectIDs" in section:
            prompt  = (f"Möchten sie die bereits gesetzten Map-Einträg für die Projekt IDs bearbeiten? [j/N]: ")
        elif "Workdays" in section:
            prompt  = (f"Möchten sie die bereits gesetzten Arbeitsstunden pro Tag bearbeiten? [j/N]: ")
        elif "Onboarding" in section:
            prompt  = (f"Möchten sie den bereits gesetzten Tag des 1. Arbeitstages bzw. 1. Tag der Nutzung bearbeiten? [j/N]: ")
        elif "General" in section:
            prompt  = (f"Möchten sie die bereits gesetzten Wochenarbeitsstunden bearbeiten? [j/N]: ")
        elif "Database" in section:
            prompt  = (f"Möchten sie die bereits gesetzten Pfad der Datenbank bearbeiten? [j/N]: ")

        if prompt:
            answer = input_with_prefill(prompt, "", "")
            print ("\n")
            if answer in ("", "n", "nein", "n", " no"):
                set_val = False
        else:
            get_or_create_wdayhours_map()
            get_or_create_projects_id_map()

        for key in HCWR_GLOBALS.CFG[section]:
            current_value = HCWR_GLOBALS.CFG[section][key]
            if set_val:
                new_value = input_with_prefill(f"[{section}] {key}: ", current_value)
            else:
                if "ProjectIDs" in section:
                    info(f" {current_value} ->", f" {key}", f"[{section}]")
                else:
                    info(f" {key} :", f" {current_value}", f"[{section}]")
                new_value = current_value
            if new_value.strip() and new_value.strip() != current_value:
                HCWR_GLOBALS.CFG[section][key] = new_value.strip()
        if prompt:
            print ("\n")

    update_config(HCWR_GLOBALS.CFG)
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nHCWR_GLOBALS.CFG = {HCWR_GLOBALS.CFG}")
        show_process_route()
        sys.exit(0)

def set_first_workday():
    """
    Setzt den  1. Arbeitstag bzw. 1. Tag der Nutzung von heco time.db.
    Wichtig für die Stundenberechnung (Zeitkonto, Abwesendheit, Urlaub, etc.)
    """
    fname = get_function_name()
    if os.path.exists(HCWR_GLOBALS.CFG_FILE):
        HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)

    # Benutzer nach den ersten Arbeitstag fragen
    firstday = input("Bitte ihre 1. Arbeitstag bzw. 1. Tag der Nutzung eingeben (Format = YYYY-MM-DD): ")

    if not "Onboarding" in HCWR_GLOBALS.CFG:
        HCWR_GLOBALS.CFG['Onboarding'] = {}

    if not "firstday" in HCWR_GLOBALS.CFG['Onboarding']:
        HCWR_GLOBALS.CFG['Onboarding']['firstday'] = str(firstday)

    # Konfigurationsdatei speichern
    update_config(HCWR_GLOBALS.CFG)
    info(f"Config file updated with firstday: {firstday}")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

def update_config(new_config):
    """
    Vergleicht übergebenes ConfigParser-Objekt (new_config) mit der Datei
    und schreibt die Datei neu, wenn Änderungen vorhanden sind.
    """
    fname = get_function_name()
    # Originale Konfiguration aus Datei einlesen
    old_config = configparser.ConfigParser()
    old_config.optionxform = str

    if not os.path.exists(HCWR_GLOBALS.CFG_FILE):
        warning(f"Config file not found! Creating now: ", HCWR_GLOBALS.CFG_FILE, "Info")
        with open(HCWR_GLOBALS.CFG_FILE, 'w') as configfile:
            old_config.write(configfile)
    old_config.read(HCWR_GLOBALS.CFG_FILE)

    changed = False  # Flag, ob Änderungen erkannt wurden

    # Alle Sektionen und Keys aus dem neuen Config-Objekt prüfen
    for section in new_config.sections():
        if section not in old_config:
            old_config[section] = {}
            changed = True

        for key, value in new_config[section].items():
            if (
                section not in old_config or
                key not in old_config[section] or
                old_config[section][key] != value
            ):
                old_config[section][key] = value
                changed = True

    if changed:
        with open(HCWR_GLOBALS.CFG_FILE, 'w') as f:
            old_config.write(f)
        info(f"Konfiguration aktualisiert und gespeichert nach: ", HCWR_GLOBALS.CFG_FILE)
    else:
        info("Keine Änderungen an der Konfiguration vorgenommen.", "")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

def get_calendar_week(date_str):
    """
    Gibt die Kalenderwoche (ISO 8601) zu einem Datum im Format 'YYYY-MM-DD' zurück.
    Rückgabe: (jahr, kw) als Tuple
    """
    fname = get_function_name()
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        iso_year, iso_week, _ = date_obj.isocalendar()
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fname}:\niso_year = {iso_year}, iso_week = {iso_week}")
            show_process_route()
            sys.exit(0)
        return iso_year, iso_week
    except ValueError:
        raise ValueError("Ungültiges Datumsformat. Erwartet: YYYY-MM-DD")

# Determine current week and year if not provided
def parse_week_env(timestamp):
    """
    Liest die Umgebungsvariablen YEAR und WEEK/KW aus und setzt args.year und args.week entsprechend.
    Akzeptiert Formate wie:
        - WEEK=19
        - WEEK=2025/19
        - WEEK=2025-19
        - WEEK=19/2025
        - WEEK=19-2025
    """
    fname = get_function_name()

    YEAR = os.environ.get('YEAR')
    WEEK = os.environ.get('KW')
    if not WEEK:
        WEEK = os.environ.get('WEEK')

    isocal = timestamp.isocalendar()

    try:
        if WEEK:
            parts = WEEK.replace('-', '/').split('/')
            if len(parts) == 1 and len(parts[0])<3:
                # Nur Woche angegeben (YEAR ggf. separat)
                week = int(parts[0])
                if YEAR:
                    year = int(YEAR)
                else:
                    year = isocal[0]  # fallback: aktuelles Jahr
            elif len(parts) == 2 and ((len(parts[0])<3 and len(parts[1])==4) or (len(parts[1])<3 and len(parts[0])==4)):
                # YEAR/WEEK oder WEEK/YEAR
                a, b = parts
                if int(a) > 1000:
                    year, week = int(a), int(b)
                else:
                    week, year = int(a), int(b)
            else:
                raise ValueError(f"Ungültiges Format für WEEK: {WEEK}")

            HCWR_GLOBALS.args.year = year
            HCWR_GLOBALS.args.week = week

        elif YEAR:
            if len(str(YEAR))==4:
                HCWR_GLOBALS.args.year = int(YEAR)
            else:
                raise ValueError(f"Ungültiges Format für YEAR: {YEAR}")
            if not HCWR_GLOBALS.args.week:
                HCWR_GLOBALS.args.week = isocal[1]
        else:
            if not HCWR_GLOBALS.args.week:
                HCWR_GLOBALS.args.week = isocal[1]
            if not HCWR_GLOBALS.args.year:
                HCWR_GLOBALS.args.year = isocal[0]
    except Exception as e:
        warning(f"Fehler beim Parsen von WEEK/YEAR: ", e, "Error")
        show_process_route()
        sys.exit(1)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"HCWR_GLOBALS.args.week = {HCWR_GLOBALS.args.week}")
        info(f"HCWR_GLOBALS.args.year = {HCWR_GLOBALS.args.year}")
        show_process_route()
        sys.exit(0)

def isoweek(date_string, year, week):
    """
    SQLite Funktion für die Timestamps in heco time.db
    """
    fname = get_function_name()
    try:
        d = datetime.strptime(date_string, "%Y-%m-%d").isocalendar()
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fname}:\nd = {d}, year = {year}, week = {week}")
            show_process_route()
            sys.exit(0)

        return d[0] == int(year) and d[1] == int(week)
    except:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fname}:\nFailed!")
            show_process_route()
            sys.exit(0)
        return False

def get_week_hours(conn, year, week, first_week=None):
    """
    Returns total hours for Mo–Fr in the specified calendar week and year.

    :param conn: db connection
    :param year: integer (e.g. 2024)
    :param week: integer (1–53)
    :return: tuple of Decimal values (Mo, Di, Mi, Do, Fr, Sa, So)
    """
    fname = get_function_name()

    sql = HCWR_GLOBALS.DB_QUERIES.whours_sql + HCWR_GLOBALS.DB_QUERIES.wdayhours_sql_excl

    cursor = conn.cursor()
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        if first_week is None:
            cursor.execute(sql, [week, week])
        else:
            cursor.execute(sql, [first_week, week])
    else:
        if first_week is None:
            cursor.execute(sql, [year, week, year, week])
        else:
            cursor.execute(sql, [year, first_week, year, week])
    row = cursor.fetchone()
    if not row:
        warning(f"No Data","found","ERROR")
        show_process_route()
        sys.exit(1)
    elif int(HCWR_GLOBALS.DBG_LEVEL) == 60:
        debug(f"row = {row}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(Decimal(row[0]) if row and row[0] is not None else Decimal("0.0"))
        show_process_route()
        sys.exit(0)

    # Convert to Decimals and ensure fallback to 0.0 if None
    return Decimal(row[0]) if row and row[0] is not None else Decimal("0.0")

def get_weekday_hours_per_day(conn, year, week):
    """
    Returns total hours for Mo–Fr in the specified calendar week and year.

    :param conn: db connection
    :param year: integer (e.g. 2024)
    :param week: integer (1–53)
    :return: tuple of Decimal values (Mo, Di, Mi, Do, Fr, Sa, So)
    """
    fname = get_function_name()

    sql = HCWR_GLOBALS.DB_QUERIES.wdayhours_sql + HCWR_GLOBALS.DB_QUERIES.wdayhours_sql_excl
    #sql = HCWR_GLOBALS.DB_QUERIES.whours_sql + HCWR_GLOBALS.DB_QUERIES.wdayhours_sql_excl
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"sql = {debug_sql(sql, [week, year, week, year])}")

    cursor = conn.cursor()
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        cursor.execute(sql, [week, year, week, year])
    else:
        cursor.execute(sql, [year, week, year, week])
    row = cursor.fetchone()
    if not row:
        warning(f"No Data","found","ERROR")
        show_process_route()
        sys.exit(1)
    elif int(HCWR_GLOBALS.DBG_LEVEL) == 60:
        debug(f"row = {row}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(tuple(val if val is not None else 0 for val in row))
        show_process_route()
        sys.exit(0)

    # Convert to Decimals and ensure fallback to 0.0 if None

    return tuple(val if val is not None else 0 for val in row)
