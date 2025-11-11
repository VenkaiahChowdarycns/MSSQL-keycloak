# Dockerfile
FROM python:3.12-slim

LABEL maintainer="you@example.com"

# Avoid .pyc files & buffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install ODBC Driver 18 + tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl gnupg apt-transport-https ca-certificates \
        unixodbc-dev netcat-openbsd && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg && \
    curl -sSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Verify driver
RUN odbcinst -q -d | grep "ODBC Driver 18 for SQL Server" || exit 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose nothing – we use STDIO
# Healthcheck via simple Python call
HEALTHCHECK --interval=5s --timeout=3s --retries=3 \
    CMD python -c "from db import get_connection; get_connection().close()" || exit 1

CMD ["python", "server.py"]