# Generated by Django 5.0.1 on 2024-02-13 14:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0015_mine_slug_shaft_slug_site_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mine',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='shaft',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='site',
            name='slug',
        ),
    ]
