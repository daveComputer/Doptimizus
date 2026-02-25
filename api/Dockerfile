# Utilise une version légère de Python
FROM python:3.10-slim

# Définit le dossier de travail
WORKDIR /app/api

# Copie et installe les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On ne copie pas tout le code ici car on utilise un "volume" 
# dans le docker-compose pour le développement en temps réel

# Lance l'application
CMD ["python", "app.py"]