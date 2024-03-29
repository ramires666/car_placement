# Generated by Django 5.0.1 on 2024-02-13 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0016_remove_mine_slug_remove_shaft_slug_remove_site_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='mine',
            name='slug',
            field=models.SlugField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shaft',
            name='slug',
            field=models.SlugField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='slug',
            field=models.SlugField(blank=True, null=True),
        ),
    ]
