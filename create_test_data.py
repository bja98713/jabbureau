#!/usr/bin/env python
"""
Script pour créer des données de test pour l'export Excel
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from comptabilite.models import Facturation, Code, Medecin

def create_test_data():
    """Créer des données de test"""
    
    # Créer un médecin de test
    medecin, _ = Medecin.objects.get_or_create(
        nom_medecin="Dr. Test",
        code_m="TEST001",
        nom_clinique="Clinique Test"
    )
    
    # Créer quelques codes d'actes
    codes = []
    for i, (code_acte, total) in enumerate([
        ("COAG001", 5000),
        ("COAG002", 7500), 
        ("COAG003", 3000),
    ], 1):
        code, _ = Code.objects.get_or_create(
            code_acte=code_acte,
            defaults={
                'total_acte': Decimal(str(total)),
                'tiers_payant': Decimal(str(total // 2)),
                'total_paye': Decimal(str(total)),
                'medecin': medecin
            }
        )
        codes.append(code)
    
    # Créer quelques facturations de test
    facturations_data = [
        {
            'dn': '1234567',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'date_naissance': date(1980, 5, 15),
            'date_acte': date.today() - timedelta(days=2),
            'date_facture': date.today() - timedelta(days=1),
            'regime': 'Sécurité Sociale',
            'lieu_acte': 'Cabinet',
            'code_acte': codes[0],
            'total_acte': Decimal('5000')
        },
        {
            'dn': '2345678',
            'nom': 'Martin',
            'prenom': 'Marie',
            'date_naissance': date(1975, 8, 22),
            'date_acte': date.today() - timedelta(days=1),
            'date_facture': date.today(),
            'regime': 'RNS',
            'lieu_acte': 'Clinique',
            'code_acte': codes[1],
            'total_acte': Decimal('7500')
        },
        {
            'dn': '3456789',
            'nom': 'Durand',
            'prenom': 'Pierre',
            'date_naissance': date(1990, 12, 10),
            'date_acte': date.today(),
            'date_facture': date.today(),
            'regime': 'Salarié',
            'lieu_acte': 'Cabinet',
            'code_acte': codes[2],
            'total_acte': Decimal('3000')
        }
    ]
    
    created_count = 0
    for data in facturations_data:
        facturation, created = Facturation.objects.get_or_create(
            dn=data['dn'],
            defaults=data
        )
        if created:
            created_count += 1
    
    return created_count

if __name__ == '__main__':
    try:
        count = create_test_data()
        print(f"✅ {count} nouvelles facturations créées avec succès!")
        
        # Afficher le total des facturations
        total_facturations = Facturation.objects.count()
        print(f"📊 Total des facturations en base : {total_facturations}")
        
        if total_facturations > 0:
            print("\n📋 Exemples de données créées :")
            for f in Facturation.objects.all()[:3]:
                print(f"  - {f.date_acte}: {f.nom} {f.prenom} - {f.total_acte} XPF - {f.lieu_acte}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données : {e}")
        sys.exit(1)