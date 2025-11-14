import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MSSQLConfigMapper:
    """
    Maps Keycloak user info to MSSQL connection configurations.
    Reads from .env to build available database configurations.
    """
    
    def __init__(self):
        """Initialize available MSSQL database configurations from environment."""
        self.db_configs = self._load_db_configs()
    
    def _load_db_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all MSSQL database configurations from .env.
        Supports DB1, DB2, DB3, etc.
        """
        configs = {}
        
        # Base server config (shared by all DBs)
        server = os.getenv("MSSQL_SERVER", "host.docker.internal")
        port = os.getenv("MSSQL_PORT", "1433")
        driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
        encrypt = os.getenv("MSSQL_ENCRYPT", "yes")
        trusted = os.getenv("MSSQL_TRUSTED_CONNECTION", "no").lower() in ("1", "true", "yes")
        
        # Check for DB1, DB2, DB3... up to DB10
        for i in range(1, 11):
            db_key = f"DB{i}"
            prefix = f"MSSQL_{db_key.upper()}_"
            
            db_name = os.getenv(prefix + "NAME")
            db_user = os.getenv(prefix + "USER")
            db_password = os.getenv(prefix + "PASSWORD")
            
            if db_name and db_user and db_password:
                configs[db_key] = {
                    "server": server,
                    "port": port,
                    "database": db_name,
                    "user": db_user,
                    "password": db_password,
                    "driver": driver,
                    "encrypt": encrypt,
                    "trusted": trusted,
                }
                logger.info(f"Loaded MSSQL config for {db_key}: {db_name}")
        
        if not configs:
            logger.warning("No MSSQL database configurations found in .env")
        
        return configs
    
    def get_db_key_for_user(self, keycloak_user_info: dict) -> Optional[str]:
        """
        Map a Keycloak user to a specific MSSQL database key.
        Priority:
        1. Check 'db_key' attribute in Keycloak user
        2. Check 'db_user' attribute and match to configured DB
        3. Default to DB1
        """
        if not keycloak_user_info:
            return "DB1"
        
        # Direct db_key attribute
        db_key = keycloak_user_info.get("db_key")
        if db_key and db_key in self.db_configs:
            logger.info(f"Mapped user to {db_key} via db_key attribute")
            return db_key
        
        # Match db_user to configured users
        db_user = keycloak_user_info.get("db_user")
        if db_user:
            for key, config in self.db_configs.items():
                if config.get("user") == db_user:
                    logger.info(f"Mapped user to {key} via db_user match")
                    return key
        
        # Default fallback
        logger.info("No specific DB mapping found, using DB1 as default")
        return "DB1"
    
    def get_config_for_user(self, keycloak_user_info: dict) -> Dict[str, Any]:
        """
        Get MSSQL configuration for a Keycloak user.
        Returns the database config mapped to this user.
        """
        db_key = self.get_db_key_for_user(keycloak_user_info)
        
        if db_key not in self.db_configs:
            logger.error(f"Database {db_key} not configured")
            raise ValueError(f"Database {db_key} not found in configuration")
        
        return self.db_configs[db_key]
    
    def list_available_databases(self) -> Dict[str, str]:
        """List all configured databases."""
        return {k: v.get("database") for k, v in self.db_configs.items()}


# Global mapper instance
config_mapper = MSSQLConfigMapper()

def get_mapper() -> MSSQLConfigMapper:
    """Get the global config mapper instance."""
    return config_mapper
