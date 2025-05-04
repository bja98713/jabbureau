from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from django.core.mail import send_mail
from comptabilite.models import Facturation
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = "Envoie chaque jour à 18h la synthèse Facturation par lieu et code"

    def handle(self, *args, **options):
        today = timezone.localdate()
        qs = Facturation.objects.filter(date_acte=today)

        # 1. Synthèse par lieu_acte et code_acte
        summary = (
            qs
            .values('lieu_acte', 'code_acte__code_acte')
            .annotate(montant_total=Sum('total_acte'))
            .order_by('lieu_acte', 'code_acte__code_acte')
        )

        # 2. Totaux globaux
        total_journalier = qs.aggregate(total=Sum('total_acte'))['total'] or 0

        # 3. Construire le contenu de l’email via un template
        context = {
            'date': today,
            'summary': summary,
            'total_journalier': total_journalier,
        }
        message_html = render_to_string('comptabilite/email/daily_summary.html', context)
        subject = f"Synthèse Facturation du {today:%d/%m/%Y}"
        recipient = ['docteur@bronstein.fr', 'bronstein.tahiti@proton.me']

        send_mail(
            subject,
            '',                   # plain-text fallback
            'noreply@votre-domaine.tld',
            recipient,
            html_message=message_html,
        )

        self.stdout.write(self.style.SUCCESS("E-mail de synthèse envoyé."))
