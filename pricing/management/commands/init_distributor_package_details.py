from django.core.management.base import BaseCommand
from store_checklist.models import Distributor

from pricing.models import PackageType , DistributorPackageTypeDetail , PackageType


class Command(BaseCommand):
    help = 'Initialize database with default distributor package type details'

    def handle(self, *args, **kwargs):
        distributor_package_details = [
            {
                'distributor_name': 'Digikey',
                'package_type_name': 'Cut Tape',
                'related_field': '2'
            },
            # {
            #     'distributor_name': 'Digikey',
            #     'package_type_name': 'Tape & Reel',
            #     'related_field': '1'
            # },
            {
                'distributor_name': 'Digikey',
                'package_type_name': 'Bulk',
                'related_field': '3'
            },

            {
                'distributor_name': 'Digikey',
                'package_type_name': 'Bag',
                'related_field': '62'
            },

            {
                'distributor_name': 'Mouser',
                'package_type_name': 'Cut Tape',
                'related_field': 'Cut Tape'
            },
            {
                'distributor_name': 'Mouser',
                'package_type_name': 'Bulk',
                'related_field': 'Bulk'
            },
            {
                'distributor_name': 'Mouser',
                'package_type_name': 'Ammo Pack',
                'related_field': 'Ammo Pack'
            },
            {
                'distributor_name': 'Element14',
                'package_type_name': 'Cut Tape',
                'related_field': 'Cut Tape'
            },
            {
                'distributor_name': 'Element14',
                'package_type_name': 'Each',
                'related_field': 'Each'
            },
            # {
            #     'distributor_name': 'Samtec',
            #     'package_type_name': 'PackageType4',
            #     'related_field': 'RelatedField4'
            # },
            # Add more distributor package details as needed
        ]

        for detail in distributor_package_details:
            try:
                distributor = Distributor.objects.get(name=detail['distributor_name'])
                package_type = PackageType.objects.get(name=detail['package_type_name'])

                obj, created = DistributorPackageTypeDetail.objects.update_or_create(
                    distributor=distributor,
                    package_type=package_type,
                    defaults={'related_field': detail['related_field']},
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created: {obj}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated: {obj}'))

            except Distributor.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Distributor "{detail["distributor_name"]}" does not exist'))
            except PackageType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'PackageType "{detail["package_type_name"]}" does not exist'))

