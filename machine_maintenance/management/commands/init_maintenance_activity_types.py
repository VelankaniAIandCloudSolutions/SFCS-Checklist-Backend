from django.core.management.base import BaseCommand
from machine_maintenance.models import MaintenanceActivityType


class Command(BaseCommand):
    help = 'Initialize Maintenance Activity Types'

    def handle(self, *args, **kwargs):
        # Check if MaintenanceActivityType objects already exist
        if MaintenanceActivityType.objects.exists():
            self.stdout.write(self.style.SUCCESS(
                'Maintenance Activity Types already initialized.'))
            return

        # Create initial MaintenanceActivityType entries
        initial_types = [
            {'name': 'Daily', 'code': 'D'},
            {'name': 'Weekly', 'code': 'W'},
            {'name': 'Monthly', 'code': 'M'},
            {'name': 'Yearly', 'code': 'Y'},
        ]
        for activity_type_data in initial_types:
            MaintenanceActivityType.objects.get_or_create(**activity_type_data)

        self.stdout.write(self.style.SUCCESS(
            'Maintenance Activity Types initialized successfully.'))
