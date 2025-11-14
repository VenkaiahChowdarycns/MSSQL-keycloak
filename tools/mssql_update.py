import json
import logging
from db import get_connection
from keycloak_integration import get_connection_from_token
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

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

def update_row(
    table: str,
    data: Union[str, Dict[str, Any]],
    condition: Union[str, Dict[str, Any]],
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    conn = cursor = None
    try:
        data = smart_parse_json(data)
        condition = smart_parse_json(condition)

        if not isinstance(data, dict) or not isinstance(condition, dict):
            return {"status": "error", "message": "Invalid MCP input — both must be JSON objects", "database": "DB1"}

        if access_token:
            conn = get_connection_from_token(access_token, "DB1")
        else:
            conn = get_connection("DB1")
        cursor = conn.cursor()

        set_clause = ", ".join([f"[{k}] = ?" for k in data.keys()])
        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(condition.values())

        cursor.execute(sql, values)
        conn.commit()

        return {"status": "success", "database": "DB1", "action": "update", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "database": "DB1", "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
