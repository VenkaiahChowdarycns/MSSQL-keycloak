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

def update_row(table: str, data: Union[str, Dict[str, Any]], condition: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Updates row(s) in a table based on a condition.
    Accepts both JSON string and dict for MCP compatibility.
    """
def update_row(table: str, data: Union[str, Dict[str, Any]], condition: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    
    conn = cursor = None
    try:
        data = smart_parse_json(data)
        condition = smart_parse_json(condition)

        if not isinstance(data, dict) or not isinstance(condition, dict):
            return {"status": "error", "message": "Invalid MCP input — 'data' and 'condition' must be JSON objects"}

        conn = get_connection()
        cursor = conn.cursor()

        set_clause = ", ".join([f"[{k}] = ?" for k in data.keys()])
        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        values = list(data.values()) + list(condition.values())

        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        

        cursor.execute(sql, values)
        conn.commit()
        return {"status": "success", "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass