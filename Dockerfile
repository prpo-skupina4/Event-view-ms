FROM python:3.11-slim

# manjši image + stabilno logiranje
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (opcijsko) sistemske odvisnosti; za sqlite navadno ni treba nič posebnega
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# najprej dependency-ji (boljši caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# šele nato koda
COPY . .

# port, ki ga bo poslušal uvicorn v containerju
EXPOSE 8000

# zagon
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
