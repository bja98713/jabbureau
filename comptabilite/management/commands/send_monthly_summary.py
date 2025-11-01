from datetime import date
from calendar import monthrange
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from comptabilite.models import Facturation


class Command(BaseCommand):
    help = "Envoie la synthèse mensuelle (mois en cours) par lieu et code."

    def handle(self, *args, **options):
        today_local = timezone.localdate()
        first_day = today_local.replace(day=1)
        last_day = date(today_local.year, today_local.month, monthrange(today_local.year, today_local.month)[1])

        qs = Facturation.objects.filter(date_facture__range=(first_day, last_day))

        report = {}
        grand_total_acte = 0
        grand_total_tiers = 0

        for lieu, _ in Facturation.LIEU_CHOICES:
            sub_qs = qs.filter(lieu_acte=lieu)
            if not sub_qs.exists():
                continue

            rows = (
                sub_qs
                .values('code_acte__code_acte')
                .annotate(
                    total_acte=Sum('total_acte'),
                    total_tiers=Sum('tiers_payant')
                )
                .order_by('code_acte__code_acte')
            )

            report[lieu] = [
                {
                    'code': row['code_acte__code_acte'],
                    'total_acte': row['total_acte'] or 0,
                    'total_tiers': row['total_tiers'] or 0,
                }
                for row in rows
            ]

            grand_total_acte += sum(r['total_acte'] for r in report[lieu])
            grand_total_tiers += sum(r['total_tiers'] for r in report[lieu])

        if not report:
            self.stdout.write(f"Aucune facture à résumer pour le mois en cours ({today_local:%m/%Y}).")
            return

        context = {
            'start_date': first_day,
            'end_date': last_day,
            'report': report,
            'grand_total_acte': grand_total_acte,
            'grand_total_tiers': grand_total_tiers,
        }

        html_content = render_to_string('comptabilite/monthly_summary_email.html', context)

        subject = f"Activité – Mois du {first_day.strftime('%d/%m/%Y')} au {last_day.strftime('%d/%m/%Y')}"
        from_email = settings.EMAIL_HOST_USER
        to = ['bronstein.tahiti@proton.me', 'marie.bronstein@gmail.com']

        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.stdout.write(self.style.SUCCESS(
            f"Synthèse mensuelle envoyée (du {first_day:%d/%m/%Y} au {last_day:%d/%m/%Y})."
        ))
