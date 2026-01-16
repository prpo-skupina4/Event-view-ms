FROM python:3.11-slim

# manjši image + stabilno logiranje
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# driver za bazo
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg2 ca-certificates apt-transport-https \
    unixodbc unixodbc-dev \
 && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*



# najprej dependency-ji (boljši caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# šele nato koda
COPY . .

# port, ki ga bo poslušal uvicorn v containerju
EXPOSE 8000

# zagon
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
