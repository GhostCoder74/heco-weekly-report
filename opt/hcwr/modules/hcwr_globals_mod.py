# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_globals_mod.py 
# Authors:        Christian Klose <cklose@intevation.de>
#                 Raimund Renkert <rrenkert@intevation.de>
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)
# Copyright (c) 2024-2026 by Intevation GmbH
# SPDX-License-Identifier: GPL-2.0-or-later
#
# File version:   1.0.3
# 
# This file is part of "hcwr - heco Weekly Report"
# Do not remove this header.
# Wochenfazit URL:
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------------------
"""
Global runtime storage for CLI arguments and variables.
This module provides globally writable runtime variables
which can be accessed from all modules after initialization.
"""
import re
import os
import locale
import configparser
import importlib
import importlib.abc
import importlib.util
import sys

# Set locale for decimal formatting
locale.setlocale(locale.LC_ALL, '')

# Setze Pfad, wenn sqlite3_queries im Unterverzeichnis liegt (z. B. ./lib/)

    
# Setze Pfad, wenn sqlite3_queries im Unterverzeichnis liegt (z. B. ./lib/)
#script_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.insert(0, script_dir)

class myGlobals:
    args = None
    # The VERSION variable is important for version check
    VERSION = "2.0.3-beta"

    # Get Env variables:
    DBG_LEVEL = os.environ.get('DBG_LEVEL')
    DBG_BREAK_POINT = os.environ.get('DBG_BREAK_POINT')
    DBG_PROCESS_ROUTE = os.environ.get('DBG_PROCESS_ROUTE')
    DBG_CALL_TREE = []
    DBG_CALL_COUNT = {}
    DBG_PROCESS_ROUTE_MODE = 0
    DBG_BREAK_POINT_LINE = None
    if DBG_BREAK_POINT is None:
        DBG_BREAK_POINT = ""
    else:
        if ":" in DBG_BREAK_POINT:
            DBG_BREAK_POINT_LINE = DBG_BREAK_POINT.split(':')[1]
            DBG_BREAK_POINT = DBG_BREAK_POINT.split(':')[0]
    if DBG_PROCESS_ROUTE:
        DBG_PROCESS_ROUTE_MODE = DBG_PROCESS_ROUTE
        DBG_PROCESS_ROUTE = []
        DBG_PROCESS_ROUTE.append("myGlobals")

    if DBG_BREAK_POINT and DBG_PROCESS_ROUTE:
        if len(DBG_PROCESS_ROUTE)>0:
            print(f"DBG_PROCESS_ROUTE = {DBG_PROCESS_ROUTE}")
            print(f"DBG_PROCESS_ROUTE_MODE = {DBG_PROCESS_ROUTE_MODE}")
    GROUP = os.environ.get('GROUP')
    DATABASE = os.environ.get('DATABASE')
    DECIMAL_POINT = locale.localeconv()['decimal_point']

    # Calling App Name:
    PROC_NAME = os.path.basename(sys.argv[0])
    # Globale Standardwerte für Host "hq"
    SSH_HOST = "hq"
    SSH_HOSTNAME = "euarne.intevation.de"
    SSH_IDENTITY_FILE = "~/.ssh/id_rsa"
    
    # Default Konstante
    CFG = configparser.ConfigParser()
    CFG.optionxform = str

    # Default Konstanter Pfad zur Config des Users
    CFG_FILE = os.path.expanduser("~/.heco/hcwr.conf")
    OLD_CFG_PATH = os.path.expanduser("~/.config/hkwreport.conf")

    # Default DB Standardwerte
    DBMS = importlib.import_module('sqlite3')
    DB_QUERIES = importlib.import_module('hcwr_sqlite_queries_sql')

    # Default Intevation Konstanten:
    # werden durch lokale Config des User neu gesetzt falls diese in der Config stehen, siehe get_config
    DB_KEYWORD_ID_PATH = os.path.expanduser("~/.heco/keyword_id.db")
    KW_REPORT_BASE_DIR = "/home/intevation/doc/Wochenberichte" # Wird für 'kw_report_dir' gebraucht, siehe weiter unten
    SQL_TEMPLATE = "/Home/projects/Intern/hecokwreport.hg/template/heco.projects.sql"
    DEFAULT_SQL_TEMPLATE = SQL_TEMPLATE
    WF_CHECK_PATH = "/home/activities/vorlagen/werkbank-wochenfazit-2024/2024-w46/wochenfazit.py"
    DEFAULT_WF_CHECK_PATH = WF_CHECK_PATH

    CONFIG_KEY_TO_GLOBAL_VAR = {
        "db_keyword_id_path": "DB_KEYWORD_ID_PATH",
        "kw_report_base_dir": "KW_REPORT_BASE_DIR",
        "sql_template": "SQL_TEMPLATE",
        "wf_check_path": "WF_CHECK_PATH",
    }
    # Tagabweichungstolleranz von ±20% 
    WD_TOLERANCE = float(0.2) 
    
    # Ausfüll Erinnerungstext:
    REMINDER_TXT = "* Bitte noch ausfüllen !!!"

    # Mapping der Config-Schlüssel zu globalen Variablennamen
    # Default Config Example Kommentarem, welche in die Config eingetragen werden
    CONFIG_EXAMPLES = {
        "General": [
            "# Examples:",
            "# Vorname Nachname:",
            "# fullname = John Doe\n#",
            "# Wöchentliche Sollarbeitszeit in Stunden",
            "# weekhours = 40\n#",
            "# Basisverzeichnis für Wochenberichte",
            "# Default: /home/intevation/doc/Wochenberichte\n#",
            "# kw_report_base_dir = /home/intevation/doc/Wochenberichte\n#",
            "# Pfad zur SQL-Vorlage",
            "# Default: /home/projects/Intern/hecokwreport.hg/template/heco.projects.sql\n#",
            "# sql_template = /home/projects/Intern/hecokwreport.hg/template/heco.projects.sql\n#",
            "# Pfad zur Workflow-Checkdatei",
            "# Default: /home/activities/vorlagen/werkbank-wochenfazit-2024/2024-w46/wochenfazit.py\n#",
            "# wf_check_path = /home/activities/vorlagen/werkbank-wochenfazit-2024/2024-w46/wochenfazit.py\n#",
            "# Ob UUK-Einträge angezeigt werden sollen (none/true/false)",
            "# Default: None or True = enabled, False = disabled",
            "# show_uuk = True\n#\n",
            "# My tasks-Einträge einfügen unter:",
            "# [ Für uns miterreicht habe ich ]",
            "# insert_tasks = (none/true/false)",
            "# Default: None or False = disabled, True = enabled",
            "# insert_tasks = false\n#\n",
        ],
        "Database": [
            "# Examples:",
            "# Unterstützte Datenbanken",
            "# Default: sqliste3\n#",
            "# dbms = sqlite3\n#",
            "# Pfad zur SQLite-Datenbankdatei (nur relevant, wenn dbms = sqlite3)",
            "# Default: ~/.heco/time.db\n#",
            "# dbpath = ~/.heco/time.db\n#",
            "# Falls dbms = pg: weitere Verbindungsparameter könnten hier ergänzt werden",
            "# dbpath = postgresql://heco:heco@localhost:54322/heco\n#",
            "# Pfad zur Datenbank mit Keyword-IDs",
            "# Default: ~/.heco/keyword_id.db\n#",
            "# db_keyword_id_path = ~/.heco/keyword_id.db\n#",
            "# Wo im String soll das Keyword erwartet werden?",
            "# Values: Am Anfang des Strings = ^, 1, beginning, first\n# oder irgendwo: None, *, any oder $, end, last oder eigener Regex String",
            "# Default: None\n#",
            "# EXAMPLES:\n#",
            "# PATTERN muss am Anfang stehen\n"
            "# keyword_place = ^\n"
            "# keyword_place = 1\n"
            "# keyword_place = beginning\n"
            "# keyword_place = first\n#\n"
            "# PATTERN muss am Ende stehen\n"
            "# keyword_place = $\n"
            "# keyword_place = end\n"
            "# keyword_place = last\n#\n"
            "# PATTERN kann irgendwo stehen\n"
            "# keyword_place = None\n"
            "# keyword_place = *\n"
            "# keyword_place = any\n"
        ],
        "Workdays": [
            "# Examples:",
            "# Arbeitstage mit zugehörigen Stundenwerten (z. B. für reduzierte Arbeitszeiten)",
            "# Default: Mo-Fr = 8.0\n#",
            "# Default: Sa-So = 0.0\n#",
            "# Mo = 8.0",
            "# Di = 8.0",
            "# Mi = 8.0",
            "# Do = 8.0",
            "# Fr = 8.0",
            "# Sa = 0.0",
            "# So = 0.0\n#\n"
        ],
        "Onboarding": [
            "# Example:",
            "# Erster Arbeitstag im Format YYYY-MM-DD",
            "# firstday = 2023-01-02\n#\n"
        ]
    }

    # Pattern
    CONTRACT_PATTERN = re.compile(r"^([^#:]+)[ ]+#([1-9][0-9]{0,4}):$")
    # SEARCH_EXCLUDE for function "my_tasks" in ../modules/hcwr_tasks_mod.py
    SEARCH_EXCLUDE = "\!C=Temp|\!C=Feiertag|\!C=Urlaub|\!C=Krank*|\!C=Zeitkonto*|\!C=Privat"
    # Prüft, ob ein String eine Uhrzeit im Format HH:MM oder HH:MM:SS enthält:
    REGEX_TIME = re.compile(r"\b([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?\b")

    # Prüft, ob ein String Datum + Uhrzeit enthält –
    # Format YYYY-MM-DD HH:MM oder YYYY-MM-DD HH:MM:SS:
    REGEX_DATETIME = re.compile(
        r"\b(20\d{2}|19\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s"
        r"([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?\b"
    )

    # Mapping of keys to projects
    MAPPING = {
        "temp": ["Temp"],
        "feiertag": ["Feiertag"],
        "urlaub": ["Urlaub"],
        "krank": ["Krank"],
        "zk_minus": ["Zeitkonto Abzug/Ausgezahlt"],
        "privat": ["Privat"],
        "zkue": ["Zeitkonto Übertrag vom Vorjahr"]
    }

    # Default Setting for projects_id_map
    PROJECTS_ID_MAP = {
            "Marketing": 310,
            "Akquise#": 311,
            "Andere Organisationen": 312,
            "Allgemein und Streut*": 313,
            "Auftrag#": 320,
            "Organisation": 321,
            "Sacharbeit abrechenbar": 322,
            "Sacharbeit andere*": 323,
            "Selbstorganisation": 330,
            "Qualifikation": 331,
            "regel. Arbeitsorganisation*": 332,
            "Unterstützung": 340,
            "Buchhaltung": 341,
            "IT-Infrastruktur": 342,
            "Büro": 343,
            "Personalmarketing und -entwicklung": 344,
            "Organisieren und verbessern*": 345,
            "Leitung": 350,
            "Menschen fördern": 351,
            "Unternehmen*": 352
    }
    INTERN_PROJEKT_ID_MAP = {
            'Temp'                          :[1,'X'  ,'X'   , 'Temp'],
            'Feiertag'                      :[2,'000','PH'  , 'Feiertag'],          # Public Holiday (Gesetzlicher Feiertag)
            'Urlaub'                        :[3,'001','VAC' , 'Urlaub'],            # Vacation       (Urlaubstag)
            'Krank'                         :[4,'002','AU'  , 'AU'],                # AU             (Arbeitsunfähigkeit)
            'Krankengeldbezug'              :[5,'003','KG'  , 'Krankengeldbezug'],   
            'Zeitkonto Übertrag vom Vorjahr':[6,'004','ZKÜ' , 'Zeitkonto Übertrag'],
            'Privat'                        :[7,'005','PRIV', 'Privat'],
            'Zeitkonto Abzug/Ausgezahlt'    :[8,'006','ZKA' , 'Zeitkonto Abzug']
    }
    # Example:
    # WDAYHOURS_MAP = {
    #     "Mo": 8.5,
    #     "Di": 8.5,
    #     "Mi": 8.5,
    #     "Do": 8.5,
    #     "Fr": 6.0,
    #     "Sa": 0.0,
    #     "So": 0.0
    # }
    WDAYHOURS_MAP = {}

    MONDAY = 0
    SUNDAY = 0

    WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
    WEEKDAY_MAP = {"Mo": "1", "Di": "2", "Mi": "3", "Do": "4", "Fr": "5", "Sa": "6", "So": "7"}
    SIGN = None

    CONTRACT_HOURS = 0
    KW_REPORT_DIR = None
    KW_REPORT_FILE = None

    PBAR_MAX = 100
    PBAR_VAL = 0

HCWR_GLOBALS = myGlobals()

# Debugging:
if not HCWR_GLOBALS.DBG_LEVEL:
    HCWR_GLOBALS.DBG_LEVEL = 0

# HCWR_GLOBALS.CONFIG_EXAMPLES um Section ProjectIDs erweitern:
if "ProjectIDs" not in HCWR_GLOBALS.CONFIG_EXAMPLES:
    HCWR_GLOBALS.CONFIG_EXAMPLES['ProjectIDs'] = ["# Defaults:"]
    for lbl, pid in HCWR_GLOBALS.PROJECTS_ID_MAP.items():
        HCWR_GLOBALS.CONFIG_EXAMPLES['ProjectIDs'].append(f"# {lbl} = {pid}")

    HCWR_GLOBALS.CONFIG_EXAMPLES['ProjectIDs'].append(f"# \n")

