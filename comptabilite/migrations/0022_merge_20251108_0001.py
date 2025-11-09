from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0020_userprofile_recipient_cache'),
        ('comptabilite', '0021_merge_20251107_0000'),
    ]

    operations = [
        # Merge migration to reconcile recipient cache addition with previous merge.
    ]
