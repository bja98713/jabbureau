from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0020_alter_courrier_type_courrier_biopsyreminder'),
        ('comptabilite', '0020_courrierphoto'),
    ]

    operations = [
        # This is a merge migration to reconcile two 0020 branches.
    ]
