# Utiliser une image Python slim basée sur Debian
FROM python:3.12-slim

# Mettre à jour apt-get et installer les dépendances système pour WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt et installer les dépendances Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier le reste du code de l'application
COPY . /app/

# Exposer le port 8000
EXPOSE 8000

# Démarrer le serveur avec gunicorn (ou utilisez manage.py runserver pour le développement)
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
