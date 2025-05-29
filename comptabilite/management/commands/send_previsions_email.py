from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.timezone import localdate, timedelta
from django.conf import settings


from comptabilite.models import PrevisionHospitalisation

class Command(BaseCommand):
    help = "Envoie les prévisions d'hospitalisation pour le lendemain par email"

    def handle(self, *args, **options):
        next_day = localdate() + timedelta(days=1)
        previsions = PrevisionHospitalisation.objects.filter(date_entree=next_day).order_by('-date_entree')

        html_content = render_to_string("comptabilite/email/previsions_email.html", {
            "date": next_day.strftime("%d/%m/%Y"),
            "previsions": previsions
        })

        subject = f"Programme du {next_day.strftime('%d/%m/%Y')}"
        email = EmailMessage(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            ["bronstein.tahiti@proton.me", "secretariat@bronstein.fr"]
        )
        email.content_subtype = "html"

        email.send()

        self.stdout.write(
            self.style.SUCCESS(f"Email envoyé avec {previsions.count()} prévision(s) pour le {next_day}.")
        )
