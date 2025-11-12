import json
from db import get_connection
from typing import Dict, Any, Union

def smart_parse_json(data):
    for _ in range(5):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                break
        else:
            break
    return data

def update_row(table: str, data: Union[str, Dict[str, Any]], condition: Union[str, Dict[str, Any]], db_key: str = "DB1") -> Dict[str, Any]:
    conn = cursor = None
    try:
        data = smart_parse_json(data)
        condition = smart_parse_json(condition)

        if not isinstance(data, dict) or not isinstance(condition, dict):
            return {"status": "error", "message": "Invalid MCP input — both must be JSON objects", "database": db_key}

        conn = get_connection(db_key)
        cursor = conn.cursor()

        set_clause = ", ".join([f"[{k}] = ?" for k in data.keys()])
        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(condition.values())

        cursor.execute(sql, values)
        conn.commit()

        return {"status": "success", "database": db_key, "action": "update", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "database": db_key, "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
