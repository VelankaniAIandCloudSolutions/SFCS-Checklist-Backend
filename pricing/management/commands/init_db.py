# pricing/management/commands/init_db.py
from django.core.management.base import BaseCommand
from store_checklist.models import Distributor

from pricing.models import PackageType , DistributorPackageTypeDetail , PackageType

class Command(BaseCommand):
    help = 'Initialize database with default distributor data'

    def handle(self, *args, **kwargs):
        distributors = [
            {
                'name': 'Digikey',
                'api_url': 'https://api.digikey.com/products/v4/search/',
                'access_id': '8mG60KW8HvJYHk2hCiLDGANQ9HossidT',
                'access_secret': 'euhdJWXXdnd6rH4s',
                'api_key': ''
            },
            {
                'name': 'Mouser',
                'api_url': 'https://api.mouser.com/api/v1/search',
                'access_id': '',
                'access_secret': '',
                'api_key': 'daf53999-5620-4003-8217-5c2ed9947d13'
            },
            {
                'name': 'Element14',
                'api_url': 'https://api.element14.com/catalog/products',
                'access_id': '',
                'access_secret': '',
                'api_key': '574e2u973fa67jt6wb5et68z'
            },
            {
                'name': 'Samtec',
                'api_url': 'https://api.samtec.com/catalog/v3/search',
                'access_id': '',
                'access_secret': '',
                'api_key': 'eyJhbGciOiJIUzI1NiIsImtpZCI6InZlbGFua2FuaSIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJwcm9kIiwib3JnIjoidmVsYW5rYW5pIiwibmFtZSI6IiIsImRpYWciOiJmYWxzZSIsImFwcHMiOlsiY2F0YWxvZyIsImNvbS5zYW10ZWMuYXBpIl0sImlzcyI6InNhbXRlYy5jb20iLCJhdWQiOiJzYW10ZWMuc2VydmljZXMifQ.1OWaiYdOCq2hMZ59dXyw_urBoqtz3PyImocf0IzNKK8'
            },
            {
                'name': 'Arrow',
                'api_url': 'http://api.arrow.com/itemservice/v4/en/search/',
                'access_id': '',
                'access_secret': 'velankani1',
                'api_key': 'cc377bced547b2d0e1ce259cad3c6aabc288553b0aabb9f2ec4e7ff251bafc2c'
            },
            # Add more distributors as needed
        ]

        for distributor_data in distributors:
            distributor, created = Distributor.objects.update_or_create(
                name=distributor_data['name'],
                api_url= distributor_data['api_url'],
                defaults={
                    'access_id': distributor_data['access_id'],
                    'access_secret': distributor_data['access_secret'],
                    'api_key': distributor_data['api_key']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created distributor: {distributor.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Successfully updated distributor: {distributor.name}'))


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

