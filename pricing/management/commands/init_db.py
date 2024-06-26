# pricing/management/commands/init_db.py
from django.core.management.base import BaseCommand
from store_checklist.models import Distributor

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
                'api_url': 'https://api.mouser.com/api/v1/search/keyword?apiKey=',
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
                'name': 'Samtec ',
                'api_url': 'https://api.element14.com/catalog/products',
                'access_id': '',
                'access_secret': '',
                'api_key': 'eyJhbGciOiJIUzI1NiIsImtpZCI6InZlbGFua2FuaSIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJwcm9kIiwib3JnIjoidmVsYW5rYW5pIiwibmFtZSI6IiIsImRpYWciOiJmYWxzZSIsImFwcHMiOlsiY2F0YWxvZyIsImNvbS5zYW10ZWMuYXBpIl0sImlzcyI6InNhbXRlYy5jb20iLCJhdWQiOiJzYW10ZWMuc2VydmljZXMifQ.1OWaiYdOCq2hMZ59dXyw_urBoqtz3PyImocf0IzNKK8'
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
