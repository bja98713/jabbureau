from django.db import migrations, models


def populate_activite_facturation(apps, schema_editor):
    Facturation = apps.get_model('comptabilite', 'Facturation')
    ActiviteFacturation = apps.get_model('comptabilite', 'ActiviteFacturation')

    rows = []
    for row in (
        Facturation.objects
        .values('date_acte', 'total_acte')
        .order_by('date_acte')
    ):
        if not row['date_acte']:
            continue
        rows.append(ActiviteFacturation(
            date_acte=row['date_acte'],
            total_acte=row['total_acte'] or 0,
        ))

    if rows:
        ActiviteFacturation.objects.bulk_create(rows)


def clear_activite_facturation(apps, schema_editor):
    ActiviteFacturation = apps.get_model('comptabilite', 'ActiviteFacturation')
    ActiviteFacturation.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0024_correspondantemail'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiviteFacturation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_acte', models.DateField(verbose_name="Date de l'acte")),
                ('total_acte', models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='Montant total facturé')),
            ],
            options={
                'verbose_name': 'Activité facturation',
                'verbose_name_plural': 'Activités facturation',
                'ordering': ['date_acte'],
                'indexes': [models.Index(fields=['date_acte'], name='comptabilit_date_ac_2560b6_idx')],
            },
        ),
        migrations.RunPython(populate_activite_facturation, clear_activite_facturation),
    ]
