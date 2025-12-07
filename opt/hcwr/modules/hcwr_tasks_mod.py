# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_tasks_mod.py
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
import sqlite3
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route
from hcwr_json_mod import to_json, output
from hcwr_utils_mod import format_decimal

def format_string_to_block(s: str, max_line_length: int = 80) -> str:
    """
    Formatiert einen Koordinaten-/Listen-String so, dass mehrere Items pro Zeile stehen,
    solange die max_line_length nicht überschritten wird.
    """
    fname = get_function_name()

    s = s.rstrip()

    if "|" not in s:
        return s

    # Präfix und Items trennen
    prefix, items = s.split(":", 1)
    prefix = prefix.strip()
    item_list = [i.strip() for i in items.split("|") if i.strip()]

    result = prefix + ":\n"
    current_line = "      "  # Einrückung

    for item in item_list:
        # Prüfen, ob Item zur aktuellen Zeile passt
        if len(current_line) + len(item) + 2 <= max_line_length:  # +2 für ", "
            if current_line.strip() != "":
                current_line += ", " + item
            else:
                current_line += item
        else:
            # Zeile voll → neue Zeile beginnen
            result += current_line.rstrip(", ") + "\n"
            current_line = "      " + item

    # letzte Zeile hinzufügen
    if current_line.strip() != "":
        result += current_line.rstrip(", ") + "\n"

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        show_process_route()
        sys.exit(0)

    return result.rstrip("\n")

def get_my_tasks():
    search_exclude = HCWR_GLOBALS.SEARCH_EXCLUDE
    tresult = fetch_and_display_entries(search_exclude, True, False)

    fname = get_function_name()

    if int(HCWR_GLOBALS.DBG_LEVEL) > 0:
        info("Funktionsaufruf von :", "get_my_tasks")

    unique_lines = []
    for line in tresult:
        idx, category, start, end, duration, entry = line
        if entry not in unique_lines:
            unique_lines.append(entry)

    lines = "- " + "\n  - ".join(unique_lines)

    new_lines = []

    # ⬇️⬇️⬇️ **GEÄNDERTER BEREICH: statt über Zeichen → über Zeilen iterieren** ⬇️⬇️⬇️
    for line in lines.splitlines():
        if "|" in line and ":" in line:
            new_line = f"  " + format_string_to_block(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    # ⬆️⬆️⬆️ **ENDE geänderter Bereich** ⬆️⬆️⬆️

    lines = "\n".join(new_lines)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nline = {line}")
        show_process_route()
        sys.exit(0)

    return lines

def calculate_time_difference(start_time, end_time):
    fname = get_function_name()
    start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    time_difference = end - start
    return time_difference.total_seconds()

def format_time_difference(seconds):
    fname = get_function_name()
    hours = int(seconds // 3600)
    minutes = int((seconds // 60) % 60)
    formatted_time = f"{hours}:{minutes:02}h"
    if HCWR_GLOBALS.args.format and not HCWR_GLOBALS.args.sum_times:
        if HCWR_GLOBALS.args.format in "%d.2dh":
            formatted_time = format_decimal(float(Decimal(hours) + Decimal(minutes) / 60)) + "h"
    return formatted_time

def format_date(date_string):
    fname = get_function_name()
    date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    formatted_date = date_object.strftime("%d.%m.%Y")
    return formatted_date

def parse_duration(duration):
    """Wandelt '1,30h', '1:30', '1.5h', '2h' oder bereits Sekunden (int/float) um."""

    fname = get_function_name()

    # Falls bereits ein int/float → direkt Sekunden zurückgeben
    if isinstance(duration, (int, float)):
        return int(duration)

    debug(f"duration = {duration}")

    # Typ in string wandeln (z.B. Decimal, andere Formate)
    duration = str(duration).strip()

    # "h" am Ende abschneiden
    if duration.endswith("h"):
        duration = duration[:-1]

    # Komma → Doppelpunkt
    duration = duration.replace(",", ":")

    # Wenn nur Stunden angegeben: "2" → "2:00"
    if ":" not in duration:
        try:
            h = float(duration)
        except ValueError:
            debug(f"parse_duration(): Ungültiges Format: {duration}")
            return 0
        return int(h * 3600)

    # Stunden + Minuten
    try:
        h, m = duration.split(":")
        h = float(h)
        m = float(m)
    except Exception:
        debug(f"parse_duration(): Fehler beim Splitten: {duration}")
        return 0

    result = int(h * 3600 + m * 60)
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        show_process_route()
        sys.exit(0)

    return result

def fetch_and_display_entries(search = None, asListObj = False, stdout = True):
    fname = get_function_name()

    conn = HCWR_GLOBALS.DBMS.connect(HCWR_GLOBALS.args.database)
    cursor = conn.cursor()

    conditions = []
    params = []

    # --- DBMS Platzhalter ---
    if HCWR_GLOBALS.DBMS.__name__ == "sqlite3":
        ph = "?"
    else:  # Postgres
        ph = "%s"

    search_raw = HCWR_GLOBALS.args.search
    if search and HCWR_GLOBALS.args.search is None:
        search_raw = search
    elif search and HCWR_GLOBALS.args.search:
        search_raw = search + "|" + HCWR_GLOBALS.args.search

    if HCWR_GLOBALS.args.cat_time_totals_of:
        if len(search_raw) > 0:
            pipe = "|"
        if "," in HCWR_GLOBALS.args.cat_time_totals_of:
            search_raw = search_raw + pipe + "C=".join(HCWR_GLOBALS.args.cat_time_totals_of.split(","))
        else:
            search_raw = search_raw + pipe + "C=" + HCWR_GLOBALS.args.cat_time_totals_of

    if search_raw:
        search_items = [s.strip() for s in search_raw.split("|")]
    else:
        search_items = []
    
    # --- SEARCH Filter ---
    search_sum = False
    sum_item_like = []
    for item in search_items:
    
        negate = False
        search_cat = False
    
        if item.startswith("!"):
            negate = True
            item = item[1:]
        elif item.startswith("\\!"):
            negate = True
            item = item[2:]
    
        if "S=" in item.upper():
            search_sum = True
            item = item[2:]

        if "C=" in item.upper():
            search_cat = True
            item = item[2:]

        if "*" in item:
            sql_value = item.replace("*", "%")
            operator = "NOT LIKE" if negate else "LIKE"
        else:
            sql_value = item
            operator = "!=" if negate else "="

        if search_sum and not negate:
            sum_item_like.append(sql_value.strip("%"))
            continue
    
        if search_cat:
            conditions.append(f"project {operator} {ph}")
        else:
            conditions.append(f"e.description {operator} {ph}")
        params.append(sql_value)

    # --- DATUM Filter (Woche) ---
    if not HCWR_GLOBALS.args.all_jobs and not HCWR_GLOBALS.args.start_day and not HCWR_GLOBALS.args.stop_day:
        if HCWR_GLOBALS.args.week and HCWR_GLOBALS.args.year:
            conditions.append(f"date(start_time) BETWEEN {ph} AND {ph}")
            params.extend([
                HCWR_GLOBALS.MONDAY.strftime("%Y-%m-%d"),
                HCWR_GLOBALS.SUNDAY.strftime("%Y-%m-%d")
            ])
    elif HCWR_GLOBALS.args.start_day and HCWR_GLOBALS.args.stop_day:
            conditions.append(f"date(start_time) BETWEEN {ph} AND {ph}")
            start_day = datetime.strptime(HCWR_GLOBALS.args.start_day, "%Y-%m-%d").date()
            stop_day  = datetime.strptime(HCWR_GLOBALS.args.stop_day,  "%Y-%m-%d").date()
           
            debug(conditions)
            params.extend([
                start_day.strftime("%Y-%m-%d"),
                stop_day.strftime("%Y-%m-%d")
            ])

    # --- Query ---
    if conditions:
        query = HCWR_GLOBALS.DB_QUERIES.jobtime_entries + "WHERE " + " AND ".join(conditions)
    else:
        query = "SELECT * FROM entries"

    if int(HCWR_GLOBALS.DBG_LEVEL) > 0:
        debug(f"query = {query}")
        debug(f"params = {params}")

    # --- Ausführen ---
    cursor.execute(query, params)
    entries = cursor.fetchall()

    data = []

    for entry in entries:
        entry_id = f"Entry db ID: {entry[0]}"
        entry_cat = f"Category: {entry[1]}"
        start_time = entry[2][:19]
        end_time   = entry[3][:19]
        time_difference = calculate_time_difference(start_time, end_time)
        formatted_time = format_time_difference(time_difference)

        description = entry[4]

        # ------------------------------------------------------------
        # 🔥 PATCH – NEUER Summierungs-Mechanismus für S=
        # ------------------------------------------------------------
        sum_existing = next(
            (s for s in sum_item_like if s in description),
            None
        )

        if sum_existing:

            ### 🔥 NEU: Merge-Block für Beschreibungen
            group_key = sum_existing   # ohne lower()
            debug(f"group_key = {group_key}")

            existing = next((e for e in data if sum_existing in e[5]), None)
            duration_sec = parse_duration(formatted_time)

            if existing:
                # ID anhängen
                existing[0] = f"{existing[0]}|{entry[0]}"

                # Zeiten anhängen
                existing[2] = f"{existing[2]}|{start_time[:16]}"
                existing[3] = f"{existing[3]}|{end_time[:16]}"

                # Dauer addieren
                existing[4] += duration_sec

                # Beschreibung anhängen
                existing[1] = existing[1]     # Kategorie beibehalten
                existing[5] = f"{existing[5]}|{description.strip(sum_existing)}"
                debug(f"existing = {existing}")

            else:
                new_entry = [
                    entry_id,             # ID
                    entry_cat,            # Category
                    start_time[:16],      # Start
                    end_time[:16],        # End
                    duration_sec,         # Duration
                    f"{group_key}: {description.strip(group_key)}"           # Description merged
                ]
                data.append(new_entry)

            continue
        # ------------------------------------------------------------
        # 🔥 ENDE PATCH
        # ------------------------------------------------------------

        # Standard-Eintrag (nicht summiert)
        new_entry = list(entry)
        new_entry.insert(4, formatted_time)
        new_entry[0] = entry_id
        new_entry[1] = entry_cat
        new_entry[2] = entry[2][:16]
        new_entry[3] = entry[3][:16]

        data.append(new_entry)

        if not asListObj and not HCWR_GLOBALS.args.zeiterfassung and not HCWR_GLOBALS.args.json and not HCWR_GLOBALS.args.sum_times:
            output(new_entry)

    conn.close()

    # --- Finale Ausgabe bei --sum-times ---
    if HCWR_GLOBALS.args.sum_times:
        new_data = []
    
        for line in data:
            idx, category, start, end, duration, entry = line
            duration_sec = parse_duration(duration)

            existing = next((x for x in new_data if x[5] == entry), None)

            if existing:
                existing[4] += duration_sec
            else:
                new_data.append([idx, category, start, end, duration_sec, entry])
        total_data = []
        for line in new_data:
            sec = line[4]
            line[4] = format_time_difference(sec)
    
            if HCWR_GLOBALS.args.cat_time_totals_of:
                new_line = [
                    line[1],         # Category
                    line[4],         # Duration
                    line[5],         # Entry Desc
                ]
                total_data.append(new_line)
        if HCWR_GLOBALS.args.cat_time_totals_of:
            new_data = total_data

        if HCWR_GLOBALS.args.json:
            to_json(new_data, stdout)
        else:
            for line in new_data:
                output(line)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            show_process_route()
            sys.exit(0)
        return 

    if HCWR_GLOBALS.args.json:
        to_json(data, stdout)
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            sys.exit(0)
        return 

    if asListObj:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fname}:\ndata = {data}")
            show_process_route()
            sys.exit(0)
        return data

