# comptabilite/management/commands/send_biopsy_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone

from comptabilite.models import BiopsyReminder
from comptabilite.utils import build_email, safe_send


class Command(BaseCommand):
    help = "Envoie les rappels d'anapath à récupérer pour les biopsies FOGD/COLO arrivées à échéance."

    def handle(self, *args, **options):
        today = timezone.localdate()
        due = BiopsyReminder.objects.filter(sent=False, send_on__lte=today)
        if not due.exists():
            self.stdout.write("Aucun rappel anapath à envoyer aujourd'hui.")
            return

        sent_count = 0
        errors = 0
        for r in due.order_by('send_on'):
            try:
                dest_label = r.destination_label()
                dna_str = r.date_naissance.strftime('%d/%m/%Y') if r.date_naissance else 'XX/XX/XXXX'
                subject = (
                    f"Ana-Path à recuperer de {r.nom} {r.prenom} {dna_str} envoyée à \"{dest_label}\""
                )
                body = (
                    "<p>Tania,</p>"
                    f"<p>Il ne faut pas oublier de recuperer l'anap-path de "
                    f"<strong>{r.nom} {r.prenom} {dna_str}</strong>, "
                    f"N°DN <strong>{r.dn}</strong>, envoyee a ({dest_label}).</p>"
                    "<p><strong>Acces service d'anapath :</strong><br>"
                    "<a href=\"https://cyberlab.icpf.pf/cyberlab/Login.jsp\" target=\"_blank\">"
                    "https://cyberlab.icpf.pf/cyberlab/Login.jsp</a><br>"
                    "Login : <strong>M3089</strong><br>"
                    "Mot de passe : <strong>Papeete98713</strong></p>"
                )

                email = build_email(
                    subject=subject,
                    body=body,
                    to=['secretariat@bronstein.fr'],
                    cc=['docteur@bronstein.fr'],
                )
                email.content_subtype = 'html'
                safe_send(email)

                r.sent = True
                r.sent_at = timezone.now()
                r.save(update_fields=['sent', 'sent_at'])
                sent_count += 1
                self.stdout.write(f"  ✓ Rappel envoyé : {r.nom} {r.prenom} ({r.dn})")
            except Exception as e:
                errors += 1
                self.stderr.write(f"  ✗ Erreur pour {r.dn} – {r.nom} {r.prenom} : {e}")
                continue

        self.stdout.write(self.style.SUCCESS(
            f"{sent_count} rappel(s) anapath envoyé(s)."
            + (f" {errors} erreur(s)." if errors else "")
        ))
