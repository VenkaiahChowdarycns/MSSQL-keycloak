import json
import logging
from typing import Dict, Any

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

def insert_row(
    table: str,
    data: Dict[str, Any],
    db_name: str = "default",
) -> Dict[str, Any]:
    """
    Insert a row into the given table on the specified database (db_name).
    """
    from server import get_conn

    conn = None
    cur = None
    try:
        conn = get_conn(db_name)
        columns = ", ".join([f"[{k}]" for k in data.keys()])
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cur = conn.cursor()
        cur.execute(sql, tuple(data.values()))
        conn.commit()
        return {"status": "success", "message": f"Inserted into {table}", "rows_affected": cur.rowcount}
    except Exception as e:
        logger.exception("Insert failed")
        return {"status": "error", "reason": str(e)}
    finally:
        try:
            if cur:
                cur.close()
        except:
            pass
        try:
            if conn:
                conn.close()
        except:
            pass
