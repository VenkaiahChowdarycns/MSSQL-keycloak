import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_table_schema(table_name: str, db_name: str = "default") -> Dict[str, Any]:
    """
    Get schema information for a table in the selected database.
    """
    from server import get_conn

    conn = None
    cur = None
    try:
        conn = get_conn(db_name)
        query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        cur = conn.cursor()
        cur.execute(query, (table_name,))
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        schema = [dict(zip(cols, row)) for row in rows]
        return {"status": "success", "table": table_name, "schema": schema}
    except Exception as e:
        logger.exception("Schema retrieval failed")
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
