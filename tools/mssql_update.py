import json
import logging
from typing import Dict, Any, Union

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
    db_name: str = "default",
) -> Dict[str, Any]:
    """
    Update row(s) in the specified database and table.
    """
    from server import get_conn

    db_conn = cursor = None
    try:
        data = smart_parse_json(data)
        condition = smart_parse_json(condition)

        if not isinstance(data, dict) or not isinstance(condition, dict):
            return {"status": "error", "message": "Invalid MCP input — both must be JSON objects"}

        db_conn = get_conn(db_name)
        cursor = db_conn.cursor()

        set_clause = ", ".join([f"[{k}] = ?" for k in data.keys()])
        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(condition.values())

        cursor.execute(sql, values)
        db_conn.commit()

        return {"status": "success", "action": "update", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        logger.exception("Update failed")
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
        except:
            pass
        try:
            if db_conn:
                db_conn.close()
        except:
            pass
