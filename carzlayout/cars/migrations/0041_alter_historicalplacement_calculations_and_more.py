# Generated by Django 5.0.1 on 2024-04-01 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0040_historicalplacement_calculations_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalplacement',
            name='calculations',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='historicalplacement',
            name='nspis',
            field=models.FloatField(default=1.0, verbose_name='Принятое списочное кол-во машин'),
        ),
        migrations.AlterField(
            model_name='placement',
            name='calculations',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='placement',
            name='nspis',
            field=models.FloatField(default=1.0, verbose_name='Принятое списочное кол-во машин'),
        ),
    ]
