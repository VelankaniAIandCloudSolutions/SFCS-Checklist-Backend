from django.core.management.base import BaseCommand
from store_checklist.models import Distributor

from pricing.models import PackageType , PackageType


class Command(BaseCommand):
    help = 'Initialize database with default package types'

    def handle(self, *args, **kwargs):
        package_types = [
            'Cut Tape',
            # 'Tape & Reel',
            'Bulk',
            'Bag',
            'Ammo Pack',
            'Each',
            # Add more package types as needed
        ]

        for name in package_types:
            obj, created = PackageType.objects.update_or_create(
                name=name,
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created package type: {obj.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Successfully updated package type: {obj.name}'))
