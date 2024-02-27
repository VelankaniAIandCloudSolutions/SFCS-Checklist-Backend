from django.core.management.base import BaseCommand
from machine_maintenance.models import MaintenanceActivityType


class Command(BaseCommand):
    help = 'Initialize Maintenance Activity Types'

    def handle(self, *args, **kwargs):
        # Initialize MaintenanceActivityType entries
        initial_types = [
            {'name': 'Daily', 'code': 'D'},
            {'name': 'Weekly', 'code': 'W'},
            {'name': 'Monthly', 'code': 'M'},
            {'name': 'Quarterly', 'code': 'Q'},  # Added Quarterly
            {'name': 'Half Yearly', 'code': 'HF'},  # Added Half Yearly
            {'name': 'Yearly', 'code': 'Y'},
        ]

        # Get existing types from the database
        existing_types = MaintenanceActivityType.objects.all()

        # Track existing type names
        existing_type_names = set(
            existing_type.name for existing_type in existing_types)

        created_types = []
        for activity_type_data in initial_types:
            activity_type, created = MaintenanceActivityType.objects.get_or_create(
                **activity_type_data)
            if created:
                created_types.append(activity_type)

        new_type_names = set(
            activity_type_data['name'] for activity_type_data in initial_types) - existing_type_names

        if created_types:
            self.stdout.write(self.style.SUCCESS(
                f'{len(created_types)} Maintenance Activity Type(s) initialized successfully:'))
            for activity_type in created_types:
                self.stdout.write(
                    f'- Name: {activity_type.name}, Code: {activity_type.code}')

        if existing_type_names:
            self.stdout.write(self.style.WARNING(
                f'{len(existing_type_names)} Maintenance Activity Type(s) already existed:'))
            for name in existing_type_names:
                self.stdout.write(f'- Name: {name}')

        if new_type_names:
            self.stdout.write(self.style.SUCCESS(
                f'{len(new_type_names)} Maintenance Activity Type(s) newly initialized:'))
            for name in new_type_names:
                self.stdout.write(f'- Name: {name}')
