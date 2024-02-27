from django.core.management.base import BaseCommand
from machine_maintenance.models import Line  # Adjust import as per your model


class Command(BaseCommand):
    help = 'Initialize Line instances'

    def handle(self, *args, **kwargs):
        # Initialize Line entries
        initial_lines = [
            {'name': 'Line-1', 'description': None},
            {'name': 'Line-2', 'description': None},
            {'name': 'Line-3', 'description': None},
            # Add more lines here if needed
        ]

        # Get existing lines from the database
        existing_lines = Line.objects.all()

        # Track existing line names
        existing_line_names = set(
            existing_line.name for existing_line in existing_lines)

        created_lines = []
        for line_data in initial_lines:
            line, created = Line.objects.get_or_create(
                **line_data)
            if created:
                created_lines.append(line)

        new_line_names = set(
            line_data['name'] for line_data in initial_lines) - existing_line_names

        if created_lines:
            self.stdout.write(self.style.SUCCESS(
                f'{len(created_lines)} Line(s) initialized successfully:'))
            for line in created_lines:
                self.stdout.write(
                    f'- Name: {line.name}, Description: {line.description if line.description else "No description provided"}')

        if existing_line_names:
            self.stdout.write(self.style.WARNING(
                f'{len(existing_line_names)} Line(s) already existed:'))
            for name in existing_line_names:
                self.stdout.write(f'- Name: {name}')

        if new_line_names:
            self.stdout.write(self.style.SUCCESS(
                f'{len(new_line_names)} Line(s) newly initialized:'))
            for name in new_line_names:
                self.stdout.write(f'- Name: {name}')
