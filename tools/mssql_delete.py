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

def delete_row(
    table: str,
    condition: Union[str, Dict[str, Any]],
    db_name: str = "default",
) -> Dict[str, Any]:
    """
    Delete row(s) from the specified table in the chosen database.
    """
    from server import get_conn

    db_conn = cursor = None
    try:
        condition = smart_parse_json(condition)
        if not isinstance(condition, dict) or not condition:
            return {"status": "error", "message": "'condition' must be a JSON object"}

        db_conn = get_conn(db_name)
        cursor = db_conn.cursor()

        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        values = list(condition.values())

        cursor.execute(sql, values)
        db_conn.commit()

        return {"status": "success", "action": "delete", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        logger.exception("Delete failed")
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
