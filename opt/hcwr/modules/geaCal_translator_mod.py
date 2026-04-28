# -----------------------------------------------------------------------------
# Project:        GaussEasterAlgorithm
# File:           translator.py
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

import json
import os
import locale

_LANG_DIR = os.path.join(os.path.dirname(__file__), "lang")
_FALLBACK_LANG = "en"

_cache = {}
_runtime_lang = None


# ---------------------------------------------------------------
# Runtime override, used by CLI (--lang de)
# ---------------------------------------------------------------
def set_runtime_language(lang: str):
    global _runtime_lang
    _runtime_lang = lang.lower()


# ---------------------------------------------------------------
# Determine locale language
# ---------------------------------------------------------------
def detect_system_lang() -> str:
    loc = locale.getdefaultlocale()[0]
    if not loc:
        return _FALLBACK_LANG
    return loc.split("_")[0]


# ---------------------------------------------------------------
# Load language JSON file into cache
# ---------------------------------------------------------------
def load_language(lang_code: str) -> dict:
    lang_code = lang_code.lower()

    if lang_code in _cache:
        return _cache[lang_code]

    file = os.path.join(_LANG_DIR, f"{lang_code}.json")

    if os.path.isfile(file):
        with open(file, "r", encoding="utf-8") as f:
            _cache[lang_code] = json.load(f)
            return _cache[lang_code]

    # fallback to english
    fallback_file = os.path.join(_LANG_DIR, f"{_FALLBACK_LANG}.json")
    with open(fallback_file, "r", encoding="utf-8") as f:
        _cache[_FALLBACK_LANG] = json.load(f)
        return _cache[_FALLBACK_LANG]


# ---------------------------------------------------------------
# Automatic extension of missing keys
# ---------------------------------------------------------------
def ensure_key_exists(lang_code: str, key: str, en_value: str):
    """If a language misses a key, append it automatically."""
    lang_file = os.path.join(_LANG_DIR, f"{lang_code}.json")

    if not os.path.isfile(lang_file):
        return

    with open(lang_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if key not in data:
        data[key] = en_value
        with open(lang_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------------------------------------------------------
# Translation function
# ---------------------------------------------------------------
def t(phrase: str) -> str:
    # Step 1: determine target language
    lang_code = _runtime_lang or detect_system_lang()
    lang = load_language(lang_code)

    # Step 2: English fallback
    en_lang = load_language(_FALLBACK_LANG)

    # Step 3: extend missing keys automatically
    ensure_key_exists(lang_code, phrase, en_lang.get(phrase, phrase))

    # Step 4: translation logic
    # language key exists → return translation
    if phrase in lang:
        return lang[phrase]

    # english exists → fallback
    if phrase in en_lang:
        return en_lang[phrase]

    # fallback to phrase itself
    return phrase

