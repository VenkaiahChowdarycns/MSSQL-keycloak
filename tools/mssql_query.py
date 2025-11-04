from db import get_connection
from typing import Any, Dict, List, Optional
import json

def run_query(query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
    conn = cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if cursor.description:  # SELECT
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            return {"status": "success", "rows": rows, "count": len(rows)}
        else:
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
