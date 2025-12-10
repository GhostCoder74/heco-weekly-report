# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_dbg_mod.py
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
import inspect
import colorama
from colorama import Fore, Style
from os.path import basename

from hcwr_globals_mod import HCWR_GLOBALS

def debug(msg):
    """
    Gibt eine farbige Debug-Nachricht auf stderr aus, wenn DBG_LEVEL > 0 ist.

    Die Nachricht wird gelb und fett formatiert dargestellt.
    Zusätzlich wird automatisch der direkte Aufrufer (Datei und Zeilennummer) mit ausgegeben.

    Parameter:
        msg (str): Die auszugebende Debug-Nachricht.

    Voraussetzung:
        Die globale Variable DBG_LEVEL muss definiert und in eine Ganzzahl konvertierbar sein.
    """
    if int(HCWR_GLOBALS.DBG_LEVEL) != 0:
        stack = inspect.stack()
        caller = stack[1]  # Der direkte Aufrufer
        if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
            sys.stderr.write("\r" + " "*80 + "\r")
        print(f"Aufgerufen von: Zeile {caller.lineno}, Funktion {caller.function}")
        print(Fore.YELLOW + Style.BRIGHT + f"DEBUG: {msg}" + Style.RESET_ALL, file=sys.stderr)

def info(msg_a, msg_b="", type="Info"):
    """
    Gibt eine formatierte Informationsnachricht farbig auf stderr aus.

    Die Nachricht besteht aus einem Typ-Präfix (z. B. "Info", "Warnung", "Fehler") und zwei Textbestandteilen,
    die farblich unterschiedlich hervorgehoben werden.

    Parameter:
        msg_a (str): Hauptnachricht, wird in Weiß ausgegeben.
        msg_b (str, optional): Zusätzliche Nachricht, wird in Gelb ausgegeben (Standard: leer).
        type (str, optional): Typ-Präfix der Nachricht, wird in Blau ausgegeben (Standard: "Info").

    Ausgabe:
        Eine farbig formatierte Zeile wird auf stderr ausgegeben.
    """
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print(Fore.BLUE + Style.BRIGHT + f"{type}:" + Fore.WHITE + f" {msg_a}" + Fore.YELLOW + f" {msg_b}" + Style.RESET_ALL, file=sys.stderr)

def warning(msg_a, msg_b, type="Warning"):
    """
    Gibt eine formatierte Informationsnachricht farbig auf stderr aus.

    Die Nachricht besteht aus einem Typ-Präfix (z. B. "Info", "Warnung", "Fehler") und zwei Textbestandteilen,
    die farblich unterschiedlich hervorgehoben werden.

    Parameter:
        msg_a (str): Hauptnachricht, wird in Weiß ausgegeben.
        msg_b (str, optional): Zusätzliche Nachricht, wird in Gelb ausgegeben (Standard: leer).
        type (str, optional): Typ-Präfix der Nachricht, wird in Blau ausgegeben (Standard: "Info").

    Ausgabe:
        Eine farbig formatierte Zeile wird auf stderr ausgegeben.
    """
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print(Fore.RED + Style.BRIGHT + f"{type}:" + Fore.YELLOW + f" {msg_a}" + Fore.RED + f" {msg_b}" + Style.RESET_ALL, file=sys.stderr)

# For colorized output
colorama.init(autoreset=True)
# Definition of colors

def whereami():
    frame = inspect.currentframe().f_back
    file = basename(frame.f_code.co_filename)
    fn = frame.f_code.co_name
    ln = frame.f_lineno
    return {'file': file,'line': ln, 'fname': fn}

def get_function_name():
    stack = inspect.stack()
    caller = stack[1]  # Der direkte Aufrufer

    ffile = basename(caller.filename)
    fline = caller.lineno
    fname = caller.function

    # Falls aus <module> aufgerufen → Dateiname statt "<module>"
    display_name = ffile if fname == "<module>" else fname

    # aktuelle Tiefe
    depth = max(len(stack) - 2, 0)

    # Breakpoint
    fn = HCWR_GLOBALS.DBG_BREAK_POINT
    if fn and display_name in ("hcwr", "hcoh"):
        warning(f"Break Point is active for function:", fn, "Info")

    # Prozessroute
    if HCWR_GLOBALS.DBG_PROCESS_ROUTE:
        entry = f"{display_name} [{ffile}:{fline}]"
        HCWR_GLOBALS.DBG_PROCESS_ROUTE.append(entry)

        # Aufrufzähler
        HCWR_GLOBALS.DBG_CALL_COUNT[entry] = (
            HCWR_GLOBALS.DBG_CALL_COUNT.get(entry, 0) + 1
        )

        # für Call-Tree
        HCWR_GLOBALS.DBG_CALL_TREE.append((depth, entry))

    # Rückgabe:
    return display_name


def show_process_route():
    if HCWR_GLOBALS.DBG_PROCESS_ROUTE:
        debug(f"HCWR_GLOBALS.DBG_PROCESS_ROUTE_MODE = {HCWR_GLOBALS.DBG_PROCESS_ROUTE_MODE}")
        match int(HCWR_GLOBALS.DBG_PROCESS_ROUTE_MODE):
            case 1:
                show_process_route_as_list()
            case 2:
                show_process_route_as_log_pipe()
            case 3:
                show_process_route_as_diagramm()
            case 4:
                show_process_route_as_tree()
            case 5:
                show_process_route_as_counted_tree()
            case _:
                warning("Wrong DBG_PROCESS_ROUTE_MODE ist set:", HCWR_GLOBALS.DBG_PROCESS_ROUTE_MODE)
        sys.exit(1)
    else:
        sys.exit(0)

def show_process_route_as_list():
    steps = HCWR_GLOBALS.DBG_PROCESS_ROUTE
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print("\n=== PROCESS ROUTE ===", file=sys.stderr)
    for idx, step in enumerate(steps, 1):
        if ":" in step and " " in step:
            colored = Fore.BLUE + Style.BRIGHT + step.split(" ")[0] + Style.RESET_ALL
            colored += " FILE:" + Fore.YELLOW + step.split(" ")[1].split(":")[0] + Style.RESET_ALL
            colored += ":" + Fore.WHITE + step.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            colored = Fore.BLUE + Style.BRIGHT + step + Style.RESET_ALL
        print(f"{idx:02d}. {colored}", file=sys.stderr)
    print("=====================\n", file=sys.stderr)

def show_process_route_as_log_pipe():
    steps = HCWR_GLOBALS.DBG_PROCESS_ROUTE
    new_steps = []
    for idx, step in enumerate(steps, 1):
        if ":" in step and " " in step:
            colored = Fore.BLUE + Style.BRIGHT + step.split(" ")[0] + Style.RESET_ALL
            colored += " FILE:" + Fore.YELLOW + step.split(" ")[1].split(":")[0] + Style.RESET_ALL
            colored += ":" + Fore.WHITE + step.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            colored = Fore.BLUE + Style.BRIGHT + step + Style.RESET_ALL
        new_steps.append(colored)
        
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print("\n=== PROCESS PIPELINE ===", file=sys.stderr)
    print(" --> ".join(new_steps), file=sys.stderr)
    print("========================\n", file=sys.stderr)

def show_process_route_as_diagramm():
    steps = HCWR_GLOBALS.DBG_PROCESS_ROUTE
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print("\n=== PROCESS FLOWCHART ===", file=sys.stderr)
    for i, step in enumerate(steps):
        if ":" in step and " " in step:
            colored = Fore.BLUE + Style.BRIGHT + step.split(" ")[0] + Style.RESET_ALL
            colored += " FILE:" + Fore.YELLOW + step.split(" ")[1].split(":")[0] + Style.RESET_ALL
            colored += ":" + Fore.WHITE + step.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            colored = Fore.BLUE + Style.BRIGHT + step + Style.RESET_ALL
        if i == len(steps) - 1:
            print(f"└── {colored}", file=sys.stderr)
        else:
            print(f"├── {colored}", file=sys.stderr)
    print("==========================\n", file=sys.stderr)

def show_process_route_as_tree():
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print(Fore.CYAN + "\nPROCESS CALL TREE" + Style.RESET_ALL, file=sys.stderr)
    print(Fore.CYAN + "──────────────────────────────────────────\n" + Style.RESET_ALL, file=sys.stderr)
    tree = HCWR_GLOBALS.DBG_CALL_TREE
    for i, (depth, name) in enumerate(tree):
        # Baumzeichen
        is_last = (i == len(tree) - 1 or tree[i+1][0] < depth)
        prefix = ("│   " * (depth - 1) + 
                  ("└── " if is_last else "├── ") if depth > 0 else "")
        # Farbe für Funktionsnamen
        if ":" in name and " " in name:
            colored = Fore.BLUE + Style.BRIGHT + name.split(" ")[0] + Style.RESET_ALL
            colored += " FILE:" + Fore.YELLOW + name.split(" ")[1].split(":")[0] + Style.RESET_ALL
            colored += ":" + Fore.WHITE + name.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            colored = Fore.BLUE + Style.BRIGHT + name + Style.RESET_ALL
        print(prefix + colored, file=sys.stderr)
    print(Fore.CYAN + "\n──────────────────────────────────────────\n" + Style.RESET_ALL, file=sys.stderr)

def compress_call_tree(raw):
    if not raw:
        return []
    compressed = []
    last_depth, last_name = raw[0]
    count = 1
    for depth, name in raw[1:]:
        if name == last_name and depth == last_depth:
            count += 1
        else:
            compressed.append((last_depth, last_name, count))
            last_depth, last_name, count = depth, name, 1
    compressed.append((last_depth, last_name, count))
    return compressed

def show_process_route_as_counted_tree():
    if HCWR_GLOBALS.PBAR_VAL > 1 and HCWR_GLOBALS.PBAR_VAL != HCWR_GLOBALS.PBAR_MAX:
        sys.stderr.write("\r" + " "*80 + "\r")
    print(Fore.CYAN + "\nPROCESS CALL TREE" + Style.RESET_ALL, file=sys.stderr)
    print(Fore.CYAN + "──────────────────────────────────────────\n" + Style.RESET_ALL, file=sys.stderr)
    raw = HCWR_GLOBALS.DBG_CALL_TREE
    tree = compress_call_tree(raw)
    for i, (depth, name, count) in enumerate(tree):
        is_last = (
            i == len(tree) - 1 or 
            tree[i+1][0] < depth
        )
        prefix = ""
        if depth > 0:
            prefix = ("│   " * (depth - 1)) + ("└── " if is_last else "├── ")
        # Funktionsname farbig
        if ":" in name and " " in name:
            fname_colored = Fore.BLUE + Style.BRIGHT + name.split(" ")[0] + Style.RESET_ALL
            fname_colored += " FILE:" + Fore.YELLOW + name.split(" ")[1].split(":")[0] + Style.RESET_ALL
            fname_colored += ":" + Fore.WHITE + name.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            fname_colored = Fore.BLUE + Style.BRIGHT + name + Style.RESET_ALL
        # Aufrufzähler
        if count > 1:
            fname_colored += Fore.GREEN + f"  (x{count})" + Style.RESET_ALL
        print(prefix + fname_colored, file=sys.stderr)
    print(Fore.CYAN + "\n──────────────────────────────────────────\n" + Style.RESET_ALL)
    # OPTIONAL: Gesamte Aufrufstatistik
    print(Fore.MAGENTA + "\nFUNCTION CALL SUMMARY" + Style.RESET_ALL, file=sys.stderr)
    for k, v in HCWR_GLOBALS.DBG_CALL_COUNT.items():
        if " " in k and ":" in k:
            new_k = Fore.BLUE + Style.BRIGHT + k.split(" ")[0] + Style.RESET_ALL
            new_k += " FILE:" + Fore.YELLOW + k.split(" ")[1].split(":")[0] + Style.RESET_ALL
            new_k += ":" + Fore.WHITE + k.split(" ")[1].split(":")[1] + Style.RESET_ALL
        else:
            new_k.BLUE + Style.BRIGHT + k.RESET_ALL
        print("  " + new_k + ": " + Fore.GREEN + str(v) + " Aufrufe" + Style.RESET_ALL, file=sys.stderr)

def debug_sql(sql: str, params):
    """
    Ersetzt SQL-Platzhalter (?, %s) durch die echten Werte aus params
    und gibt einen fertigen SQL-String zurück, z.B. für sqlite3 tests.
    """
    fname = get_function_name()
    def quote(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        # Escape single quotes für SQL
        return "'" + str(v).replace("'", "''") + "'"

    # Wenn params nicht iterable ist → Fehler vermeiden
    if not isinstance(params, (list, tuple)):
        params = [params]

    final_sql = sql

    if "?" in sql:  
        # SQLite / MySQL-style
        for p in params:
            final_sql = final_sql.replace("?", quote(p), 1)

    elif "%s" in sql:
        # PostgreSQL-style  
        for p in params:
            final_sql = final_sql.replace("%s", quote(p), 1)

    return final_sql
