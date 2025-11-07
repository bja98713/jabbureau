from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('comptabilite', '0019_courrier'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourrierPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='courrier_photos/%Y/%m/%d')),
                ('position', models.PositiveSmallIntegerField(default=1, help_text="Ordre d'affichage (1-4)")),
                ('legend', models.CharField(blank=True, max_length=120)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('courrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='comptabilite.courrier')),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='courrierphoto',
            constraint=models.UniqueConstraint(fields=('courrier', 'position'), name='uniq_photo_position_par_courrier'),
        ),
    ]
