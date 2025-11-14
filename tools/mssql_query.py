import logging
from db import get_connection
from keycloak_integration import get_connection_from_token

logger = logging.getLogger(__name__)

def run_query(query: str, params=None, access_token: str = None):
    """
    Execute a SELECT query against MSSQL.
    If access_token provided, use Keycloak-managed credentials; otherwise use default.
    """
    try:
        if access_token:
            conn = get_connection_from_token(access_token)
        else:
            conn = get_connection()
        
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Fetch column names
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        
        logger.info(f"Query executed successfully, returned {len(result)} rows")
        return {"success": True, "data": result, "row_count": len(result)}
    
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {"success": False, "error": str(e)}
