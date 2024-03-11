# Generated by Django 5.0.1 on 2024-03-11 11:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0033_historicalplacement_placement_placementcar_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalplacement',
            name='period',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='cars.yearmonth', verbose_name='Период'),
        ),
        migrations.AddField(
            model_name='placement',
            name='period',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='cars.yearmonth', verbose_name='Период'),
            preserve_default=False,
        ),
    ]