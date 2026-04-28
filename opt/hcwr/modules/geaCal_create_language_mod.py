# -----------------------------------------------------------------------------
# Project:        GaussEasterAlgorithm
# File:           create_language.py
# Author:         Christian Klose
# Email:          ghostcoder@gmx.de
# GitHub:         https://github.com/GhostCoder74/Set-Project-Headers (GhostCoder74)
# Copyright (c) 2025 Christian Klose
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of GaussEasterAlgorithm.
# Do not remove this header.
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------

"""
create_language.py – generate new language files from English base translation

Usage (internally or via geaCalCli):
    from create_language import create_language_file
    create_language_file("de")
"""

import json
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
LANG_DIR = MODULE_DIR / "lang"

def create_language_file(lang_code: str) -> Path:
    """Create a new language file based on en.json.
       If exists → return existing file.
    """
    lang_code = lang_code.lower()
    src = LANG_DIR / "en.json"
    dest = LANG_DIR / f"{lang_code}.json"

    if not src.exists():
        raise FileNotFoundError(f"Base language en.json missing at: {src}")

    if dest.exists():
        return dest  # already exists

    # Load English base
    base = json.loads(src.read_text(encoding="utf-8"))

    # Write new language file (structure identical to EN)
    dest.write_text(
        json.dumps(base, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    return dest

