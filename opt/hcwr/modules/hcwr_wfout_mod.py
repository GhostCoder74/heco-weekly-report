# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_wfout_mod.py
# Authors:        Christian Klose <cklose@intevation.de>                                      
#                 Raimund Renkert <rrenkert@intevation.de>                                    
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)           
# Copyright (c) 2024-2026 by Intevation GmbH                                                  
# SPDX-License-Identifier: GPL-2.0-or-later                                                   
#
# File version:   1.0.4
# 
# This file is part of "hcwr - heco Weekly Report"                                            
# Do not remove this header.                                                                  
# Wochenfazit URL:                                                                            
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit    
# Header added by https://github.com/GhostCoder74/Set-Project-Headers                         
# -----------------------------------------------------------------------------------------
import os
import sys
import shutil
import tempfile
import subprocess
import colorama
from colorama import Fore, Style
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route
from hcwr_utils_mod import format_decimal, get_wday_diff, input_with_prefill, chgrp
from hcwr_extexec_mod import run_wochenfazit
from hcwr_tasks_mod import get_my_tasks 

def SecToHours(sec, xtype=","):
    result = Decimal(sec / 3600).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)
    if xtype == ",":
       return format_decimal(result)        
    return result

# Final report output
def generate_report(work_hours, kw_should, contract_hours, feiertage, urlaub, abwesend,
                    kw_old_overhours, kw_overhours_add, kw_stundenkonto, result, zk_minus,
                    conn, wdays, myname):
    """
    Erzeugt die den Bericht für das Wochenfazit
    """
    fname = get_function_name()

    report_lines = []
    week_str = f"{HCWR_GLOBALS.args.year}-W{HCWR_GLOBALS.args.week:02d}"
    report_lines.append(f"Wochenfazit: {week_str} Name: {myname}\n")
    report_lines.append(
        f"Arbeitsstunden: {SecToHours(work_hours)} von {SecToHours(kw_should)} "
        f"(Vertrag: {contract_hours}  Feiertage: {SecToHours(feiertage)}  "
        f"Urlaub: {SecToHours(urlaub)}  abwesend: {SecToHours(abwesend)})"
    )
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"sign = {HCWR_GLOBALS.SIGN}")
        info(f"kw_overhours_add = {SecToHours(kw_overhours_add)}")
        info(f"kw_old_overhours = {SecToHours(kw_old_overhours)}")
        info(f"kwADD = {SecToHours(kw_overhours_add)}")
    kwOLD = SecToHours(kw_old_overhours)
    kwADD = SecToHours(kw_overhours_add, False)
    ZK = SecToHours(kw_stundenkonto)
    if kwADD < 0:
        sign = "-"
    else:
        sign = "+"
    report_lines.append(
        f"Stundenkonto: {kwOLD} {sign} {format_decimal(abs(kwADD))} "
        f"= {ZK}"
    )

    # Tagabweichungen hinzufügen (erst jetzt!)
    report_lines.append(get_wday_diff(conn, wdays, HCWR_GLOBALS.args.year, HCWR_GLOBALS.args.week))

    conn.close()

    if work_hours > 0 and kw_should > 0:

        # TODO: Per config option oder arg eine Uniq-Liste der Tätigkeiten der KW einfügen wenn dies gesetzt wurde.
        my_tasks = None
        if HCWR_GLOBALS.CFG.has_option('General', 'insert_tasks'):
            if HCWR_GLOBALS.CFG.get("General", "insert_tasks").lower() == "true":
                my_tasks = get_my_tasks()

        # my_tasks ist noch in Arbeit
        if my_tasks is None:
            my_tasks = HCWR_GLOBALS.REMINDER_TXT
        report_lines.append(f"\nFür uns miterreicht habe ich:\n  {my_tasks}")
        report_lines.append(f"\nGelernt habe ich:\n  {HCWR_GLOBALS.REMINDER_TXT}")
        report_lines.append(f"\nUns besser machen würde vielleicht:\n  {HCWR_GLOBALS.REMINDER_TXT}\n")

        # Workload breakdown
        report_lines.append("Stundenaufteilung:")
        percent_part = Decimal(0.0) if work_hours == 0 else Decimal(100) / Decimal(work_hours/3600)

        groups = []
        current_group = None
        if int(HCWR_GLOBALS.DBG_LEVEL) == 1:
            debug(f"generate_report: result = {result}")
            debug(f"#############################################################################")
        for item in result:
            if int(HCWR_GLOBALS.DBG_LEVEL) == 1:
                debug(f"generate_report: item = {item}")
            is_sub = item['description'].startswith("  ")

            if SecToHours(item['duration'], False) > 0:
                if not is_sub:
                    if current_group:
                        groups.append(current_group)
                    p = round(percent_part * SecToHours(item['duration'], False), 0)
                    current_group = {
                        "percent": p,
                        "parent": item,
                        "subs": []
                    }
                else:
                    if current_group:
                        current_group["subs"].append(item)

        if current_group:
            groups.append(current_group)

        groups.sort(key=lambda g: g["percent"], reverse=True)
        for group in groups:
            p = group["percent"]
            parent = group["parent"]
            report_lines.append(f"{p}%: {parent['description']}: {SecToHours(parent['duration'])}")
            for sub in group["subs"]:
                line = ""
                if 'task' in sub and sub['task']:
                    line += f"  {sub['task']} {sub.get('contract_id', '')}: {SecToHours(sub['duration'])}"
                else:
                    line += f"{sub.get('description', '')}: {SecToHours(sub['duration'])}"
                report_lines.append(line)

                if int(HCWR_GLOBALS.DBG_LEVEL) == -99:
                    debug(f"sub = {sub}")
                uuk_entries = sub.get('uuk')
                if int(HCWR_GLOBALS.DBG_LEVEL) == -99:
                    info("uuk_entries = ",uuk_entries)
                    debug(f"config = {HCWR_GLOBALS.has_option('General', 'show_uuk')}")
                if uuk_entries != None:
                    if HCWR_GLOBALS.CFG.has_option("General", "show_uuk"):
                        if HCWR_GLOBALS.CFG.get("General", "show_uuk").lower() == "true":
                            if int(HCWR_GLOBALS.DBG_LEVEL) == -99:
                                info("uuk = ",uuk_entries)
                            if isinstance(uuk_entries, dict):
                                if int(HCWR_GLOBALS.DBG_LEVEL) == -99:
                                    info("uuk is dict")
                                desc = uuk_entries['description']
                                dur = uuk_entries['duration']
                                if desc and dur is not None:
                                    report_lines.append(f"{desc}: {SecToHours(dur)}")

    if zk_minus > 0:
        report_lines.append(f"\nPS:\n  {HCWR_GLOBALS.MAPPING['zk_minus'][0]}: {SecToHours(zk_minus)}")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        print("\n".join(report_lines))
        show_process_route()
        sys.exit(1)

    return "\n".join(report_lines)

def handle_output(report_content: str):
    #TODO: MY_EDITOR Variable etablieren
    """
    Gibt den Bericht als STDOUT oder Datei zum editieren geöffnet in vim
    """
    fname = get_function_name()

    if HCWR_GLOBALS.args.dry_run:
        print(report_content)
    else:
        # Zielpfade vorbereiten
        kwd = HCWR_GLOBALS.KW_REPORT_DIR
        os.makedirs(kwd, exist_ok=True)

        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as f:
            f.write(report_content)
            f.flush()
            tempname = f.name

        # Öffne vim zur Bearbeitung
        subprocess.call(["vim", tempname])

	# Nach Bearbeitung fragen, ob wochenfazit.py zur Prüfung ausgeführt werden soll (Enter = Ja)
        prompt = (f"Soll der Bericht nun " + Fore.BLUE + Style.BRIGHT + f"'{tempname}'" + Style.RESET_ALL + f"  geprüft werden, von \n\n {HCWR_GLOBALS.WF_CHECK_PATH}\n\n [J/n]: ")
        answer = input_with_prefill(prompt, "", "").strip().lower()
        if answer in ("", "j", "ja", "y", "yes"):
            run_wochenfazit(tempname)
	# Nach Bearbeitung fragen, ob speichern (Enter = Ja)
        prompt = (f"Soll der Bericht nach " + Fore.BLUE + Style.BRIGHT + f"'{HCWR_GLOBALS.KW_REPORT_FILE}'" + Style.RESET_ALL + f" gespeichert werden? [J/n]: ")
        answer = input_with_prefill(prompt, "", "").strip().lower()
        if answer in ("", "j", "ja", "y", "yes"):
            shutil.copy(tempname, HCWR_GLOBALS.KW_REPORT_FILE)
            os.remove(tempname)
            print(Fore.GREEN + Style.BRIGHT + f"\n✅ Bericht gespeichert unter: {HCWR_GLOBALS.KW_REPORT_FILE}" + Style.RESET_ALL, file=sys.stderr)
            chgrp(HCWR_GLOBALS.KW_REPORT_FILE, HCWR_GLOBALS.args.group)
        else:
            os.remove(tempname)
            print(Fore.RED + Style.BRIGHT + f"X Bericht wurde verworfen." + Style.RESET_ALL, file=sys.stderr)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

