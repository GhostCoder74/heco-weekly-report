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

wdayhours_sql = """
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
            ELSE 0 END) AS Fr
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND (isoweek(date(e.start_time), ?, ?) OR isoweek(date(e.stop_time), ?, ?))
    WHERE strftime('%w', e.start_time) BETWEEN '1' AND '5' 
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

entry_update = """
    UPDATE entries SET description = ? WHERE description = ? AND date(start_time BETWEEN ? AND ?;
"""

check_db_key_structure = """
    SELECT key FROM projects where (description LIKE '├─%' or description like '└─%') and not (description LIKE '  %' or description like '  %');
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
