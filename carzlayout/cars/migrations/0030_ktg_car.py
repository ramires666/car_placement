# Generated by Django 5.0.1 on 2024-02-28 18:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0029_ktg'),
    ]

    operations = [
        migrations.AddField(
            model_name='ktg',
            name='car',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='cars.car', verbose_name='Машина'),
            preserve_default=False,
        ),
    ]