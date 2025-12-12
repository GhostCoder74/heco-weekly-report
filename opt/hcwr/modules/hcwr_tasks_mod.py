# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_tasks_mod.py
# Authors:        Christian Klose <cklose@intevation.de>
#                 Raimund Renkert <rrenkert@intevation.de>
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)
# Copyright (c) 2024-2026 by Intevation GmbH
# SPDX-License-Identifier: GPL-2.0-or-later
#
# File version:   1.0.1
#
# This file is part of "hcwr - heco Weekly Report"
# Do not remove this header.
# Wochenfazit URL:
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------------------
import re, textwrap
import sys
import sqlite3
import colorama
from colorama import Fore, Style
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route, debug_sql
from hcwr_json_mod import to_json, output
from hcwr_utils_mod import format_decimal, input_with_prefill

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
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\ntresult = {tresult}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()

    unique_lines = []
    for line in tresult:
        idx, category, start, end, duration, entry = line
        if entry not in unique_lines:
            unique_lines.append(entry)

    lines = "- " + "\n  - ".join(unique_lines)

    new_lines = []

    i=0
    s=""
    for line in lines.splitlines():
        if i > 0:
            s = "  "
        if "|" in line and ":" in line:
            new_line = s + format_string_to_block(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    lines = "\n".join(new_lines)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nline = {line}")
        show_process_route()

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
    #if HCWR_GLOBALS.args.format and not HCWR_GLOBALS.args.sum_times:
    #    if HCWR_GLOBALS.args.format in "%d.2dh":
    #        formatted_time = format_decimal(float(Decimal(hours) + Decimal(minutes) / 60)) + "h"
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

def build_sql_from_search(search_raw, ph, PROJECT_EXPR):
    """
    Parse a search expression into a WHERE-clause + params.
    Supports:
      - AND: &    (higher precedence than |)
      - OR:  |
      - NOT: !
      - Parentheses: ( ... ) (with simple auto-fix for unbalanced parens)
      - Category prefix: C=...  -> uses PROJECT_EXPR
      - Wildcards: '*' -> SQL LIKE (value converted to %)
      - Parameterized output using placeholder `ph` (e.g. '?' or '%s')
    Returns:
      (where_sql_string, params_list)

    Examples of valid search_raw:
      "C=Temp&!C=Feiertag&(Support*|Koord*)"
      "!C=Temp|Support*"
      "\!Support|Koord*"   # NOTE: we treat leading backslash same as escaping '!' in user input
    """

    fname = get_function_name()
    # --- Helper: tokenize (preserve tokens like "C=abc/def" etc.) ---
    def tokenize(s):
        # remove surrounding whitespace
        s = s.strip()
        tokens = []
        buf = ""
        i = 0
        while i < len(s):
            c = s[i]
            # treat escaped characters: \!
            if c == "\\" and i + 1 < len(s):
                buf += s[i:i+2]
                i += 2
                continue
            # operators and parens are separate tokens
            if c in ("(", ")","&","|","!"):
                if buf:
                    tokens.append(buf)
                    buf = ""
                tokens.append(c)
                i += 1
                continue
            else:
                buf += c
                i += 1
        if buf:
            tokens.append(buf)
        return tokens

    # --- Helper: fix parentheses (remove extra ')' and append missing ')' ) ---
    def fix_parentheses(tokens):
        fixed = []
        open_count = 0
        for t in tokens:
            if t == "(":
                open_count += 1
                fixed.append(t)
            elif t == ")":
                if open_count > 0:
                    open_count -= 1
                    fixed.append(t)
                else:
                    # extra closing paren -> drop it
                    # simply ignore
                    continue
            else:
                fixed.append(t)
        # append missing closing parens if needed
        fixed.extend([")"] * open_count)
        return fixed

    # --- Shunting-yard to produce postfix (RPN) ---
    def to_postfix(tokens):
        out = []
        ops = []
        prec = {"!": 3, "&": 2, "|": 1}
        # treat '!' as unary and highest precedence
        for t in tokens:
            if t == "(":
                ops.append(t)
            elif t == ")":
                while ops and ops[-1] != "(":
                    out.append(ops.pop())
                if ops and ops[-1] == "(":
                    ops.pop()
            elif t in prec:
                # '!' is unary; ensure correct associativity: treat as right-assoc
                if t == "!":
                    # push '!' onto op stack
                    ops.append(t)
                else:
                    # binary operators: pop while top has >= prec
                    while ops and ops[-1] != "(" and prec.get(ops[-1], 0) >= prec[t]:
                        out.append(ops.pop())
                    ops.append(t)
            else:
                # operand
                out.append(t)
        while ops:
            out.append(ops.pop())
        return out

    # --- Build SQL fragment objects from postfix ---
    # We represent a fragment as tuple (sql_string, params_list)
    def make_operand_fragment(token):
        # handle escaped leading \! (user might have typed "\!foo" — treat as literal "!" in value)
        negate = False
        tok = token

        if tok.startswith("\\!"):
            tok = tok[1:]  # remove leading backslash, keep '!' as part of value (not a not-operator)
        elif tok.startswith("!"):
            # if operand token itself starts with '!', treat as negation applied to operand
            negate = True
            tok = tok[1:]

        # sum like filter?
        if tok.upper().startswith("S="):
            val = tok[2:]
            column = PROJECT_EXPR
        else:
            val = tok
            column = "e.description"

        # category filter?
        if tok.upper().startswith("C="):
            val = tok[2:]
            column = PROJECT_EXPR
        elif tok.upper().startswith("S="): # sum like filter?
            val = tok[2:]
            column = "e.description"
        else:
            val = tok
            column = "e.description"

        # wildcard?
        if "*" in val:
            sql = f"{column} LIKE {ph}"
            param = val.replace("*", "%")
        else:
            sql = f"{column} = {ph}"
            param = val

        if negate:
            sql = f"NOT ({sql})"

        return (sql, [param])

    def combine_fragments(a, b, op):
        a_sql, a_params = a
        b_sql, b_params = b
        if op == "&":
            return (f"({a_sql} AND {b_sql})", a_params + b_params)
        elif op == "|":
            return (f"({a_sql} OR {b_sql})", a_params + b_params)
        else:
            raise ValueError("Unknown binary op")

    # ---------- main flow ----------
    if not search_raw or not str(search_raw).strip():
        return ("", [])

    tokens = tokenize(search_raw)
    tokens = fix_parentheses(tokens)
    postfix = to_postfix(tokens)

    # Evaluate postfix into SQL fragments
    stack = []
    for t in postfix:
        if t == "!":
            if not stack:
                # malformed but try to recover: skip
                continue
            frag = stack.pop()
            frag_sql, frag_params = frag
            stack.append((f"NOT ({frag_sql})", frag_params))
        elif t in ("&", "|"):
            # binary
            if len(stack) < 2:
                # malformed -> ignore
                continue
            b = stack.pop()
            a = stack.pop()
            stack.append(combine_fragments(a, b, t))
        else:
            # operand
            stack.append(make_operand_fragment(t))

    if not stack:
        return ("", [])

    # final fragment
    final_sql, final_params = stack.pop()

    # safety: collapse outermost redundant parentheses
    if final_sql.startswith("(") and final_sql.endswith(")"):
        # attempt to only strip one pair if matching
        # ensure parentheses match inside
        depth = 0
        ok = True
        for i, ch in enumerate(final_sql):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth == 0 and i < len(final_sql) - 1:
                ok = False
                break
        if ok:
            final_sql = final_sql[1:-1]

    result = [final_sql, final_params]

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        #info(f"or_buckets = {or_buckets}")
        #info(f"final_conditions = {final_conditions}")
        #info(f"final_params = {final_params}")
        info(f"\nresult = {result}")
        info(f"\ndebug_sql = {debug_sql(result[0],result[1])}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()
    return result

def fetch_and_display_entries(search = "", asListObj = False, stdout = True):
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

    PROJECT_EXPR = "REPLACE(REPLACE(p.description, '├─ ', ''), '└─ ', '')"
    search_raw = HCWR_GLOBALS.args.search
    if HCWR_GLOBALS.args.search is None:
        search_raw = search
    elif search and HCWR_GLOBALS.args.search:
        search_raw = search + "&(" + HCWR_GLOBALS.args.search + ")"

    if "S=" in search_raw:
        info(Fore.WHITE + "Suchparameter " + Fore.RED + "'S=' " + Fore.WHITE + "ist nicht mit Option:",Fore.RED + "-z/--zeiterfassung" + Fore.WHITE + " erlaubt!")
        show_process_route()

    if HCWR_GLOBALS.args.cat_time_totals_of:
        if len(search_raw) > 0:
            pipe = "|"
        if "," in HCWR_GLOBALS.args.cat_time_totals_of:
            search_raw = search_raw + pipe + "C=".join(HCWR_GLOBALS.args.cat_time_totals_of.split(","))
        else:
            search_raw = search_raw + pipe + "C=" + HCWR_GLOBALS.args.cat_time_totals_of

    if search_raw:
        search_items = [s.strip() for s in search_raw.replace("|", " OR °").replace("&", " AND °").replace("(", "").replace(")", "").split("°")]
    else:
        search_items = []

    # ------------------------------------------------------------
    # ⭐ NEUER PARSER WIRD HIER AUFGERUFEN
    # ------------------------------------------------------------
    if search_raw:
        where_expr = build_sql_from_search(search_raw, ph, PROJECT_EXPR)
        conditions.append(where_expr[0])
        params = where_expr[1]
    # ------------------------------------------------------------

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nsearch_raw = {search_raw}")
        info(f"asListObj = {asListObj}")
        info(f"stdout = {stdout}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()

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

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"query = {query}")
        info(f"params = {params}")
        info(f"query = {debug_sql(query, params)}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()

    # --- Ausführen ---
    cursor.execute(query, params)
    entries = cursor.fetchall()

    data = []

    for entry in entries:
        entry_id = f"Entry db ID: {entry[0]}"
        entry_cat = f"Category: {entry[1]}"
        if entry[2]:
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"entry_id = {entry_id}")
                info(f"entry_cat = {entry_cat}")
            start_time = entry[2][:19]
            end_time   = entry[3][:19]
            time_difference = calculate_time_difference(start_time, end_time)
            formatted_time = format_time_difference(time_difference)

            description = entry[4]

            # ------------------------------------------------------------
            # 🔥 Summierungs-Mechanismus für S=
            # ------------------------------------------------------------
            search_raw_items = [s.strip() for s in search_raw.replace("|", "°").replace("&", "°").replace("(", "").replace(")", "").split("°")]
            sum_item_like = [
                s[2:].strip("*") for s in search_raw_items
                if s.upper().startswith("S=")
            ]

            sum_existing = next(
                (s for s in sum_item_like if s in description),
                None
            )

            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"search_raw_items = {search_raw_items}")
                info(f"sum_item_like = {sum_item_like}")
                info(f"sum_existing = {sum_existing}")
                info(f"query = {debug_sql(query, params)}")
                prompt = "Enter für fortfahren oder N für Nein "
                answer = input_with_prefill(prompt, "", '')
                if answer in ("N", "n"):
                    show_process_route()

            if sum_existing:

                group_key = sum_existing
                debug(f"group_key = {group_key}")

                existing = next((e for e in data if sum_existing in e[5]), None)
                duration_sec = parse_duration(formatted_time)

                if existing:
                    existing[0] = f"{existing[0]}|{entry[0]}"
                    existing[2] = f"{existing[2]}|{start_time[:16]}"
                    existing[3] = f"{existing[3]}|{end_time[:16]}"
                    existing[4] += duration_sec
                    existing[5] = f"{existing[5]}|{description.strip(sum_existing.strip('/')).strip('/')}"
                    debug(f"existing = {existing}")

                else:
                    new_entry = [
                        entry_id,
                        entry_cat,
                        start_time[:16],
                        end_time[:16],
                        duration_sec,
                        f"{group_key}: {description.strip(group_key.strip('/')).strip('/')}"
                    ]
                    data.append(new_entry)

                continue

            new_entry = list(entry)
            new_entry.insert(4, formatted_time)
            new_entry[0] = entry_id
            new_entry[1] = entry_cat
            new_entry[2] = entry[2][:16]
            new_entry[3] = entry[3][:16]

            data.append(new_entry)

            if not asListObj and not HCWR_GLOBALS.args.zeiterfassung and not HCWR_GLOBALS.args.json and not HCWR_GLOBALS.args.sum_times:
                output(new_entry)

    if HCWR_GLOBALS.args.zeiterfassung:
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"data = {data}")
            info(f"HCWR_GLOBALS.args.zeiterfassung = {HCWR_GLOBALS.args.zeiterfassung}")
            info(f"HCWR_GLOBALS.args.sum_times = {HCWR_GLOBALS.args.sum_times}")
            info(f"HCWR_GLOBALS.args.json = {HCWR_GLOBALS.args.json}")
            prompt = "Enter für fortfahren oder N für Nein "
            answer = input_with_prefill(prompt, "", '')
            if answer in ("N", "n"):
                show_process_route()
        uid , spec = HCWR_GLOBALS.args.zeiterfassung.split(",")
        for row in data:
            sdate = format_date(row[2]+":00")
            dur = row[4]
            desc = row[5]
            line = textwrap.fill(f"{sdate}  {dur} ? {uid} [{spec}] {desc}", width=72, subsequent_indent=' '*24)
            output(line)
        show_process_route()

    conn.close()

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"DATA = {data}")
        info(f"asListObj = {asListObj}")
        info(f"HCWR_GLOBALS.args.sum_times = {HCWR_GLOBALS.args.sum_times}")
        info(f"HCWR_GLOBALS.args.json = {HCWR_GLOBALS.args.json}")
        prompt = "Enter für fortfahren oder N für Nein "
        answer = input_with_prefill(prompt, "", '')
        if answer in ("N", "n"):
            show_process_route()
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
                    line[1],
                    line[4],
                    line[5],
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
            info(f"SUM TIMES: new_data = {new_data}")
            show_process_route()
        return

    if HCWR_GLOBALS.args.json:
        to_json(data, stdout)
        info(f"JSON: data = {data}")
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            show_process_route()
        return data

    if asListObj:
        info(f"HCWR_GLOBALS.args.sum_times = {HCWR_GLOBALS.args.sum_times}")
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"asListObj: data = {data}")
            prompt = "Enter für fortfahren oder N für Nein "
            answer = input_with_prefill(prompt, "", '')
            if answer in ("N", "n"):
                show_process_route()
        return data

