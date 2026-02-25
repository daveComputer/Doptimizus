# Utilise une version légère de Python
FROM python:3.10-slim

# Définit le dossier de travail
WORKDIR /app/api

# Copie et installe les dépendances (on le fait avant pour le cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Lance l'application
CMD ["python", "app.py"]