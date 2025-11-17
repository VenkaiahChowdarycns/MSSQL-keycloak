import logging
from typing import Any, List, Optional, Dict

logger = logging.getLogger(__name__)

def run_query(query: str, params: Optional[List[Any]] = None, db_name: str = "default") -> Dict[str, Any]:
    """
    Execute a SELECT or arbitrary query against the connection for db_name.
    """
    from server import get_conn

    conn = None
    cur = None
    try:
        conn = get_conn(db_name)
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if cur.description:
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            data = [dict(zip(cols, row)) for row in rows]
            return {"status": "success", "row_count": len(data), "data": data}
        else:
            return {"status": "success", "message": "Command executed"}
    except Exception as e:
        logger.exception("Query execution failed")
        return {"status": "error", "reason": str(e)}
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
