from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0020_bibliographie'),
        ('comptabilite', '0022_merge_20251108_0001'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bibliographie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200, unique=True, verbose_name='Titre')),
                ('reference', models.CharField(blank=True, max_length=255, verbose_name='Référence')),
                ('resume', models.TextField(blank=True, verbose_name='Résumé')),
                ('texte', models.TextField(blank=True, verbose_name='Texte complet')),
                ('lien', models.URLField(blank=True, verbose_name='Lien externe')),
                ('codes_cim10', models.CharField(blank=True, help_text='Séparez les codes par une virgule ou un espace.', max_length=255, verbose_name='Codes CIM-10')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Bibliographie',
                'verbose_name_plural': 'Bibliographies',
                'ordering': ['titre'],
            },
        ),
    ]
