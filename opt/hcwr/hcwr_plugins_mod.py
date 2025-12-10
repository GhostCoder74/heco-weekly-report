# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_plugins_mod.py
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
import subprocess
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from decimal import Decimal, InvalidOperation
import json
import colorama
from colorama import Fore, Style

# Import von eigenem Module
from hcwr_globals_mod import HCWR_GLOBALS
from hcwr_dbg_mod import debug, info, warning, get_function_name, debug_sql, show_process_route
from hcwr_utils_mod import get_wday_short_name, add_decimal_hours, command_exists

# set public holidays for this and next week

def insert_holiday_entries(db_connection, year, reference_date=None):
    """
    Fügt die Feiertage der aktuellen und nächsten Woche
    automatisch in die entries-Tabelle ein.

    Voraussetzungen:
    - get_holidays_this_and_next_week() ist bereits implementiert
    - project_id für Feiertage = 2
    """

    fname = get_function_name()

    # Feiertage ermitteln
    weeks = get_holidays_this_and_next_week(year, reference_date)

    if not reference_date is None:
        year = datetime.strptime(reference_date, "%Y-%m-%d").date().year

    exists_sql = HCWR_GLOBALS.DB_QUERIES.LOA_exists_sql
    delete_sql = HCWR_GLOBALS.DB_QUERIES.LOA_delete_sql
    update_sql = HCWR_GLOBALS.DB_QUERIES.LOA_update_sql
    insert_sql = HCWR_GLOBALS.DB_QUERIES.LOA_insert_sql

    cursor = db_connection.cursor()

    project_id = HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP.get('Feiertag')[0]

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nweeks = {weeks}")
        info(f"year = {year}")
        info(f"project_id['Feiertag'] = {project_id}")

    # Helper: Einfügen eines Feiertags
    def insert_one(date_str, name):
        fn = get_function_name()
        start_ts = f"{date_str} 00:00:00"
        wdname = get_wday_short_name(date_str)
        wdayhours = Decimal("8.0")
        if HCWR_GLOBALS.CFG.has_option("Workdays", wdname):
            wdayhours = Decimal(HCWR_GLOBALS.CFG.get("Workdays", wdname))
        stop_ts = add_decimal_hours(start_ts, wdayhours)
        desc     = f"Feiertag: {name}"

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"weeks = {weeks}")
            info(f"sql={debug_sql(insert_sql, (project_id, start_ts, stop_ts, desc))}")
        else:
            cursor.execute(insert_sql, (project_id, start_ts, stop_ts, desc))

    # Feiertage schreiben
    for (date_str, name) in weeks["current_week"]:
        insert_one(date_str, name)

    for (date_str, name) in weeks["next_week"]:
        insert_one(date_str, name)

    # Transaktion abschließen
    db_connection.commit()
    cursor.close()
    result = {
        "inserted_current_week": weeks["current_week"],
        "inserted_next_week": weeks["next_week"]
    }

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"result = {result}")
        show_process_route()
        sys.exit(0)
    else:
        return result

# geaCal Implementierung für Feiertags Entries
def get_holidays_this_and_next_week(year, reference_date=None):
    """
    Ruft geaCal auf, holt die JSON-Feiertage und gibt die Feiertage
    der aktuellen und der nächsten ISO-Woche zurück.
    """
    fname = get_function_name()

    # Pre-define of result
    result = {
        "current_week": [],
        "next_week": []
    }

    if not reference_date is None:
        year = datetime.strptime(reference_date, "%Y-%m-%d").date().year

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")

    # Checking for geaCal exists
    if not command_exists("geaCal"):
        warning("Plugin geaCal not found!", "No holyday check possible!")
        return result

    # --- 1. geaCal ausführen ---
    try:
        output = subprocess.check_output(
            ["geaCal", "-l", "-y", str(year), "-j"],
            text=True
        )
    except Exception as e:
        raise RuntimeError(f"geaCal konnte nicht ausgeführt werden: {e}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"output = {output}")
    # --- 2. JSON parsen ---
    try:
        data = json.loads(output)
        holidays = data.get("holidays", [])
    except Exception as e:
        raise ValueError(f"Ungültiges JSON von geaCal erhalten: {e}")

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"data = {data}")
    # --- 3. Referenzdatum bestimmen ---
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

    year_now, week_now, _ = reference_date.isocalendar()
    next_week = week_now + 1
    next_year = year_now

    # Jahreswechsel berücksichtigen
    if next_week > 52:
        next_week = 1
        next_year += 1

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"year_now = {year_now}")
        info(f"week_now = {week_now}")
        info(f"next_week = {next_week}")
        info(f"next_year = {next_year}")

    # --- 4. Feiertage der beiden Wochen filtern ---
    for hdate_str, name in holidays:
        hdate = datetime.strptime(hdate_str, "%Y-%m-%d").date()
        hy, hw, _ = hdate.isocalendar()

        if hy == year_now and hw == week_now:
            result["current_week"].append((hdate_str, name))
        elif hy == next_year and hw == next_week:
            result["next_week"].append((hdate_str, name))

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\nresult = {result}")
        show_process_route()
        sys.exit(0)

    return result

def date_to_ymd(date_obj):
    fname = get_function_name()
    if isinstance(date_obj , str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")
    
def is_feiertag(date_obj, cursor):
    """
    Prüft, ob 'date_obj' ein Feiertag ist, basierend auf
    get_holidays_this_and_next_week().
    """

    fname = get_function_name()

    if isinstance(date_obj , str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        year = date_obj.year
    elif isinstance(date_obj, date):
        year = date_obj.year
    else:
        warning(f"Wrong format of date: {date_obj}")
        sys.exit(1)

    # Datum als String, damit es zum Rückgabeformat passt
    date_str = date_obj.strftime("%Y-%m-%d")
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\ndate_str = {date_str}")

    holidays_dict = get_holidays_this_and_next_week(year, date_str )
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"holidays_dict = {holidays_dict}")

    if float(HCWR_GLOBALS.CFG.get("Workdays", get_wday_short_name(date_str))) == float(0):
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"date_str = {date_str}\nreturn 2")
        else:
            return 2
        
    # In beiden Wochen suchen
    for week in ("current_week", "next_week"):
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"week = {week}")
        
        hdict = holidays_dict.get(week, [])
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"hdict = {hdict}")
        if not hdict:
            def check_for_manuell_inserted_hdays(dstr):
                fn = get_function_name()
                fid = HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP.get('Feiertag')[0]
                exists_sql = HCWR_GLOBALS.DB_QUERIES.LOA_exists_sql
                cursor.execute(exists_sql, (dstr, fid))
                row = cursor.fetchone()
                if fn in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"{fn}:\ndate_str = {dstr}, row = {row[1]}")
                    show_process_route()
                    sys.exit(0)
                if row:
                    info(f"Manuellen Eintrag für Feiertag gefunden: " + 
                    Fore.MAGENTA + 
                    dstr + Fore.WHITE + " ist " +
                    Fore.MAGENTA + row[1])
                    return dstr
                return False    

            cres =  check_for_manuell_inserted_hdays(date_str)
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"cres = {cres}")
            return cres

        else:
            for hdate, _ in holidays_dict.get(week, []):
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"hdate = {hdate}")
                if hdate == date_str:
                    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                        info(f"hdate = {hdate}")
                        info(f"return {hdate}")
                    else:
                        return hdate

    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        show_process_route()
        info(f"return status: False")
        sys.exit(0)

    return False

def insert_LOA_entries(db_connection, hstart_date, pname="Urlaub", hstop_date=None, DEL_MODE=False, H=None, M=None):
    """
    Fügt, aktualisiert oder entfernt LOA-Einträge ("Leave of Absence") wie Urlaub,
    Krankheit, Feiertagsanpassungen oder andere interne Projekteinträge in der
    Tabelle `entries`.

    Die Funktion unterstützt:
        • Einzel-Tage und Datumsbereiche
        • Automatische Feiertags- und Wochenend-Erkennung
        • Speziallogik für Krankheit/Fehltage (Feiertage → 0 Stunden setzen)
        • INSERT, UPDATE oder DELETE je nach vorhandenen Einträgen
        • Debug-Ausgaben und SQL-Vorschau mittels `debug_sql()`

    -------------------------------------------------------------------------
    PARAMETER
    -------------------------------------------------------------------------
    db_connection : DB-Verbindung
        Eine geöffnete SQLite/MySQL/PSQL-Verbindung. Der Cursor wird intern 
        erzeugt und nach Abschluss automatisch geschlossen.

    hstart_date : str ("YYYY-MM-DD")
        Startdatum für den LOA-Zeitraum oder Einzel-Tag.

    pname : str (Default: "Urlaub")
        Internes Projektlabel. Muss in 
        HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP enthalten sein.
        Beispiele: "Urlaub", "Krank", "Feiertag", …

    hstop_date : str | None
        Wenn `None`: Einzel-Tag.
        Wenn gesetzt: Inklusive Enddatum → Bereichsverarbeitung.

    DEL_MODE : bool
        False → Einträge werden gesetzt/aktualisiert  
        True  → Einträge werden gelöscht

    -------------------------------------------------------------------------
    INTERN GENUTZTE GLOBALE STRUKTUREN
    -------------------------------------------------------------------------
    HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP
        Mapping: Projektname → (project_id, …)

    HCWR_GLOBALS.DB_QUERIES.<…>
        Enthält SQL-Statements für:
            • LOA_exists_sql  – prüfen, ob Eintrag bereits existiert
            • LOA_update_sql  – vorhandene Einträge aktualisieren
            • LOA_insert_sql  – neue Einträge anlegen
            • LOA_delete_sql  – Einträge löschen

    HCWR_GLOBALS.CFG
        INI-Konfiguration, Abschnitt "Workdays":
        definiert Arbeitsstunden pro Wochentag.

    HCWR_GLOBALS.DBG_BREAK_POINT
        Liste von Funktionsnamen für Debug-Abbruchpunkte.

    -------------------------------------------------------------------------
    ABLAUF
    -------------------------------------------------------------------------
    1. Projekt-ID ermitteln (z. B. Urlaub/Krank/Feiertag)
    2. Datumsbereich bestimmen (Einzel-Tag oder Range)
    3. Feiertage und Wochenenden prüfen
    4. Spezielle Behandlung für Krankheitstage:
        • Feiertagseinträge mit 0 Stunden überschreiben
    5. Für jeden Tag:
        • Arbeitsstunden bestimmen (Workdays)
        • SQL existiert? → UPDATE oder DELETE
        • SQL existiert nicht? → INSERT
    6. Änderungen committen
    7. Rückgabe: Dict { datum : "inserted" | "updated" | "skipped" }

    -------------------------------------------------------------------------
    HINWEISE ZU HELFERFUNKTIONEN
    -------------------------------------------------------------------------
    set_holyday_to_zero_hours(date_str)
        Wird verwendet, wenn pname "Krank" enthält.
        Prüft, ob am Datum bereits ein "Feiertag"-Eintrag existiert.
        Falls ja:
            • start_time bleibt 08:00:00
            • stop_time wird = start_time (0 Stunden)
        Effekt:
            Feiertag wird zu 0-Stunden-Krank-Tag geändert.

    run_sql_query(date_str)
        Hauptlogik pro Tag:
            1. Arbeitsstunden für den Wochentag laden
            2. start_time / stop_time erzeugen
            3. Existenzcheck via LOA_exists_sql
            4. Falls existiert:
                • DELETE (DEL_MODE=True) oder
                • UPDATE (DEL_MODE=False)
            5. Falls nicht existiert:
                • INSERT (nur wenn DEL_MODE=False)

    -------------------------------------------------------------------------
    RETURN
    -------------------------------------------------------------------------
    dict:
        { "YYYY-MM-DD": "inserted" | "updated" | "skipped" | True }

    -------------------------------------------------------------------------
    BESONDERHEITEN
    -------------------------------------------------------------------------
    * Bei ZKÜ=<H:M> oder ZKA=<H:M> wird H=Hours und M=Minutes übergeben von 
      Aussen, dann wird is_feiertag ignoriert, weil das g´keine Rolle spielt,
      da es sich enweder um: 
        "Zeitkonto Übertrag vom Vorjahr"
      oder:
        "Zeitkonto Abzug/Auszahlung"
      dann handelt und dies nur für das Zeitkonto relevant ist!
      Dabei wird die angegebenen HOURS:MINUTES entweder für ZKÜ oder ZKA 
      eingtragen.
    • Für Krankheitstage wird h_to_zero aktiviert → Feiertage werden 0 Stunden.
    • Bei Debug Breakpoints (HCWR_GLOBALS.DBG_BREAK_POINT) wird SQL angezeigt 
      und ggf. `sys.exit(0)` ausgeführt.
    • Die Funktion verändert keine globalen Strukturen.
    """

    msg_lbl_map = HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP
    fname = get_function_name()

    # ----------------------------------------------------------------------
    # Projekt-ID ermitteln (z.B. Urlaub/Krank/Feiertag)
    # HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP liefert die zugehörige interne ID.
    # ----------------------------------------------------------------------
    project_id = HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP.get(pname)[0]

    cursor = db_connection.cursor()
    # ----------------------------------------------------------------------
    # SQL-Statements je nach DBMS (werden aus globaler Struktur geladen)
    # ----------------------------------------------------------------------
    exists_sql = HCWR_GLOBALS.DB_QUERIES.LOA_exists_sql
    delete_sql = HCWR_GLOBALS.DB_QUERIES.LOA_delete_sql
    update_sql = HCWR_GLOBALS.DB_QUERIES.LOA_update_sql
    insert_sql = HCWR_GLOBALS.DB_QUERIES.LOA_insert_sql

    # ----------------------------------------------------------------------
    # HELFER: Feiertagseinträge modifizieren bei Krankheit
    # Wenn pname "Krank" enthält:
    #   - Feiertage werden als vorhanden erkannt
    #   - Diese werden per UPDATE auf 0 Stunden gesetzt
    #   - Benutzt LOA_exists_sql und LOA_update_sql
    # ----------------------------------------------------------------------
    h_to_zero = False
    def set_holyday_or_vacation_to_zero_hours(date_str, pn):
        fsubname = get_function_name()
        pid = HCWR_GLOBALS.INTERN_PROJEKT_ID_MAP.get(pn)[0]

        # Existenz prüfen: Startzeit 08:00:00
        PH_start_ts = f"{date_str} 08:00:00"
        cursor.execute(exists_sql, (PH_start_ts, pid))
        row = cursor.fetchone()

        # Debug-Ausgabe
        if fsubname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"{fsubname}:\ndate_str = {date_str}")
            p = [PH_start_ts, pid]
            info(f"exists_sql = {debug_sql(exists_sql, p)}")
            info(f"row = {row}")

        # Wenn ein Feier- oder Urlaubstag existiert → auf 0 Stunden setzen
        # Bei DEL_MODE = True, Stunden wieder herstellen!
        if row:
            PH_entry_id  = row[0]
            PH_labeldesc = row[1]

            wdname = get_wday_short_name(date_str)
            wdayhours = Decimal("8.0")
            if HCWR_GLOBALS.CFG.has_option("Workdays", wdname):
                wdayhours = Decimal(HCWR_GLOBALS.CFG.get("Workdays", wdname))

            # DEL_MODE = True → Feiertag wieder normale Stunden
            if DEL_MODE:
                PH_stop_ts = add_decimal_hours(PH_start_ts, wdayhours)
                info_msg = [f"\n      Stunden für {pn} am:", f"{date_str} wieder auf {wdayhours} zurück gesetzt", "Löschung der "]
            else:
                info_msg = [f"\n      Stunden für {pn} am:", f"{date_str} auf 0 gesetzt, wegen {pname}!", ""]
                PH_stop_ts = PH_start_ts  # 0 Stunden

            warning(info_msg[0],info_msg[1],f"Info zur {info_msg[2]}{pname} Eintragung")
            
            # Debug-Block
            if fsubname in HCWR_GLOBALS.DBG_BREAK_POINT:
                p = [PH_start_ts, PH_stop_ts, PH_labeldesc, PH_entry_id]
                info(f"update_sql = {debug_sql(update_sql, p)}")
                if not HCWR_GLOBALS.args.dry_run:
                    cursor.execute(update_sql, (PH_start_ts, PH_stop_ts, PH_labeldesc, PH_entry_id))
                else:
                    warning(f"SQL-Execution not applied, because: ", "DRY-RUN MODE active!")
            else:
                cursor.execute(update_sql, (PH_start_ts, PH_stop_ts, PH_labeldesc, PH_entry_id))

            return False
        else:
            return

    # ----------------------------------------------------------------------
    # Debug-Ausgabe für Startparameter
    # ----------------------------------------------------------------------
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"{fname}:\npname = {pname}, project_id = {project_id}, DEL_MODE = {DEL_MODE}, H = {H}, M = {M}")

    # ----------------------------------------------------------------------
    # DATUMSBEREICH bestimmen:
    #   - Ohne hstop_date → Einzel-Tag
    #   - Mit hstop_date  → Bereich inkl. Enddatum
    # Feiertage werden ggf. ignoriert (Warnung)
    # ----------------------------------------------------------------------
    if hstop_date is None:
        if H and M: # Disable Holyday Check if ZKÜ=<H:M> or ZKA=<H:M> was set
            res = None
        else:
            res = is_feiertag(hstart_date, cursor)

        # Krankheit → Feiertage zu 0 Stunden
        if "Krank" in pname:
            h_to_zero = True
            res = set_holyday_or_vacation_to_zero_hours(hstart_date, 'Feiertag')
            h_to_zero = True
            res = set_holyday_or_vacation_to_zero_hours(hstart_date, 'Urlaub')

        # Nur aufnehmen, wenn kein Feiertag oder wenn 0-Stunden erzwungen
        if not res or h_to_zero:
            dates = [hstart_date]
        else:
            if res == 2:
                warning("Wird ignoriert: ", f"{hstart_date} ist ein {get_wday_short_name(hstart_date)}.")
            else:
                warning("Wird ignoriert: ", f"{hstart_date} ist ein Feiertag!")
            return
    else:
        # Range erstellen
        start = datetime.strptime(hstart_date, "%Y-%m-%d").date()
        stop  = datetime.strptime(hstop_date, "%Y-%m-%d").date()
        delta = (stop - start).days

        dates = []
        for i in range(delta + 1):
            entry_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            res = is_feiertag(entry_date, cursor)

            # Debug: Feiertagsprüfung
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"is_feiertag({entry_date}) => res = {res}")

            # Krankheit → Feiertage prüfen/0 Stunden setzen
            if "Krank" in pname:
                h_to_zero = True
                res = set_holyday_or_vacation_to_zero_hours(entry_date, 'Feiertag')
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"pname = {pname}, res = {res}")
                res = set_holyday_or_vacation_to_zero_hours(entry_date, 'Urlaub')
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"pname = {pname}, res = {res}")

            # Nur erlaubte Tage aufnehmen
            if not res or h_to_zero:
                dates.append(entry_date)
            else:
                if res == 2:
                    warning("Wird ignoriert: ", f"{entry_date} ist ein {get_wday_short_name(entry_date)}.")
                else:
                    warning("Wird ignoriert: ", f"{entry_date} ist ein Feiertag!")

    # ----------------------------------------------------------------------
    # HELFER: Führt SQL für einen einzelnen Tag aus.
    # Entscheidet INSERT / UPDATE / DELETE.
    # ----------------------------------------------------------------------
    def run_sql_query(date_str):
        fn = get_function_name()
        start_ts = None
        m = HCWR_GLOBALS.REGEX_DATETIME
        r = m.search(date_str)
        if r:
            start_ts = date_str
            date_str = date_str.split(" ")[0]
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                info(f"r = {r}")
                info(f"date_str = {date_str}")
                info(f"start_ts = {start_ts}")
                info(f"exists_sql={debug_sql(exists_sql, (start_ts, project_id))}")

        wdname = get_wday_short_name(date_str)

        # Arbeitsstunden des Wochentags bestimmen
        wdayhours = Decimal("8.0")
        if HCWR_GLOBALS.CFG.has_option("Workdays", wdname):
            wdayhours = Decimal(HCWR_GLOBALS.CFG.get("Workdays", wdname))

        # No work day → no entry saving!
        if wdayhours == 0:
            return "skipped"
        if not start_ts:
            start_ts = f"{date_str} 08:00:00"
        if H and M: # Set Hours and Minutes if AU,PRIV,ZKÜ,ZKA=<H:M> was set
            wdayhours = float(int(H) + int(M) / 60)
        stop_ts = add_decimal_hours(start_ts, wdayhours)
        desc = pname

        # Existenzcheck: existiert LOA-Eintrag bereits?
        if r:
            cursor.execute(exists_sql, (start_ts, project_id))
        else:
            cursor.execute(exists_sql, (date_str, project_id))
        row = cursor.fetchone()

        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            if r:
                info(f"exists_sql={debug_sql(exists_sql, (start_ts, project_id))}")
            else:
                info(f"exists_sql={debug_sql(exists_sql, (date_str, project_id))}")
            info(f"row = {row}")
        # ------------------------------------------------------------------
        # UPDATE oder DELETE
        # ------------------------------------------------------------------
        if row:
            entry_id = row[0]

            sql = delete_sql if DEL_MODE else update_sql

            # Debug-Ausgabe
            if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                lbl = "DELETE" if DEL_MODE else "UPDATE"
                info(f"[{lbl}] Entry '{pname}', {date_str}, id={entry_id}")

            # DELETE
            if DEL_MODE:
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"sql={debug_sql(sql, (entry_id,))}")
                    if not HCWR_GLOBALS.args.dry_run:
                        cursor.execute(sql, (entry_id,))
                    else:
                        warning(f"SQL-Execution not applied, because: ", "DRY-RUN MODE active!")
                else:
                    cursor.execute(sql, (entry_id,))
            else:
                # UPDATE
                if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
                    info(f"sql={debug_sql(sql, (start_ts, stop_ts, desc, entry_id))}")
                    if not HCWR_GLOBALS.args.dry_run:
                        cursor.execute(sql, (start_ts, stop_ts, desc, entry_id))
                    else:
                        warning(f"SQL-Execution not applied, because: ", "DRY-RUN MODE active!")
                else:
                    cursor.execute(sql, (start_ts, stop_ts, desc, entry_id))

            lbl = "entfernt" if DEL_MODE else "aktualisiert"
            info(f"{msg_lbl_map[pname][3]} Eintrag {lbl}: {date_str}")

            return "updated"

        # ------------------------------------------------------------------
        # DELETE ohne vorhandenen Eintrag → erledigt
        # ------------------------------------------------------------------
        if DEL_MODE:
            return True

        # ------------------------------------------------------------------
        # INSERT
        # ------------------------------------------------------------------
        if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
            info(f"[INSERT] {msg_lbl_map[pname][3]} {date_str}")
            info(f"sql={debug_sql(insert_sql, (project_id, start_ts, stop_ts, desc))}")

            if not HCWR_GLOBALS.args.dry_run:
                cursor.execute(insert_sql, (project_id, start_ts, stop_ts, desc))
            else:
                warning(f"SQL-Execution not applied, because: ", "DRY-RUN MODE active!")
        else: 
            cursor.execute(insert_sql, (project_id, start_ts, stop_ts, desc))
        
        info(f"{msg_lbl_map[pname][3]} eingetragen: {date_str}")

        return "inserted"

    # ----------------------------------------------------------------------
    # Hauptschleife über alle Tage
    # ----------------------------------------------------------------------
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"dates = {dates}")
    results = {}
    for d in dates:
        results[d] = run_sql_query(d)

    # Änderungen übernehmen
    db_connection.commit()
    cursor.close()

    # Debug: Ergebnisse zeigen
    if fname in HCWR_GLOBALS.DBG_BREAK_POINT:
        info(f"results = {results}")
        show_process_route() 
        sys.exit(0)

    return results
