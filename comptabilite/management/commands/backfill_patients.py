from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from comptabilite.models import Facturation, Observation, Patient


class Command(BaseCommand):
    help = (
        "Backfill the Patient table from historical Facturation and Observation data.\n"
        "For each DN, prefer the latest Facturation (by date_acte) for nom/prenom/date_naissance,\n"
        "fallback to the latest Observation (by date_observation)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', help='Do not write to database, only print what would change.'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # 1) Collect DNs from both sources
        dns_fact = set(Facturation.objects.values_list('dn', flat=True).distinct())
        dns_obs = set(Observation.objects.values_list('dn', flat=True).distinct())
        dns_all = sorted(dns_fact | dns_obs)

        created = 0
        updated = 0
        skipped = 0

        self.stdout.write(self.style.HTTP_INFO(f"Found {len(dns_all)} distinct DN(s) across history."))

        with transaction.atomic():
            for dn in dns_all:
                if not dn:
                    skipped += 1
                    continue

                # Prefer data from latest Facturation
                fact = (
                    Facturation.objects
                    .filter(dn=dn)
                    .order_by('-date_acte', '-id')
                    .values('nom', 'prenom', 'date_naissance')
                    .first()
                )
                if fact:
                    nom = fact['nom'] or ''
                    prenom = fact['prenom'] or ''
                    date_naissance = fact['date_naissance']
                else:
                    obs = (
                        Observation.objects
                        .filter(dn=dn)
                        .order_by('-date_observation', '-created_at')
                        .values('nom', 'prenom', 'date_naissance')
                        .first()
                    )
                    if not obs:
                        skipped += 1
                        continue
                    nom = obs['nom'] or ''
                    prenom = obs['prenom'] or ''
                    date_naissance = obs['date_naissance']

                try:
                    patient = Patient.objects.get(dn=dn)
                    # Determine if updates are needed
                    fields_to_update = []
                    if patient.nom != nom:
                        patient.nom = nom
                        fields_to_update.append('nom')
                    if patient.prenom != prenom:
                        patient.prenom = prenom
                        fields_to_update.append('prenom')
                    # date can be None; update if different
                    if patient.date_naissance != date_naissance:
                        patient.date_naissance = date_naissance
                        fields_to_update.append('date_naissance')

                    if fields_to_update:
                        if dry_run:
                            self.stdout.write(f"[DRY] Update {dn}: {fields_to_update}")
                        else:
                            patient.save(update_fields=fields_to_update + ['updated_at'])
                        updated += 1
                except Patient.DoesNotExist:
                    if dry_run:
                        self.stdout.write(f"[DRY] Create {dn}: {nom} {prenom} {date_naissance}")
                    else:
                        Patient.objects.create(
                            dn=dn,
                            nom=nom,
                            prenom=prenom,
                            date_naissance=date_naissance,
                        )
                    created += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"Backfill complete. Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))
