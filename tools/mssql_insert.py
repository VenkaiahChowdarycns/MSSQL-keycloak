import json
from db import get_connection
from typing import Dict, Any, Union

def smart_parse_json(data):
    """Try to decode JSON up to 5 levels deep (handles MCP escaping)."""
    for _ in range(5):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                break
        else:
            break
    return data

def insert_row(table: str, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    conn = cursor = None
    try:
        data = smart_parse_json(data)

        if not isinstance(data, dict) or not data:
            return {"status": "error", "message": "'data' must be a non-empty JSON object"}

        conn = get_connection()
        cursor = conn.cursor()

        cols = ", ".join([f"[{c}]" for c in data.keys()])
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())

        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        conn.commit()

        return {"status": "success", "action": "insert", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
