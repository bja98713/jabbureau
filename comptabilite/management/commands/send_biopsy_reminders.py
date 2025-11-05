# comptabilite/management/commands/send_biopsy_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage

from comptabilite.models import BiopsyReminder

class Command(BaseCommand):
    help = "Envoie les rappels d'anapath à récupérer pour les biopsies FOGD/COLO arrivées à échéance."

    def handle(self, *args, **options):
        today = timezone.localdate()
        due = BiopsyReminder.objects.filter(sent=False, send_on__lte=today)
        if not due.exists():
            self.stdout.write("Aucun rappel anapath à envoyer aujourd'hui.")
            return

        sent_count = 0
        for r in due.order_by('send_on'):
            try:
                # Construire sujet et corps selon le cahier des charges
                dest_label = r.destination_label()
                dna_str = r.date_naissance.strftime('%d/%m/%Y') if r.date_naissance else 'XX/XX/XXXX'
                subject = (
                    f"Ana-Path à recuperer de {r.nom} {r.prenom} {dna_str} envoyée à \"{dest_label}\""
                )
                body = (
                    "Tania,\n\n"
                    f"Il ne faut pas oublier de récuperer l'anap-path de {r.nom} {r.prenom} {dna_str}, N°DN {r.dn}, envoyée à ({dest_label}).\n"
                )
                to = ['secretariat@bronstein.fr']
                cc = ['docteur@bronstein.fr']

                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=to,
                    cc=cc,
                )
                email.send(fail_silently=False)

                r.sent = True
                r.sent_at = timezone.now()
                r.save(update_fields=['sent', 'sent_at'])
                sent_count += 1
            except Exception as e:
                self.stderr.write(f"Erreur envoi rappel pour {r.dn} – {r.nom} {r.prenom}: {e}")
                continue

        self.stdout.write(self.style.SUCCESS(f"{sent_count} rappel(s) anapath envoyé(s)."))
