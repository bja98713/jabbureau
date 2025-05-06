from django.core.management.base import BaseCommand
from django.template.loader       import render_to_string
from django.core.mail             import send_mail
from django.utils                  import timezone
from datetime                     import timedelta
import pytz

from comptabilite.models import Facturation

class Command(BaseCommand):
    help = "Envoie la synthèse journalière"

    def handle(self, *args, **opts):
        # 1) on choisit la TZ de Tahiti
        tz_tahiti = pytz.timezone('Pacific/Tahiti')
        now_tahiti = timezone.now().astimezone(tz_tahiti)

        # 2) date à résumer = date locale (le cron étant lancé à 18h00)
        target_date = now_tahiti.date()

        # 3) requête des factures du target_date
        factures = Facturation.objects.filter(date_acte=target_date)
        if not factures.exists():
            self.stdout.write(f"Aucune facture à résumer pour le {target_date}")
            return

        # 4) agrégations cabinet / clinique / total
        from django.db.models import Sum
        synthese = (factures
                    .values('lieu_acte','code_acte__code_acte')
                    .annotate(total_acte=Sum('total_acte'),
                              total_tiers=Sum('tiers_payant'))
                    .order_by('lieu_acte','code_acte__code_acte'))

        grand_total = factures.aggregate(
            grand_total_acte=Sum('total_acte'),
            grand_total_tiers=Sum('tiers_payant')
        )

        # 5) rendu du mail
        context = {
            'target_date': target_date,
            'synthese':    synthese,
            'grand_total': grand_total,
        }
        subject = f"Synthèse du {target_date} (cabinet/clinique)"
        html    = render_to_string('comptabilite/daily_summary_email.html', context)
        send_mail(subject,
                  '',  # plain-text fallback
                  'ja.bronstein@gmail.com',
                  ['bronstein.tahiti@proton.me'],
                  html_message=html
        )
        self.stdout.write(f"Mail envoyé pour le {target_date}")
