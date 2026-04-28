# python file for sql query definitions for postgresql
# LOA: Steht für "Leave of Absence" und wird im Personalwesen für 
#      eine Beurlaubung oder Freistellung von der Arbeit verwendet.
LOA_exists_sql = """
    SELECT id, description FROM entries
    WHERE id = %s
"""
LOA_delete_sql = """
    DELETE FROM entries
    WHERE date(start_time) = date(%s)
      AND project_id = %s
"""
LOA_update_sql = """
    UPDATE entries
        SET start_time = %s, stop_time = %s, description = %s
    WHERE id = %s
"""
LOA_insert_sql = """
    INSERT INTO entries (project_id, start_time, stop_time, description)
    VALUES (%s, %s, %s, %s)
"""
LOA_week_complete = """
    SELECT count(*) FROM entries WHERE start_time >= %s AND start_time < %s;
"""

total_per_project = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(EXTRACT ('epoch' FROM e.stop_time - e.start_time))) / 3600.0 AS duration
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
    GROUP BY p.id, p.key, p.description
    ORDER BY p.id DESC;
"""

total_per_project_by_week = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(EXTRACT ('epoch' FROM e.stop_time - e.start_time))) / 3600.0 AS duration
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id AND date(e.start_time) BETWEEN %s AND %s 
    GROUP BY p.id, p.key, p.description
    ORDER BY p.id DESC;
"""

wdayhours_sql = """
    SELECT
        SUM(CASE 
            WHEN EXTRACT(dow FROM e.start_time) = '1' THEN EXTRACT('epoch' from e.stop_time - e.start_time) / 3600.0
            ELSE 0 END) AS Mo,
        SUM(CASE
            WHEN EXTRACT(dow FROM e.start_time) = '2' THEN EXTRACT('epoch' from e.stop_time - e.start_time) / 3600.0
            ELSE 0 END) AS Di,
        SUM(CASE
            WHEN EXTRACT(dow FROM e.start_time) = '3' THEN EXTRACT('epoch' from e.stop_time - e.start_time) / 3600.0
            ELSE 0 END) AS Mi,
        SUM(CASE 
            WHEN EXTRACT(dow FROM e.start_time) = '4' THEN EXTRACT('epoch' from e.stop_time - e.start_time) / 3600.0
            ELSE 0 END) AS Do,
        SUM(CASE
            WHEN EXTRACT(dow FROM e.start_time) = '5' THEN EXTRACT('epoch' from e.stop_time - e.start_time) / 3600.0
            ELSE 0 END) AS Fr
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND (EXTRACT(WEEK FROM e.start_time) = %s OR EXTRACT(WEEK FROM e.stop_time) = %s)
    WHERE EXTRACT(dow FROM e.start_time) BETWEEN '1' AND '5' 
    """

wdayhours_sql_excl = """
	AND p.description NOT LIKE '%%Feiertag%%' 
	AND p.description NOT LIKE '%%Urlaub%%' 
	AND p.description NOT LIKE '%%Krank%%' 
	AND p.description NOT LIKE '%%Privat%%' 
	AND p.description NOT LIKE '%%Zeitkonto%%';
"""

absence = """
    SELECT
        REPLACE(REPLACE(p.description, '├─', ' '), '└─', ' ') AS description,
        COALESCE(SUM(EXTRACT('epoch' from e.stop_time - e.start_time))) / 3600.0 AS stunden
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
    WHERE EXTRACT(WEEK from e.start_time) = %s OR EXTRACT(WEEK FROM e.stop_time) = %s
    GROUP BY p.description;
"""

wday_absence = """
    SELECT
        COUNT(*) 
    FROM projects p
    LEFT JOIN entries e ON e.project_id = p.id
        AND EXTRACT(WEEK FROM e.start_time) = %s OR EXTRACT(WEEK FROM e.stop_time) = %s
    WHERE EXTRACT(WEEK FROM e.start_time) = %s
        AND (
            p.description LIKE '%%Krank%%' OR
            p.description LIKE '%%Urlaub%%' OR
            p.description LIKE '%%Feiertag%%'
        );
"""

insert_contract = """
    INSERT INTO contracts (keyword, contract_id, task)
    SELECT %s, %s, %s
    WHERE NOT EXISTS (
        SELECT 1 FROM contracts WHERE keyword = %s AND contract_id = %s
    )
"""

contract_by_keyword = """
    SELECT contract_id, category FROM contracts WHERE keyword = %s
"""

contract_delete = """
    DELETE FROM contracts WHERE keyword = %s
"""

contract_exists = """
    SELECT 1 FROM contracts WHERE keyword = %s AND contract_id = %s
"""

contract_insert = """
    INSERT INTO contracts (keyword, contract_id, category) VALUES (%s, %s, %s)
"""

create_contracts_tbl = """
    CREATE TABLE public.contracts (
        id integer NOT NULL,
        keyword text NOT NULL,
        contract_id text NOT NULL,
        task text
    );
"""

pid_by_description = """
    SELECT id FROM projects WHERE description = %s
"""

entry_update = """
    UPDATE entries SET description = %s WHERE description = %s AND date(start_time BETWEEN %s AND %s;
"""
create_entries_tbl = """
    CREATE TABLE IF NOT EXISTS entries (
        id integer NOT NULL,
        project_id integer,
        start_time timestamp without time zone NOT NULL,
        stop_time timestamp without time zone NOT NULL,
        description character varying(256),
        CONSTRAINT entries_check CHECK ((start_time <= stop_time))
    );
"""

create_projects = """
    CREATE TABLE IF NOT EXISTS projects (
        id integer NOT NULL,
        key character varying(16) NOT NULL,
        description character varying(256),
        active boolean DEFAULT true
    );
"""

create_recover = """
    CREATE TABLE IF NOT EXISTS recover (
        id integer NOT NULL,
        project_id integer,
        start_time timestamp without time zone NOT NULL,
        stop_time timestamp without time zone NOT NULL,
        description character varying(256),
        CONSTRAINT recover_check CHECK ((start_time <= stop_time))
    );
"""
