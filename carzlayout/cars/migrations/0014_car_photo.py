# Generated by Django 5.0.1 on 2024-02-10 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0013_uploadfiles_alter_car_cat_alter_car_content_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='photo',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='photos/%Y/%m/%d/', verbose_name='Фоточка'),
        ),
    ]
