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

def delete_row(table: str, condition: Union[str, Dict[str, Any]], db_key: str = "DB1") -> Dict[str, Any]:
    conn = cursor = None
    try:
        condition = smart_parse_json(condition)
        if not isinstance(condition, dict) or not condition:
            return {"status": "error", "message": "'condition' must be a JSON object", "database": db_key}

        conn = get_connection(db_key)
        cursor = conn.cursor()

        where_clause = " AND ".join([f"[{k}] = ?" for k in condition.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        values = list(condition.values())

        cursor.execute(sql, values)
        conn.commit()

        return {"status": "success", "database": db_key, "action": "delete", "table": table, "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "database": db_key, "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
