# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_extexec_mod.py
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
import re
import sys
import datetime
import subprocess
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route
from hcwr_config_mod import get_calendar_week
from hcwr_config_mod import get_weekday_hours_per_day, get_week_hours

def run_wochenfazit(file_path):
    """
    Führt wochenfazit.py mit der übergebenen Datei aus und gibt die Ausgabe auf stderr aus.
    """
    fname = get_function_name()
    try:
        result = subprocess.run(
            [HCWR_GLOBALS.WF_CHECK_PATH, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            text=True  # für str statt bytes
        )
        print(result.stdout, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Ausführen von {HCWR_GLOBALS.WF_CHECK_PATH}: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        sys.exit(0)
