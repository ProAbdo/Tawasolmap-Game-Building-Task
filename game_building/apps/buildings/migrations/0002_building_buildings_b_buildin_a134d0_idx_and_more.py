# Generated by Django 5.2.4 on 2025-07-19 01:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='building',
            index=models.Index(fields=['building_id'], name='buildings_b_buildin_a134d0_idx'),
        ),
        migrations.AddIndex(
            model_name='building',
            index=models.Index(fields=['name'], name='buildings_b_name_7f3d06_idx'),
        ),
    ]
