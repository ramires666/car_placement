# Generated by Django 5.0.1 on 2024-02-28 18:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0028_remove_car_ktg_remove_historicalcar_ktg'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ktg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата_обновления')),
                ('document', models.FileField(null=True, upload_to='property_documents/', verbose_name='Документ_обоснование')),
                ('KTG', models.FloatField(verbose_name='КТГ')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='cars.yearmonth', verbose_name='Период')),
            ],
            options={
                'verbose_name': 'KTG - КТГ',
            },
        ),
    ]