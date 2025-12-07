# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_remote_mod.py
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
import subprocess
import os
import sys
import time

from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route

def ssh_config_check():
    """
    Stellt sicher, dass in ~/.ssh/config ein 'Host hq' mit den Default-Werten existiert,
    inklusive User-Zeile (User wird abgefragt, wenn er fehlt).
    """
    fname = get_function_name()

    ssh_config_path = os.path.expanduser("~/.ssh/config")

    # Vorhandene Konfigurationszeilen lesen
    if os.path.exists(ssh_config_path):
        with open(ssh_config_path, "r") as f:
            config_lines = f.readlines()
    else:
        config_lines = []

    found_host = False
    has_user = False
    insert_index = None

    # Suche nach Host hq
    for i, line in enumerate(config_lines):
        if line.strip().lower() == f"host {HCWR_GLOBALS.SSH_HOST}":
            found_host = True
            insert_index = i
            for j in range(i + 1, len(config_lines)):
                if config_lines[j].strip().lower().startswith("host "):
                    break
                if config_lines[j].strip().lower().startswith("user "):
                    has_user = True
                    break
            break

    if not found_host:
        user = input(f"🔐 Kein Eintrag für 'Host {HCWR_GLOBALS.SSH_HOST}' gefunden. Bitte User angeben: ").strip()
        new_block = (
            f"\nHost {HCWR_GLOBALS.SSH_HOST}\n"
            f"    User {user}\n"
            f"    HostName {HCWR_GLOBALS.SSH_HOSTNAME}\n"
            f"    IdentityFile {HCWR_GLOBALS.SSH_IDENTITY_FILE}\n"
        )
        config_lines.append(new_block)
        info(f"✅ Neuer Block eingefügt für: ",f"'Host {HCWR_GLOBALS.SSH_HOST}'")
    elif found_host and not has_user:
        user = input(f"🔐 'Host {HCWR_GLOBALS.SSH_HOST}' vorhanden, aber kein User gesetzt. Bitte User angeben: ").strip()
        config_lines.insert(insert_index + 1, f"    User {user}\n")
        info(f"✅ User-Zeile ergänzt für: ", f"'Host {HCWR_GLOBALS.SSH_HOST}'")
    else:
        info(f"🔎 'Host {HCWR_GLOBALS.SSH_HOST}' mit User-Eintrag bereits vorhanden. Keine Änderung nötig.")

    # Datei zurückschreiben
    with open(ssh_config_path, "w") as f:
        f.writelines(config_lines)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)

def checkNfetch_file_from_NIS(remote_path, local_dest, ssh_host="hq"):
    """
    Prüft, ob die Datei lokal existiert, und kopiert sie bei Bedarf via rsync über SSH
    unter Nutzung der ~/.ssh/config Einträge.

    Parameter:
    - remote_path:  Pfad zur Datei auf dem Remote-Host
    - local_dest:   Ziel lokal
    - ssh_host:     Alias aus ~/.ssh/config, z. B. 'hq'

    Rückgabewert:
    - True  bei Erfolg (Datei existiert oder erfolgreich übertragen)
    - False bei Fehler
    """
    fname = get_function_name()
    ssh_config_check()

    if os.path.isfile(local_dest):
        info(f"✔️  Datei existiert bereits:", local_dest)
        return True

    info(f"⏳ Versuche, Datei per rsync zu holen, von:", f"{ssh_host}:{remote_path}...")

    try:
        subprocess.run(
            ["rsync", "-av", f"{ssh_host}:{remote_path}", local_dest],
            check=True
        )
        if os.path.isfile(local_dest):
            info(f"✅ Datei erfolgreich kopiert nach", local_dest)
            time.sleep(2)
            return True
        else:
            warning(f"❌ Datei wurde nicht wie erwartet kopiert:", local_dest)
            return False
    except subprocess.CalledProcessError as e:
        warning(f"❌ Fehler beim rsync:", e)
        return False

