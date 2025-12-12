# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           hcwr_json_mod.py
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
import json

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, show_process_route

def to_json(data, stdout=True):
    fname = get_function_name()
    return output(data, True, stdout)

def output(data, use_json=False, stdout=True):
    fname = get_function_name()
    if use_json:
        if stdout:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            show_process_route()
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        if isinstance(data, list):
            space = None
            for line in data:
                if space is None:
                    print(line)
                    space = "  "
                else:
                    print(f"{space}{line}")
            print("")
        else:
            if stdout:
                print(data)
            else:
                return data
