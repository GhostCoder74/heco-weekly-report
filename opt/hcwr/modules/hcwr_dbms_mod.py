# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_dbms_mod.py
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
import importlib
import shutil
import subprocess
import re
import os
import sys
from decimal import Decimal
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
import colorama
from colorama import Fore, Style

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route, debug_sql
from hcwr_utils_mod import input_with_prefill
from hcwr_config_mod import update_config_comments, update_config, get_config

def init_heco(kw=None):
    """
    Initialisiert eine heco time.db und führt ein Projekt-SQL-Import durch.
    Optional mit Kalenderwoche (`kw`) als int.
    """
    fname = get_function_name()

    if not os.path.exists(HCWR_GLOBALS.SQL_TEMPLATE):
        warning(f"Das in {HCWR_GLOBALS.CFG_FILE} definierte SQL-Template für heco: {HCWR_GLOBALS.SQL_TEMPLATE} existiert nicht!", "")
        prompt  = (f"Möchten sie das Default SQL-Template für heco verwenden und nach {HCWR_GLOBALS.SQL_TEMPLATE} kopieren? [J/n]: ")
        answer = input_with_prefill(prompt, "", "")
        print("\n")
        if answer in ("", "j", "ja", "y", "yes"):
            checkNfetch_file_from_NIS(HCWR_GLOBALS.DEFULT_SQL_TEMPLATE, HCWR_GLOBALS.SQL_TEMPLATE)
        else:
            warning(f"Da das in {HCWR_GLOBALS.CFG_FILE} definierte SQL-Template für heco existiert nicht!\nBitte dort hinterlegen!\n\n","Abbruch!")
            show_process_route()
            sys.exit(1)

    if not os.path.exists(HCWR_GLOBALS.WF_CHECK_PATH):
        warning(f"Das in {HCWR_GLOBALS.CFG_FILE} definierte wochenfazit.py: {HCWR_GLOBALS.WF_CHECK_PATH} existiert nicht!", "")
        prompt  = (f"Möchten sie das Default wochenfazit.py nach {HCWR_GLOBALS.WF_CHECK_PATH} kopieren? [J/n]: ")
        answer = input_with_prefill(prompt, "", "")
        print("\n")
        if answer in ("", "j", "ja", "y", "yes"):
            checkNfetch_file_from_NIS(HCWR_GLOBALS.DEFAULT_WF_CHECK_PATH, HCWR_GLOBALS.WF_CHECK_PATH)
        else:
            warning(f"Da das in {HCWR_GLOBALS.CFG_FILE} definierte wochenfazit.py für heco existiert nicht!\nBitte dort hinterlegen!\n\n","Abbruch!")
            show_process_route()
            sys.exit(1)
#TODO: Postgress Support weiter ein-/ausbauen
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        info("Derzeit wird nur SQLite unterstutzt für die Initalisierung von heco.")
        show_process_route()
        sys.exit(1)
    else:

        if kw is not None:
            # Pfad für eine bestimmte KW
            db_dir = os.path.expanduser(f"~/.heco/2025/kw{int(kw)}")
            db_path = os.path.join(db_dir, "time.db")
        else:
            # Standard-Pfad
            db_dir = os.path.expanduser("~/.heco")
            db_path = os.path.join(db_dir, "time.db")

        if os.path.exists(db_path):
            info(f"Es exsistiert bereits eine {db_path}", "Es wird da hier abgebrochen!")
            show_process_route()
            sys.exit(1)
            return

        os.makedirs(db_dir, exist_ok=True)

        # heco initialisieren
        subprocess.run(["heco", "--init-only", db_path], check=True)

        # SQL-Datei importieren

        if int(HCWR_GLOBALS.DBG_LEVEL)<0:
            debug(f"sql_template = {HCWR_GLOBALS.SQL_TEMPLATE}")
        subprocess.run(
            f"echo '.read {HCWR_GLOBALS.SQL_TEMPLATE}' | sqlite3 {db_path}",
            shell=True,
            check=True
        )

    # Interaktive Konfiguration starten
    configure_interactive()

    if not auto_migration():
        show_process_route()
        sys.exit(1)

def is_current_week_and_complete(db_path, year, kw):
    """
    Prüf Funktion, die überprüft, ob die definierten Arbeitstage auch schon Arbeitszeiteneinträge haben.
    Und setzt den Trigger ob es eine Tagesabweichung gibt, von der eingetsellten normal Arbeitsstunden.
    """
    fname = get_function_name()

    # Aktuelle Woche und Jahr ermitteln
    today = datetime.today()
    current_year, current_kw, _ = today.isocalendar()

    is_current = (year == current_year and kw == current_kw)

    # Wochenbeginn (Montag) und Ende (Sonntag) berechnen
    def get_week_bounds(year, kw):
        fname = get_function_name()
        # ISO-Woche: Montag als erster Tag
        monday = datetime.strptime(f'{year}-W{kw:02}-1', "%G-W%V-%u")
        return monday

    HCWR_GLOBALS.MONDAY = get_week_bounds(year, kw)

    # Verbindung zur SQLite-Datenbank herstellen
    conn = HCWR_GLOBALS.DBMS.connect(db_path)
    cursor = conn.cursor()

    # Wochentage Mo–So
    weekdays = HCWR_GLOBALS.WEEKDAYS
    missing_days = []
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"weekdays = {weekdays}")

    #TODO DONE: Auch Sa. & So. fähig machen
    for day_index in range(len(weekdays)):  # Mo.–So.
        day = HCWR_GLOBALS.MONDAY + timedelta(days=day_index)
        day_str = day.strftime('%Y-%m-%d')
        next_day_str = (day + timedelta(days=1)).strftime('%Y-%m-%d')

        cursor.execute(
            HCWR_GLOBALS.DB_QUERIES.week_complete,
            (day_str, next_day_str)
        )
        count = cursor.fetchone()[0]
        hours = HCWR_GLOBALS.WDAYHOURS_MAP.get(weekdays[day_index], 0)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info (f"HCWR_GLOBALS.DB_QUERIES.week_complete = {debug_sql(HCWR_GLOBALS.DB_QUERIES.week_complete,  [day_str, next_day_str])}")
            info(f"count = {count}, hours = {hours}")
        if float(hours) == 0:
            count = 1
        if count == 0:
            missing_days.append(weekdays[day_index])

    conn.close()

    all_days_complete = (len(missing_days) == 0)
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nis_current = {is_current}, all_days_complete = {all_days_complete}, missing_days = {missing_days}")
        show_process_route()
        sys.exit(0)

    return is_current, all_days_complete, missing_days

# Prüft welche "Kürzel" verwentet werden, entsprechend der Vorlage aus:
# /home/projects/Intern/hecokwreport.hg/template:
#   heco.projects.sql
#   heco.projects-v2.sql
#   heco.projects-ms.sql
def get_db_key_structure():
    fname = get_function_name()

    conn = HCWR_GLOBALS.DBMS.connect(HCWR_GLOBALS.args.database)
    cursor = conn.cursor()

    cursor.execute(HCWR_GLOBALS.DB_QUERIES.check_db_key_structure)
    rows = cursor.fetchall()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nget_db_key_structure: rows = {rows}, count rows = {len(rows)}")
        sys.exit(0)

    if rows:
        debug(f"get_db_key_structure: rows = {rows}, count rows = {len(rows)}")
        return len(rows) # > 0 = heco.projects.sql, sonst heco.projects-v2.sql oder heco.projects-ms.sql
    return 0

# Automigrate Funktion im alte Daten und Config zu migrieren:
def auto_migration():
    """
    Führt eine automatische Migration der Konfiguration und Datenbanken durch:

    1. Kopiert die alte Konfigurationsdatei '~/.config/hkwreport.conf' nach
       '~/.heco/hcwr.conf', wenn letztere noch nicht existiert.
       Gibt eine Info-Meldung aus, lässt die alte Datei aber bestehen.

    2. Aktualisiert in der neuen Konfiguration im Abschnitt [ProjectIDs] die Schlüssel:
       - 'Sachbearbeitung abrechenbar' → 'Sacharbeit abrechenbar'
       - 'Sachbearbeitung andere*'    → 'Sacharbeit andere*'

    3. Öffnet die SQLite-Datenbank '~/.heco/time.db' und ersetzt in der Tabelle 'projects':
       - ID 322: description → 'Sacharbeit abrechenbar'
       - ID 323: description → 'Sacharbeit andere*'

    4. Öffnet die SQLite-Datenbank '~/.heco/keyword_id.db' und benennt in der Tabelle 'contracts'
       die Spalte 'category' um in 'task', sofern 'category' existiert und 'task' noch nicht existiert.

    Hinweise:
    - Diese Funktion kann gefahrlos mehrfach aufgerufen werden.
    - Bei Fehlern in den Datenbankoperationen werden Ausnahmen abgefangen und ausgegeben.
    """
    fname = get_function_name()

    if HCWR_GLOBALS.args.verbose or HCWR_GLOBALS.args.dry_run:
        info(f"Running Automigration ...")

    success = False
    db_key_structure = get_db_key_structure()

    # Schritt 1: Alte Config kopieren
    if int(HCWR_GLOBALS.DBG_LEVEL)==1:
        debug(f"auto_migration: success = {success}")
        debug(f"auto_migration: Checking for {HCWR_GLOBALS.OLD_CFG_PATH}")
    if os.path.exists(HCWR_GLOBALS.OLD_CFG_PATH) and not os.path.exists(HCWR_GLOBALS.CFG_FILE):
        shutil.copy(HCWR_GLOBALS.OLD_CFG_PATH, HCWR_GLOBALS.CFG_FILE)
        info(f"Alte Config migriert nach {HCWR_GLOBALS.CFG_FILE}. Alte Config nicht entfernt!")
        success = True
    elif os.path.exists(HCWR_GLOBALS.CFG_FILE):
        success = True

    if int(HCWR_GLOBALS.DBG_LEVEL)==-1 and success:
        debug(f"auto_migration: success = {success}")
        info(f"{HCWR_GLOBALS.OLD_CFG_PATH} exsists, ", "migrated to default config file: {HCWR_GLOBALS.CFG_FILE}")
    elif int(HCWR_GLOBALS.DBG_LEVEL)==-1 and not success:
        info(f"{HCWR_GLOBALS.OLD_CFG_PATH} does not exsists, ", f"using default config file: {HCWR_GLOBALS.CFG_FILE}")

    # Schritt 2: Einträge in [ProjectIDs] aktualisieren (Description zu Project ID 322 und 323 anpassen)
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug(f"auto_migration: success = {success}")
        debug(f"auto_migration: Checking for entries if [ProjectIDs] in default {HCWR_GLOBALS.CFG_FILE}")
    if os.path.exists(HCWR_GLOBALS.CFG_FILE):
        HCWR_GLOBALS.CFG.read(HCWR_GLOBALS.CFG_FILE)

        if HCWR_GLOBALS.CFG.has_section("ProjectIDs"):
            if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
                debug(f"auto_migration: Checking ProjectIDs in {HCWR_GLOBALS.CFG_FILE}")
            changes_made = False
            mapping = {
                "Sachbearbeitung abrechenbar": "Sacharbeit abrechenbar",
                "Sachbearbeitung andere*": "Sacharbeit andere*"
            }

            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"mapping = {mapping}")
                info(f"changes_made = {changes_made}")

            for old_key, new_key in mapping.items():
                if HCWR_GLOBALS.CFG.has_option("ProjectIDs", old_key):
                    value = HCWR_GLOBALS.CFG.get("ProjectIDs", old_key)                    
                    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                        info(f"value old_key = {value}")
                        info(f"old_key = {old_key}")
                        info(f"new_key = {new_key}")
                    HCWR_GLOBALS.CFG.remove_option("ProjectIDs", old_key)
                    HCWR_GLOBALS.CFG.set("ProjectIDs", new_key, value)
                    changes_made = True

            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"changes_made = {changes_made}")

            if changes_made:
                success = False
                update_config(HCWR_GLOBALS.CFG)
                info("Config-Einträge in [ProjectIDs] erfolgreich aktualisiert.")
                get_config("auto_migration")
                success = True

    # Schritt 3: heco DB aktualisieren (Description zu Project ID 322 und 323 anpassen)
    dbpath = HCWR_GLOBALS.args.database
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug(f"auto_migration: success = {success}")
        debug(f"auto_migration: Checking 'description for project id 322 and 323' heco database {dbpath}")
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        HCWR_GLOBALS.DBMS = importlib.import_module('psycopg')
        HCWR_GLOBALS.DB_QUERIES = importlib.import_module('hcwr_pg_queries_sql')
    if os.path.exists(dbpath):
        try:
            success = False
            conn = HCWR_GLOBALS.DBMS.connect(dbpath)
            cursor = conn.cursor()
            resA = get_project_id(cursor, "├─ Sachbearbeitung abrechenbar")
            resB = get_project_id(cursor, "└─ Sachbearbeitung andere*")
            cursor = conn.cursor()
            debug(f"db_key_structure = {db_key_structure}")
            debug(f"len(HCWR_GLOBALS.PROJECTS_ID_MAP) = {len(HCWR_GLOBALS.PROJECTS_ID_MAP)}")
            #if db_key_structure != len(HCWR_GLOBALS.PROJECTS_ID_MAP) - 5 : 
            if db_key_structure != len(HCWR_GLOBALS.PROJECTS_ID_MAP): 
                # TODO: Bessere Zuordnung welches DB-Schema genutzt wird bauen ( Quick-FIX: -5 = - Anzahl der Oberkategorien )
                if resA != None and int(resA) == 322:
                    sql_update = "UPDATE projects SET description = '  Sacharbeit abrechenbar' WHERE id = 322;"
                    info(f"sql_update = {sql_update}")
                    cursor.execute(sql_update)
                    conn.commit()
                if resB != None and int(resB) == 323:
                    sql_update = "UPDATE projects SET description = '  Sacharbeit andere*' WHERE id = 323;"
                    info(f"sql_update = {sql_update}")
                    cursor.execute(sql_update)
                    conn.commit()
            elif (resA and resB and db_key_structure == len(HCWR_GLOBALS.PROJECTS_ID_MAP) - 5 and int(resA) == 322 and int(resB) == 323):
                # TODO: Bessere Zuordnung welches DB-Schema genutzt wird bauen ( Quick-FIX: -5 = - Anzahl der Oberkategorien )
                if resA != None and int(resA) == 322:
                    sql_update = "UPDATE projects SET description = '├─ Sacharbeit abrechenbar' WHERE id = 322;"
                    info(f"sql_update = {sql_update}")
                    cursor.execute(sql_update)
                    conn.commit()
                if resB != None and int(resB) == 323:
                    sql_update = "UPDATE projects SET description = '└─ Sacharbeit andere*' WHERE id = 323;"
                    info(f"sql_update = {sql_update}")
                    cursor.execute(sql_update)
                    conn.commit()
                info("Projektbeschreibungen in time.db erfolgreich aktualisiert.")
            else:
                if HCWR_GLOBALS.args.verbose:
                    info("Projektbeschreibungen in time.db sind aktuell.")
            success = True
        except Exception as e:
            success = False
            warning(f"heco DB aktualisieren: Fehler beim Aktualisieren der {dbpath}:", e)
            show_process_route()
            sys.exit(1)
        finally:
            success = True
            conn.close()

    # Schritt 4: Spalte "category" in Datenbank: HCWR_GLOBALS.DB_KEYWORD_ID_PATH umbenennen in "task"
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug(f"auto_migration: success = {success}")
        debug(f"auto_migration: Checking for col 'category' key word id database {HCWR_GLOBALS.DB_KEYWORD_ID_PATH} nad rename it to 'task', is exists")
    if os.path.exists(HCWR_GLOBALS.DB_KEYWORD_ID_PATH):
        try:
            success = False
            DBMS = importlib.import_module('sqlite3')
            DB_QUERIES = importlib.import_module('hcwr_sqlite_queries_sql')
            conn = DBMS.connect(HCWR_GLOBALS.DB_KEYWORD_ID_PATH)
            cursor = conn.cursor()
            # Prüfen ob Spalte 'category' existiert
            cursor.execute("PRAGMA table_info(contracts);")
            columns = [row[1] for row in cursor.fetchall()]
            if "category" in columns and "task" not in columns:
                cursor.execute("ALTER TABLE contracts RENAME COLUMN category TO task;")
                conn.commit()
                info("Spalte 'category' wurde zu 'task' umbenannt in keyword_id.db.")
        except Exception as e:
            success = False
            warning(f"Spalte 'category' in Datenbank: Fehler beim Anpassen der {HCWR_GLOBALS.DB_KEYWORD_ID_PATH}:", e)
            show_process_route()
            sys.exit(1)
        finally:
            success = True
            conn.close()
    if int(HCWR_GLOBALS.DBG_LEVEL)==-1:
        debug(f"auto_migration: success = {success}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

    return success

# Prepare SQL query
def merge_results(result):
    """
    Fügt die Daten entsprechend des geforderten Formats von Wochenfazit zusammen zur weiteren Verabeitung.
    """
    fname = get_function_name()

    merged = {}

    # Phase 1: Sammeln und aufsummieren
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        info(f"===============================================")
    for entry in result:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"entry = {entry}")
            info(f"------------#############################################--------------")
        desc = entry['description']
        dur = entry['duration'] or 0
        uuk = entry['uuk']
        uuk_dur = 0
        if uuk == None:
            uuk = []
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"uuk = {uuk}")
            info(f"--------------------------")
        for u in uuk:
            if isinstance(u, dict) and u.get('duration') is not None:
                uuk_dur += u['duration']

        if desc not in merged:
            if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
                merged[desc] = {'duration': 0, 'uuk': []}
            else:
                merged[desc] = {'duration': 0, 'uuk': None}

            if 'task' in entry:
                merged[desc]['task'] = entry['task']
            if 'contract_id' in entry:
                merged[desc]['contract_id'] = entry['contract_id']
        merged[desc]['duration'] += int(dur)

        if uuk:
            merged[desc]['uuk'] = uuk

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"merged = {merged}")
    # Phase 2: Neuaufbau der Ergebnisliste
    final_result = []
    for description in merged:
        i = {
            'description': description,
            'duration': merged[description]['duration'],
            'uuk': merged[description]['uuk'],
        }
        if 'task' in merged[description]:
            i['task'] = merged[description]['task']
        if 'contract_id' in merged[description]:
            i['contract_id'] = merged[description]['contract_id']
        final_result.append(i)
        if int(HCWR_GLOBALS.DBG_LEVEL) == -1:
            debug(f"final_result = {final_result}")
            debug(f"****************************************************")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nfinal_result = {final_result}")
        show_process_route()
        sys.exit(0)

    return final_result

def get_project_id(cursor, category):
    """
    Holt sich die ID zu einer "category" aus der heco time.db
    """
    fname = get_function_name()

    category = f"%{category}%"
    cursor.execute(HCWR_GLOBALS.DB_QUERIES.pid_by_description, (category,))  # <-- Tupel mit Komma
    result = cursor.fetchone()
    if int(HCWR_GLOBALS.DBG_LEVEL) == 6:
        debug(f"result = {result}")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        show_process_route()
        sys.exit(0)

    return  result[0] if result else None

def get_UK_and_UUK(conn, base_sql, category, params):
    """
    Bereitet die Daten soweit auf und sortiert sie so, dass sie in dem geforderten Format für das Wochenfazit verarbeitbar sind.
    """
    fname = get_function_name()

    pid = HCWR_GLOBALS.PROJECTS_ID_MAP[category.strip()]
    pnew = []
    for p in params:
        pnew.append(p)
    pnew.append(str(pid))
        
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\npid = {pid}, pnew = {pnew}")
    sql_query = HCWR_GLOBALS.DB_QUERIES.tppbw_uuk
    #sql_query = base_sql.replace(
    #        "SELECT",
    #        "SELECT e.start_time AS entry_start_time, e.id AS entry_id, e.description AS entry,"
    #        )

    #sql_query = sql_query.replace(
    #        "GROUP BY p.id, p.key, p.description",
    #        f"WHERE p.id = {str(pid)} GROUP BY p.id, p.key, p.description, e.description"
    #        )
    cursor = conn.cursor()
    cursor.execute(sql_query, pnew)
    result_rows = cursor.fetchall()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"sql_query = {debug_sql(sql_query, pnew)}\nresult_rows for [{category.strip()}] = {result_rows}")
    uk_entry = []
    for entry_start_time, entry_id, entry, uuk, duration in result_rows:
        if int(HCWR_GLOBALS.DBG_LEVEL)==-10:
            info(f"uuk = {uuk}\ncategory = {category}")
        if uuk == category:
            if int(HCWR_GLOBALS.DBG_LEVEL) == 4:
                debug(f"entry = {entry}, uuk = {uuk}, duration = {duration}")
            line = f"  {entry}:"
            m = HCWR_GLOBALS.CONTRACT_PATTERN.match(line)
            contract = get_contract_id(entry)
            if int(HCWR_GLOBALS.DBG_LEVEL)==-10:
                info(f"line = {line}\nentry = {entry}\ncontract = {contract}")
            if int(HCWR_GLOBALS.DBG_LEVEL) == -2 and contract != None and contract.get('contract_id') not in entry and not m and entry != None:
                debug(f"contract_id = {contract}\nentry = {entry}")
            if contract != None and contract.get('contract_id') not in entry and not m and entry != None:
                entry = f"{entry} {contract.get('contract_id')}"
            if int(HCWR_GLOBALS.DBG_LEVEL) == -2:
                debug(f"contract_id = {contract}\nAFTER CHECK entry = {entry}")
            line = f"  {entry}:"
            m = HCWR_GLOBALS.CONTRACT_PATTERN.match(line)
            if int(HCWR_GLOBALS.DBG_LEVEL) == -98:
                debug(f"get_UK_and_UUK [contract] -> contract: {contract}")
            if not m and entry != None:
                #info(f"contract = {contract}, line = {line}")
                keyword_place = HCWR_GLOBALS.CFG.get("Database", "keyword_place")
                if HCWR_GLOBALS.PROC_NAME in "hcoh":
                    answer = "n"
                else:
                    warning(f"  {entry}",f" <- Missing contract No# in entry by pattern setting [keyword_place = {keyword_place}]")
                    prompt  = (f"Möchten sie den Eintrag hier nun korrigieren? {entry}? [J/n]: ")
                    answer = input_with_prefill(prompt, "", "")
                if answer in ("", "j", "ja", "y", "yes"):
                    entry_new = input_with_prefill("Bearbeiten von : ", entry)
                    info("Changed entry : ", entry_new)
                    if entry != entry_new:
                        prompt = (f"Möchten Sie den/die Einträge auch in der heco time.db für " +
                                            Fore.YELLOW + Style.BRIGHT +
                                            f"{HCWR_GLOBALS.args.year} KW {HCWR_GLOBALS.args.week}" + Style.RESET_ALL +
                                            f" nun korrigieren? {entry}? [j/N]: ")

                        answer = input_with_prefill(prompt, "", "")
                        if answer in ("j", "ja", "y", "yes"):
                            sql_params = [entry_new, entry, HCWR_GLOBALS.MONDAY.strftime("%Y-%m-%d"), HCWR_GLOBALS.SUNDAY.strftime("%Y-%m-%d")]
                            cursor.execute(HCWR_GLOBALS.DB_QUERIES.update_entry, sql_params)
                            conn.commit()
                        else:
                            print()
                            info("Keine Änderung vorgenommen für " +
                                 Fore.YELLOW + Style.BRIGHT +
                                 f"{HCWR_GLOBALS.args.year} KW {HCWR_GLOBALS.args.week} von Entry " +
                                 Fore.BLUE
                                 + f"{entry}" + Style.RESET_ALL + " in : ",
                                 "heco time.db")
                        entry = entry_new
            added = False
            for e in uk_entry:
              if (
                      contract is not None and
                      e.get('contract_id') is not None and
                      contract.get('contract_id') in e.get('contract_id')
              ):

                    e['duration'] += duration
                    e['description'] = f"{contract.get('keyword')} {contract.get('task')} {contract.get('contract_id')}" if contract is not None else e['description']
                    added = True
                    if int(HCWR_GLOBALS.DBG_LEVEL) == -98:
                        debug(f"get_UK_and_UUK [TOTALED BY CONTRACT] -> uk_entry : {uk_entry}")
                    break
            if not added:
                if int(HCWR_GLOBALS.DBG_LEVEL) == -98:
                    debug(f"get_UK_and_UUK [ADDED] -> entry : {entry}, uuk: {uuk.strip()}, duration: {duration}, contract: {contract}")

                if contract is not None:
                    entry = f"{contract.get('keyword')} {contract.get('task')} {contract.get('contract_id')}"
                if int(HCWR_GLOBALS.DBG_LEVEL) == -98:
                    debug(f"get_UK_and_UUK [DESC CHANGED TO CONTRACT DESC] -> entry : {entry}, uuk: {uuk.strip()}, duration: {duration}, contract: {contract}")

                uk_entry.append({
                    "entry": entry,
                    "uuk": uuk.strip(),
                    "duration": duration,
                    "contract_id": contract.get('contract_id') if contract is not None else None,
                    "task": contract.get('task') if contract is not None else None
                })

    if int(HCWR_GLOBALS.DBG_LEVEL) == -98:
        debug(f"get_UK_and_UUK: uk_entry = {uk_entry}")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nuk_entry = {uk_entry}")
        show_process_route()
        sys.exit(0)

    if uk_entry:
        return uk_entry

def initialize_contracts_db():
    """Initialisiert die contracts-Datenbank mit Beispieldaten, falls nicht vorhanden."""
    fname = get_function_name()

    os.makedirs(os.path.dirname(HCWR_GLOBALS.DB_KEYWORD_ID_PATH), exist_ok=True)

    
    DBMS = importlib.import_module('sqlite3')
    DB_QUERIES = importlib.import_module('hcwr_sqlite_queries_sql')
    conn = DBMS.connect(HCWR_GLOBALS.DB_KEYWORD_ID_PATH)
    cursor = conn.cursor()

    # Tabelle erstellen (mit AUTOINCREMENT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            contract_id TEXT NOT NULL,
            task TEXT
        );
    """)

    # Beispielhafte Einträge
    contracts = [
        ('pflege', '#4012', 'Dauertätigkeit'),
        ('verbesserung', '#4012', 'Dauertätigkeit'),
        ('features', '#4013', 'Dauertätigkeit'),
        ('betrieb', '#4014', 'Dauertätigkeit'),
        ('openslides-allgemein', '#3969', 'Dauertätigkeit'),
        ('relationale datenbank', '#4015', 'Projekt'),
        ('keycloak', '#4016', 'Projekt'),
        ('crypto-vote', '#4017', 'Projekt'),
        ('projektor-service', '#4019', 'Projekt'),
    ]

    for keyword, contract_id, task in contracts:
        cursor.execute(DB_QUERIES.contract_insert, (keyword, contract_id, task, keyword, contract_id))

    conn.commit()
    conn.close()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\ncontracts = {contracts}")
        show_process_route()
        sys.exit(0)

def get_contract_id(entry, db_path=None):
    """
    Ermittelt contract_id basierend auf Keywords.

    Rückgabe:
        contract_id (str) oder None

    Regeln:
      * keyword_place = "*" oder "any" oder None:
           -> normale Suche
           -> bei mehreren Treffern wird der User gefragt und die ausgewählte contract_id zurückgegeben
      * keyword_place = ^, 1, beginning, first:
           -> Keyword muss am Anfang stehen -> erster gültiger Treffer liefert contract_id
      * keyword_place = $, end, last:
           -> Keyword muss am Ende stehen -> erster gültiger Treffer liefert contract_id
      * keyword_place = eigener REGEX:
           -> Regex wird gegen den Entry geprüft -> erster gültiger Treffer liefert contract_id
    """
    fname = get_function_name()
    if not entry:
        return None

    if db_path is None:
        db_path = HCWR_GLOBALS.DB_KEYWORD_ID_PATH

    # Falls SQLite DB fehlt → erstellen
    if (not HCWR_GLOBALS.CFG.has_option("Database", "dbms") or
        HCWR_GLOBALS.CFG.get("Database", "dbms") == "sqlite") and not os.path.exists(db_path):
        initialize_contracts_db()

    conn = HCWR_GLOBALS.DBMS.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(HCWR_GLOBALS.DB_QUERIES.contract_select)
        rows = cursor.fetchall()
    finally:
        conn.close()

    entry_lower = entry.lower()

    # keyword_place laden (original string, nicht zwangsläufig lower)
    keyword_place = None
    if HCWR_GLOBALS.CFG.has_option("Database", "keyword_place"):
        keyword_place = HCWR_GLOBALS.CFG.get("Database", "keyword_place")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nkeyword_place  = {keyword_place }")
        info(f"entry_lower = {entry_lower}")
        info(f"rows = {rows}")

    if int(HCWR_GLOBALS.DBG_LEVEL) == 1:
        debug(f"keyword_place = {keyword_place}")

    # Positionstest je nach keyword_place
    def pos_match(keyword):
        fn = get_function_name()
        kw = keyword.lower()

        # A: überall erlaubt → "*" oder None → User-Auswahl möglich
        if not keyword_place or keyword_place.lower() in ("*", "any"):
            debug(f"pos_match -> # A")
            debug(f"KEYWORD_PLACE = {keyword_place}")
            return True

        # B: Anfang
        if keyword_place in ("^", "1", "beginning", "first"):
            debug(f"pos_match -> # B")
            debug(f"KEYWORD_PLACE = {keyword_place}")
            return entry_lower.startswith(kw)

        # C: Ende
        if keyword_place in ("$", "end", "last"):
            debug(f"pos_match -> # C")
            debug(f"KEYWORD_PLACE = {keyword_place}")
            return entry_lower.endswith(kw)

        # D: eigener Regex (keyword_place ist das Regex). Prüfe Match gegen entry.
        try:
            debug(f"pos_match -> # D")
            debug(f"KEYWORD_PLACE = {keyword_place}")
            return re.search(keyword_place, entry) is not None
        except re.error:
            warning(f"Ungültiges Regex in keyword_place: {keyword_place}")
            # Fallback: erlauben
            return True

    # Sammle Treffer (nur contract_id + keyword + task)
    found = []
    for keyword, contract_id, task in rows:
        # Wortgrenzen-Match, case-insensitive
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        r = re.search(pattern, entry_lower)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"pattern = {pattern}")
            info(f"r = {r}")
            info(f"r = {r}")
            if r:
                info(f"r.span = {r.span()}")
                info(f"r.start = {r.start()}")
                info(f"r.end = {r.end()}")

        if not r:
            continue

        p = pos_match(keyword)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"p = {p}")

        if not p:
            # Keyword gefunden, aber nicht an geforderter Position
            info(f"Keyword [ " + 
            Fore.GREEN + 
            keyword + 
            Fore.WHITE + 
            " ] gefunden, aber nicht an definierter Stelle ( " + 
            Fore.YELLOW + keyword_place + Fore.WHITE +
            " ) laut config.")
            continue

        found.append({'contract_id': contract_id, 'keyword': keyword, 'task': task})

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"found = {found}")

    # FALL A: "*" / "any" / None  -> mehrere Treffer → Benutzer auswählen
    if not keyword_place or keyword_place.lower() in ("*", "any"):
        debug(f"FALL A found = {found}")
    
        # WICHTIG: kein Regex bei None/"any" verwenden!
        if len(found) == 0:
            return None
    
        if len(found) == 1:
            return found[0]
    
        # mehrere -> Benutzer wählen lassen
        warning(f"  {entry}", " <- Mehrdeutiger Eintrag – mehrere Keywords gefunden")
        print("Folgende Keywords wurden gefunden:")
        for idx, f in enumerate(found, 1):
            print(f"[{idx}] contract_id: {f['contract_id']} | keyword: '{f['keyword']}' | task: {f['task']}")
    
        prompt = f"Welche ID soll verwendet werden für '{entry}'? [1-{len(found)}]: "
        while True:
            try:
                answer = input_with_prefill(prompt, "", "")
                selected = int(answer)
                if 1 <= selected <= len(found):
                    return found[selected - 1]
            except (ValueError, TypeError):
                pass
            print(f"Ungültige Eingabe. Bitte Zahl zwischen 1 und {len(found)} eingeben.")

    # FALL B/C/D: ^, $, eigener REGEX -> erster gültiger Treffer, keine Nachfrage
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"found = {found}")
        show_process_route()
        sys.exit(0)

    if found:
        debug(f"found = {found}")
        m = re.search(keyword_place, entry)
        debug(f"m = {m}")
        return found[0]

    return None

def show_contract_keywords():
    """Zeigt alle gespeicherten Contract-Keywords tabellarisch an."""
    fname = get_function_name()
    if not os.path.exists(HCWR_GLOBALS.DB_KEYWORD_ID_PATH):
        info("Noch keine Contract-Keyword-Datenbank vorhanden.","Initialisiere DB")
        initialize_contracts_db()

    conn = HCWR_GLOBALS.DBMS.connect(HCWR_GLOBALS.DB_KEYWORD_ID_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT contract_id, keyword, task FROM contracts ORDER BY contract_id, keyword")
    rows = cursor.fetchall()

    if not rows:
        info("Keine Contract-Keywords gefunden.")
    else:
        # Spaltenüberschrift
        print(f"{'Contract ID':<12} | {'Keyword':<30} | {'Kategorie':<20}")
        print("-" * 12 + "-+-" + "-" * 30 + "-+-" + "-" * 20)

        for contract_id, keyword, task in rows:
            print(f"{contract_id:<12} | {keyword:<30} | {task or '-':<20}")

    conn.close()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nrows = {rows}")
        show_process_route()
        sys.exit(0)

def delete_contract_keyword():
    fname = get_function_name()
    """Löscht ein einzelnes Keyword aus der Contract-Datenbank."""
    if not os.path.exists(HCWR_GLOBALS.DB_KEYWORD_ID_PATH):
        info("Noch keine Contract-Keyword-Datenbank vorhanden.","Initialisiere DB")
        initialize_contracts_db()
    
    show_contract_keywords()

    keyword = input("Welches Keyword soll gelöscht werden? ").strip()

    if not keyword:
        warning("Kein Keyword eingegeben.")
        return

    conn = HCWR_GLOBALS.DBMS.connect(HCWR_GLOBALS.DB_KEYWORD_ID_PATH)
    cursor = conn.cursor()

    # Prüfen ob das Keyword existiert
    cursor.execute(HCWR_GLOBALS.DB_QUERIES.contract_by_keyword, (keyword,))
    results = cursor.fetchall()

    if not results:
        info(f"Keyword '{keyword}'"," nicht gefunden.")
    else:
        warning("Folgender Eintrag wird gelöscht:","")
        for contract_id, task in results:
            print(f"- Contract ID: {contract_id}, Kategorie: {task or '-'}")

        confirm = input(f"Möchtest du das Keyword '{keyword}' wirklich löschen? [j/N] ").strip().lower()
        if confirm == "j":
            cursor.execute(HCWR_GLOBALS.DB_QUERIES.contract_delete, (keyword,))
            conn.commit()
            info(f"Keyword '{keyword}'"," wurde gelöscht.")
        else:
            info("Löschen abgebrochen.","")

    conn.close()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        show_process_route()
        sys.exit(0)

def set_contract_keywords(keywords):
    """Setzt ein oder mehrere Keywords in der Contract-Datenbank."""

    fname = get_function_name()

    os.makedirs(os.path.dirname(HCWR_GLOBALS.DB_KEYWORD_ID_PATH), exist_ok=True)

    if not os.path.exists(HCWR_GLOBALS.DB_KEYWORD_ID_PATH):
        initialize_contracts_db()

    # DB und Tabelle sicherstellen
    conn = HCWR_GLOBALS.DBMS.connect(HCWR_GLOBALS.DB_KEYWORD_ID_PATH)
    cursor = conn.cursor()
    cursor.execute(HCWR_GLOBALS.DB_QUERIES.create_contracts_tbl)
    conn.commit()

    # Nach contract_id fragen
    contract_id = input_with_prefill("Contract ID (z. B. #4012): ", "")
    if not contract_id.strip():
        print("Abgebrochen: Contract-ID darf nicht leer sein.")
        return

    # Nach Kategorie fragen
    task = input_with_prefill("Kategorie (z. B. Dauertätigkeit, Projekt): ", "")

    # Falls per Argument mitgegeben, verwenden
    if keywords:
        input_keywords = keywords
    else:
        # Manuelle Eingabe, mehrere durch Komma trennbar
        keyword_input = input_with_prefill("Keywords (durch Komma getrennt): ", "")
        input_keywords = [kw.strip() for kw in keyword_input.split(',') if kw.strip()]

    # In DB eintragen
    inserted = 0
    for kword in input_keywords:
        cursor.execute(HCWR_GLOBALS.DB_QUERIES.contract_exists, (kword, contract_id))
        if cursor.fetchone():
            warning(f"Übersprungen: Keyword '{kword}' mit ID '{contract_id}' existiert bereits.", "Info")
            continue

        cursor.execute(HCWR_GLOBALS.DB_QUERIES.contract_insert, (kword, contract_id, task, kword, contract_id))
        inserted += 1

    conn.commit()
    conn.close()
    info(f"{inserted} Keyword(s)"," gespeichert.")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)
    
def berechne_abwesenheiten(conn, year, week):
    """
    Berechnen Sie die Abwesenheitszeiten pro Kategorie.
    """
    fname = get_function_name()

    cursor = conn.cursor()
    result = {key: 0 for key in HCWR_GLOBALS.MAPPING}
    sql = HCWR_GLOBALS.DB_QUERIES.absence
    if HCWR_GLOBALS.CFG.has_option("Database", "dbms") and HCWR_GLOBALS.CFG.get("Database", "dbms") == "pg":
        params = [week, week]
    else:
        params = [year, week, year, week]

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\sql = {debug_sql(sql, params)}")
        info(f"rows = {rows}")
    for desc, entry_seconds in rows:
        desc = desc.strip()
        for key, keywords in HCWR_GLOBALS.MAPPING.items():
            if any(desc.startswith(word) for word in keywords):
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"result[{key}] += {entry_seconds}")
                #if HCWR_GLOBALS.CFG.has_option('Database', 'dbms') == "pg":
                #    result[key] = Decimal('0.0')
                result[key] += entry_seconds
                break
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"rows = {rows}")
        show_process_route()
        sys.exit(0)
    return result

def get_last_entry(db_connection):
    """
    Liefert den zeitlich letzten Datensatz aus der Tabelle 'entries'.
    Sortiert nach start_time (primär) und id (sekundär als Fallback).

    Rückgabe:
        dict mit allen Feldern des Datensatzes,
        oder None wenn die Tabelle leer ist.
    """
    fname = get_function_name()
    cursor = db_connection.cursor()

    sql = HCWR_GLOBALS.DB_QUERIES.get_last_record_of_eintries_today

    cursor.execute(sql)
    row = cursor.fetchone()

    if not row:
        return None

    # Feldnamen bestimmen
    column_names = [desc[0] for desc in cursor.description]

    # Datensatz als dict zurück
    return dict(zip(column_names, row))
