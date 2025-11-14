import logging
from db import get_connection
from keycloak_integration import get_connection_from_token

logger = logging.getLogger(__name__)

def get_table_schema(table_name: str, access_token: str = None):
    """
    Get schema information for an MSSQL table.
    If access_token provided, use Keycloak-managed credentials; otherwise use default.
    """
    try:
        if access_token:
            conn = get_connection_from_token(access_token)
        else:
            conn = get_connection()
        
        query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (table_name,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        schema = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        
        logger.info(f"Schema retrieved for table {table_name}")
        return {"success": True, "table": table_name, "schema": schema}
    
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        return {"success": False, "error": str(e)}
