from db import get_connection
from typing import Dict, Any

def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Fetch schema information for a specific table."""
    conn = cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(sql, table_name)
        cols = [c[0] for c in cursor.description] if cursor.description else []
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return {"status": "success", "table": table_name, "columns": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
