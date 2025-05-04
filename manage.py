#!/usr/bin/env python
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
import sys

def main():
    """Point d'entrée principal pour le script de gestion."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Vérifiez qu'il est installé "
            "et disponible dans votre environnement Python."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
