# comptabilite/management/commands/send_daily_summary.py
import sys
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from comptabilite.models import Facturation

class Command(BaseCommand):
    help = "Envoie chaque jour à 18h la synthèse par lieu et code."

    def handle(self, *args, **options):
        # 1) Calcul de la date « veille » dans le fuseau configuré
        tz = timezone.get_current_timezone()
        today_local = timezone.now().astimezone(tz).date()
        target_date = today_local - timedelta(days=1)

        # 2) Filtrer les factures de la veille
        qs = Facturation.objects.filter(date_facture=target_date)

        # 3) Préparer le rapport :
        report = {}
        grand_total_acte = 0
        grand_total_tiers = 0

        for lieu, _ in Facturation.LIEU_CHOICES:
            sub_qs = qs.filter(lieu_acte=lieu)
            if not sub_qs.exists():
                continue

            # regrouper par code_acte
            rows = (
                sub_qs
                .values('code_acte__code_acte')
                .annotate(
                    total_acte=Sum('total_acte'),
                    total_tiers=Sum('tiers_payant')
                )
                .order_by('code_acte__code_acte')
            )

            # transformer en liste de dict plus lisibles
            report[lieu] = [
                {
                    'code': row['code_acte__code_acte'],
                    'total_acte': row['total_acte'] or 0,
                    'total_tiers': row['total_tiers'] or 0,
                }
                for row in rows
            ]

            # additionner aux totaux généraux
            grand_total_acte  += sum(r['total_acte'] for r in report[lieu])
            grand_total_tiers += sum(r['total_tiers'] for r in report[lieu])
            #grand_total_total = grand_total_acte + grand_total_tiers

        if not report:
            self.stdout.write("Aucune facture à résumer pour le " + target_date.isoformat())
            return

        # 4) Construire le contexte pour le template
        context = {
            'date': target_date,
            'report': report,
            'grand_total_acte': grand_total_acte,
            'grand_total_tiers': grand_total_tiers,
            #'grand_total_total': grand_total_total,
        }

        # 5) Rendre le corps HTML
        html_content = render_to_string('comptabilite/daily_summary_email.html', context)

        # 6) Envoyer l'email
        subject = f"Activité du {target_date:%d/%m/%Y}"
        from_email = settings.EMAIL_HOST_USER
        to = ['bronstein.tahiti@proton.me', 'marie.bronstein@gmail.com']

        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.stdout.write(self.style.SUCCESS(
            f"Synthèse envoyée pour le {target_date:%d/%m/%Y}."
        ))
