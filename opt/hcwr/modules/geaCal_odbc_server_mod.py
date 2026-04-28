import socket
import json
from geaCal_holidays_mod import get_holiday, list_holidays_for_year



def row_to_dict(row):
    """
    Converts tuples, objects or dicts to dicts with known keys.
    Ensures our SQL server never crashes regardless of the row format.
    """

    # If already a dict → keep it
    if isinstance(row, dict):
        return row

    # If tuple/list → map to known fields
    if isinstance(row, (tuple, list)):
        # Define your canonical column order
        cols = ["date", "name", "region", "movable"]

        d = {}
        for i in range(min(len(row), len(cols))):
            d[cols[i]] = row[i]

        return d

    # If object → try attributes
    if hasattr(row, "__dict__"):
        return row.__dict__

    # Unknown type → convert to string
    return {"value": str(row)}


def execute_sql(sql):
    """
    Very small SQL parser.
    Currently supports:
    SELECT * FROM holidays;
    SELECT * FROM holidays WHERE year=2025;
    """

    sql = sql.strip().upper()

    if not sql.startswith("SELECT"):
        return {"error": "Only SELECT queries are supported"}

    # Default year
    year = 2025

    if "WHERE YEAR=" in sql:
        try:
            part = sql.split("WHERE YEAR=")[1]
            year = int(part.split()[0].replace(";", ""))
        except Exception:
            return {"error": "Invalid WHERE YEAR=..."}

    # Get holidays (whatever format is returned)
    try:
        holidays = list_holidays_for_year(year)
    except Exception as e:
        return {"error": f"Holiday module error: {e}"}

    # Normalize rows into dicts
    rows = []
    for idx, h in enumerate(holidays):
        d = row_to_dict(h)

        # guarantee these keys exist
        d.setdefault("region", "")
        d.setdefault("movable", False)

        d["id"] = idx
        rows.append(d)

    return rows


def run_server(host="127.0.0.1", port=7777):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    print(f"geaCal-DB listening on {host}:{port}")

    while True:
        conn, addr = s.accept()
        try:
            sql = conn.recv(4096).decode().strip()

            result = execute_sql(sql)

            response = json.dumps(result, ensure_ascii=False)

            conn.sendall(response.encode("utf-8"))
        except Exception as e:
            err = json.dumps({"error": f"Internal server error: {e}"})
            conn.sendall(err.encode("utf-8"))
        finally:
            conn.close()

