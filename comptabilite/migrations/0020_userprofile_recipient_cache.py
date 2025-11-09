from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0019_courrier'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_recipient_cache',
            field=models.TextField(blank=True, default='{}'),
        ),
    ]
