import json
from db import get_connection
from typing import Dict, Any, Union

def smart_parse_json(data):
    """Aggressively decode escaped JSON up to 5 levels deep."""
    for _ in range(5):
        if isinstance(data, str):
            data = data.strip()
            if (data.startswith('"') and data.endswith('"')) or (data.startswith("'") and data.endswith("'")):
                data = data[1:-1]
            data = data.replace('\\"', '"').replace("\\'", "'")
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                continue
        else:
            break
    return data

def delete_row(table: str, condition: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Deletes row(s) from a table based on a condition."""
    conn = cursor = None
    try:
        condition = smart_parse_json(condition)

        if not isinstance(condition, dict) or not condition:
            return {"status": "error", "message": "Invalid MCP input — 'condition' must be a JSON object"}

        conn = get_connection()
        cursor = conn.cursor()

        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        values = list(condition.values())

        cursor.execute(sql, values)
        conn.commit()

        return {"status": "success", "action": "delete", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
