#!/usr/bin/env bash
# Script de build pour Render

set -o errexit

# Installer les dépendances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations
python manage.py migrate

# Créer le superuser (ne fait rien s'il existe déjà)
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin123')
    print('Superuser créé avec succès')
else:
    print('Superuser existe déjà')
EOF
