import os
import sys
import logging
from dotenv import load_dotenv
from keycloak import KeycloakOpenID

# Load environment variables from .env FIRST
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_keycloak_connectivity():
    """
    Verify that Keycloak server is reachable and properly configured.
    Returns: (success: bool, message: str)
    """
    keycloak_url = os.getenv("KEYCLOAK_URL", "http://host.docker.internal:8080")
    realm = os.getenv("KEYCLOAK_REALM", "mssql-mcp")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID", "mssql-mcp-server")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")

    logger.info("🔍 Checking Keycloak connectivity...")
    logger.info(f"   URL: {keycloak_url}")
    logger.info(f"   Realm: {realm}")
    logger.info(f"   Client ID: {client_id}")
    logger.info(f"   Client Secret: {'***' if client_secret else 'NOT SET'}")

    if not client_secret:
        logger.error("❌ KEYCLOAK_CLIENT_SECRET not set in .env")
        return False, "Missing KEYCLOAK_CLIENT_SECRET"

    try:
        keycloak_openid = KeycloakOpenID(
            server_url=keycloak_url,
            client_id=client_id,
            realm_name=realm,
            client_secret_key=client_secret,
        )
        
        # Test by fetching the public key (lightweight check)
        public_key = keycloak_openid.public_key()
        if public_key:
            logger.info("✅ Successfully connected to Keycloak")
            logger.info(f"✅ Realm '{realm}' is accessible")
            logger.info(f"✅ Client '{client_id}' is configured")
            return True, "Keycloak connectivity verified"
        else:
            logger.error("❌ Failed to retrieve Keycloak public key")
            return False, "Public key retrieval failed"

    except Exception as e:
        logger.error(f"❌ Keycloak connection failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, message = check_keycloak_connectivity()
    print(f"\n{'='*70}")
    print(f"Keycloak Health Check: {'PASS ✅' if success else 'FAIL ❌'}")
    print(f"Message: {message}")
    print(f"{'='*70}\n")
    sys.exit(0 if success else 1)
