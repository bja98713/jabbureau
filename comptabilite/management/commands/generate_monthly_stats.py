# comptabilite/management/commands/generate_monthly_stats.py

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from comptabilite.models import Facturation, Statistique
from django.db.models import Q

class Command(BaseCommand):
    help = 'Génère et stocke la statistique du mois précédent'

    def handle(self, *args, **options):
        # 1) Calcul de la période (mois précédent)
        today = timezone.localdate()
        print(f"DEBUG: today = {today}")
        first_of_month = today.replace(day=1)
        print(f"DEBUG: first_of_month = {first_of_month}")
        prev_month_last = first_of_month - datetime.timedelta(days=1)
        year, month = prev_month_last.year, prev_month_last.month
        print(f"DEBUG: target year={year}, month={month:02d}")

        # 2) Récupération des factures du mois précédent
        qs = Facturation.objects.filter(
            date_facture__year=year,
            date_facture__month=month
        )
        print(f"DEBUG: QuerySet count = {qs.count()}")

        # 3) Vérifier les valeurs de lieu_acte / total_acte
        resumo = qs.values('lieu_acte').annotate(somme=Sum('total_acte'))
        print("DEBUG: resumo (par lieu) =", list(resumo))

        # 4) Calcul explicite des deux totaux en une passe
        stats = qs.aggregate(
            total_acte_cabinet = Sum('total_acte', filter=Q(lieu_acte__iexact='cabinet')),
            total_acte_clinique= Sum('total_acte', filter=Q(lieu_acte__iexact='clinique')),
        )
        total_cabinet  = stats['total_acte_cabinet']  or 0
        total_clinique = stats['total_acte_clinique'] or 0

        print(f"DEBUG: total_cabinet={total_cabinet}, total_clinique={total_clinique}")


        # 5) Création ou mise à jour de la Statistique
        obj, created = Statistique.objects.update_or_create(
            year=year,
            month=month,
            defaults={
                'total_acte_cabinet': total_cabinet,
                'total_acte_clinique': total_clinique,
            }
        )
        print(f"DEBUG: Statistique object {'created' if created else 'updated'}: {obj}")

        # 6) Message final
        verb = 'Créée' if created else 'Mise à jour'
        final_msg = (
            f"{verb} statistique pour {month:02d}/{year}: "
            f"cabinet={total_cabinet}, clinique={total_clinique}"
        )
        print(f"DEBUG: final message = {final_msg}")
        self.stdout.write(self.style.SUCCESS(final_msg))
