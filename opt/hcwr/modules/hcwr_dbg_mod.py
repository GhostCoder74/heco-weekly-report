# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_dbg_mod.py
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
import inspect
import colorama
from colorama import Fore, Style

from hcwr_globals_mod import HCWR_GLOBALS

def get_function_name():
    stack = inspect.stack()
    caller = stack[1]  # Der direkte Aufrufer
    fname = caller.function
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        warning(f"Break Point is active for function:", fname, "Info")
    return caller.function

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
        print(f"Aufgerufen von: Zeile {caller.lineno}, Funktion {caller.function}")
        print(get_fore_color("YELLOW") + Style.BRIGHT + f"DEBUG: {msg}" + Style.RESET_ALL, file=sys.stderr)

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
    print(get_fore_color("BLUE") + Style.BRIGHT + f"{type}:" + get_fore_color("WHITE") + f" {msg_a}" + get_fore_color("YELLOW") + f" {msg_b}" + Style.RESET_ALL, file=sys.stderr)

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
    print(get_fore_color("RED") + Style.BRIGHT + f"{type}:" + get_fore_color("YELLOW") + f" {msg_a}" + get_fore_color("RED") + f" {msg_b}" + Style.RESET_ALL, file=sys.stderr)

# For colorized output
colorama.init(autoreset=True)
# Definition of colors
def get_fore_color(color):
    """
    Returns the color code for text foreground in the console based on the
    given color name.

    :param color: A string representing the color name.
    Available color names are:
                 - "RED" (default for error messages)
                 - "MAGENTA"
                 - "GREEN"
                 - "YELLOW" (default for debug messages)
                 - "BLUE"
                 - "WHITE" (default for info messages)

    :return: The color code for the specified color, or Fore.RESET if the color
             name is not recognized.
    """
    colors = {
        "RED": Fore.RED,        # Default für Error
        "MAGENTA": Fore.MAGENTA,
        "GREEN": Fore.GREEN,
        "YELLOW": Fore.YELLOW,  # Default für Debug
        "BLUE": Fore.BLUE,
        "WHITE": Fore.WHITE,    # Default für Info
        # Weitere Farben hier hinzufügen, falls gewünscht
    }
    return colors.get(color, Fore.RESET)

def debug_sql(sql: str, params):
    """
    Ersetzt SQL-Platzhalter (?, %s) durch die echten Werte aus params
    und gibt einen fertigen SQL-String zurück, z.B. für sqlite3 tests.
    """

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
