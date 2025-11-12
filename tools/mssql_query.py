from db import get_connection
from typing import Any, Dict, List, Optional

def run_query(query: str, params: Optional[List[Any]] = None, db_key: str = "DB1") -> Dict[str, Any]:
    conn = cursor = None
    try:
        conn = get_connection(db_key)
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if cursor.description:
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            return {"status": "success", "database": db_key, "type": "query", "rows": rows, "count": len(rows)}
        else:
            conn.commit()
            return {"status": "success", "database": db_key, "type": "non_query", "rows_affected": cursor.rowcount}

    except Exception as e:
        return {"status": "error", "database": db_key, "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
