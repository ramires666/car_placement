# Generated by Django 5.0.1 on 2024-02-07 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0011_yearmonth_month'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='company',
        ),
        migrations.AlterModelOptions(
            name='mine',
            options={'verbose_name': 'Рудник', 'verbose_name_plural': 'Рудники'},
        ),
        migrations.AlterModelOptions(
            name='shaft',
            options={'verbose_name': 'Шахта', 'verbose_name_plural': 'Шахты'},
        ),
        migrations.AlterModelOptions(
            name='site',
            options={'verbose_name': 'Участок', 'verbose_name_plural': 'Участки'},
        ),
        migrations.AlterModelOptions(
            name='yearmonth',
            options={'verbose_name': 'Период', 'verbose_name_plural': 'Периоды'},
        ),
        migrations.RemoveField(
            model_name='site',
            name='year_month',
        ),
        migrations.AlterField(
            model_name='yearmonth',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.DeleteModel(
            name='Company',
        ),
        migrations.DeleteModel(
            name='Product',
        ),
    ]
