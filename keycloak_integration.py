import requests
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KEYCLOAK_URL = "http://localhost:8080"
REALM = "mssql-mcp"
CLIENT_ID = "mssql-mcp-server"
CLIENT_SECRET = "1YUnRP9jClXLOAsmsHU7bktN8fCVCeZE"

# Admin
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASS = "admin"
KEYCLOAK_ADMIN_CLIENT = "admin-cli"


# ------------------ USER TOKEN -------------------------
def get_token(username, password):
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    logger.info("🟩 Access token obtained")
    return resp.json()


# ------------------ JWT VERIFY -------------------------
def verify_token(token: str):
    jwks_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    decoded = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=CLIENT_ID
    )
    logger.info("🟩 JWT verified")
    return decoded


# ------------------ ADMIN TOKEN ------------------------
def get_admin_token() -> str:
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": KEYCLOAK_ADMIN_CLIENT,
        "username": KEYCLOAK_ADMIN_USER,
        "password": KEYCLOAK_ADMIN_PASS
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


# ------------------ USER DB ATTRIBUTES -----------------------
def get_user_db_attrs(username: str):
    token = get_admin_token()

    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users?username={username}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()

    users = resp.json()
    if not users:
        raise Exception(f"No user: {username}")

    user_id = users[0]["id"]

    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()

    udata = resp.json()
    attrs = udata.get("attributes", {}) or {}

    # Required
    needed = ["db_user", "db_password", "db_server", "db_port", "db_driver"]
    for key in needed:
        if key not in attrs:
            raise Exception(f"User missing attribute: {key}")

    fixed = {}
    for key in needed:
        val = attrs[key]
        fixed[key] = val[0] if isinstance(val, list) else val

    # Optional DB name
    for alt in ["db_database", "database", "db_name", "preferred_db"]:
        if alt in attrs:
            v = attrs[alt]
            fixed["db_database"] = v[0] if isinstance(v, list) else v
            break

    return fixed