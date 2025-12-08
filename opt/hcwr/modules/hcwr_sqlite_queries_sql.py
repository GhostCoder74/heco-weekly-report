# -----------------------------------------------------------------------------------------   
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter            
# File:           hcwr_sqlite_queries_sql.py
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
#
# python file for sql query definitions for sqlite
# LOA: Steht für "Leave of Absence" und wird im Personalwesen für 
#      eine Beurlaubung oder Freistellung von der Arbeit verwendet.
LOA_exists_sql = """
    SELECT id, description FROM entries
    WHERE date(start_time) = date(?)
      AND project_id = ?
"""
LOA_delete_sql = """
    DELETE FROM entries
    WHERE id = ?
"""
LOA_update_sql = """
    UPDATE entries
        SET start_time = ?, stop_time = ?, description = ?
    WHERE id = ?
"""
LOA_insert_sql = """
    INSERT INTO entries (project_id, start_time, stop_time, description)
    VALUES (?, ?, ?, ?)
"""

get_last_record_of_eintries = """
    SELECT *
    FROM entries
    ORDER BY start_time DESC, id DESC
    LIMIT 1
"""

get_last_record_of_eintries_today = """
    SELECT *
    FROM entries
    WHERE DATE(start_time) = DATE('now')
    ORDER BY start_time DESC, id DESC
    LIMIT 1
"""
week_complete = """
    SELECT count(*) FROM entries WHERE start_time >= ? AND start_time < ?;
"""

total_per_project = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(strftime('%s', e.stop_time) - strftime('%s', e.start_time)), 0) / 3600.0 AS total_duration
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
    GROUP BY p.id, p.key, p.description
    ORDER BY p.id DESC;
"""

total_per_project_by_week = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(strftime('%s', e.stop_time) - strftime('%s', e.start_time)), 0) / 3600.0 AS total_duration
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id AND date(e.start_time) BETWEEN ? AND ?
    GROUP BY p.id, p.key, p.description
    ORDER BY p.id DESC;
"""

tppbw_uuk = """
    SELECT
        e.start_time AS entry_start_time,
        e.id AS entry_id,
        e.description AS entry,
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(
            (julianday(e.stop_time) - julianday(e.start_time)) * 24.0,
        0) AS total_duration
    FROM projects p
    LEFT JOIN entries e 
        ON e.project_id = p.id
       AND DATE(e.start_time) BETWEEN ? AND ?
    WHERE p.id = ?
    ORDER BY e.start_time;
"""

whours_sql = """
    SELECT
        SUM((strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0) AS KW_Total
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND (isoweek(date(e.start_time), ?, ?) OR isoweek(date(e.stop_time), ?, ?))
    WHERE strftime('%w', e.start_time) BETWEEN '0' AND '6' 
"""

wdayhours_sql = """
    -- So = 0, Mo = 1, ..., Sa = 6
    SELECT
        SUM(CASE strftime('%w', e.start_time)
            WHEN '1' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Mo,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '2' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Di,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '3' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Mi,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '4' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Do,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '5' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Fr,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '6' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS Sa,
        SUM(CASE strftime('%w', e.start_time)
            WHEN '0' THEN (strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0
            ELSE 0 END) AS So,
        SUM((strftime('%s', e.stop_time) - strftime('%s', e.start_time)) / 3600.0) AS KW_Total
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND (isoweek(date(e.start_time), ?, ?) OR isoweek(date(e.stop_time), ?, ?))
    WHERE strftime('%w', e.start_time) BETWEEN '0' AND '6' 
"""

wdayhours_sql_excl = """
	AND p.description NOT LIKE '%Feiertag%' 
	AND p.description NOT LIKE '%Urlaub%' 
	AND p.description NOT LIKE '%Krank%' 
	AND p.description NOT LIKE '%Privat%' 
	AND p.description NOT LIKE '%Zeitkonto%';
"""

absence = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(strftime('%s', e.stop_time) - strftime('%s', e.start_time)), 0) / 3600.0 AS stunden
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
    WHERE (isoweek(date(e.start_time), ?, ?) OR isoweek(date(e.stop_time), ?, ?))
    GROUP BY p.description;
"""

wday_absence = """
    SELECT
        COUNT(*) 
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND (isoweek(date(e.start_time), ?, ?) OR isoweek(date(e.stop_time), ?, ?))
    WHERE strftime('%w', e.start_time) = ?
        AND (
            p.description LIKE '%Krank%' OR
            p.description LIKE '%Urlaub%' OR
            p.description LIKE '%Feiertag%'
        );
"""

pid_by_description = """
    SELECT id FROM projects WHERE description LIKE ?
"""
hcwrd_select = """
    SELECT * FROM entries WHERE project_id=? AND start_time BETWEEN ? AND ?
"""
entry_update = """
    UPDATE entries SET description = ? WHERE description = ? AND date(start_time BETWEEN ? AND ?;
"""

check_db_key_structure = """
    SELECT key FROM projects where (description LIKE '├─%' or description like '└─%' or key LIKE '3%') and not (description LIKE '  %' or description like '  %');
"""

create_contracts_tbl = """
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        contract_id TEXT NOT NULL,
        task TEXT
    );
"""

contract_insert = """
    INSERT INTO contracts (keyword, contract_id, task)
    SELECT ?, ?, ?
    WHERE NOT EXISTS (
        SELECT 1 FROM contracts WHERE keyword = ? AND contract_id = ?
    )
"""

contract_select = """
    SELECT keyword, contract_id, task FROM contracts;
"""

contract_by_keyword = """
    SELECT contract_id, task FROM contracts WHERE keyword = ?
"""

contract_delete = """
    DELETE FROM contracts WHERE keyword = ?
"""

contract_exists = """
    SELECT 1 FROM contracts WHERE keyword = ? AND contract_id = ?
"""

jobtime_entries = """
    SELECT
        e.id AS id,
        REPLACE(REPLACE(p.description, '├─ ', ''), '└─ ', '') AS project,
        e.start_time AS start_time,
        e.stop_time AS stop_time,
        e.description AS description
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
"""
