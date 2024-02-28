from django.db import IntegrityError
from django.core.management.base import BaseCommand
# from django.utils.text import slugify
from pytils.translit import slugify

from cars.models import Mine, Shaft, Site

class Command(BaseCommand):
    help = 'Populate slug fields for Mine, Shaft, and Site models from their titles'

    def handle(self, *args, **options):
        self.update_mine_slugs()
        self.update_shaft_slugs()
        self.update_site_slugs()

    def update_mine_slugs(self):
        for mine in Mine.objects.all():
            # if not mine.slug:
            mine.slug = slugify(mine.title)
            try:
                mine.save()
            except IntegrityError:
                mine.slug += f'-{mine.id}'
                mine.save()
            self.stdout.write(self.style.SUCCESS(f'Updated slug for mine "{mine.title}"'))

    def update_shaft_slugs(self):
        for shaft in Shaft.objects.all():
            # if not shaft.slug:
            shaft.slug = slugify(f'{shaft.mine.title}-{shaft.title}')
            try:
                shaft.save()
            except IntegrityError:
                shaft.slug += f'-{shaft.id}'
                shaft.save()
            self.stdout.write(self.style.SUCCESS(f'Updated slug for shaft "{shaft.title}"'))

    def update_site_slugs(self):
        for site in Site.objects.all():
            # if not site.slug:
            site.slug = slugify(f'{site.shaft.title}-{site.title}')
            try:
                site.save()
            except IntegrityError:
                site.slug += f'-{site.id}'
                site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated slug for site "{site.title}"'))

