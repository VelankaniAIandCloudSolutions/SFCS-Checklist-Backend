from django.core.management.base import BaseCommand
# Adjust import as per your model
from machine_maintenance.models import Line, Machine


class Command(BaseCommand):
    help = 'Initialize machines for each line'

    def handle(self, *args, **kwargs):
        # Define the machines for each line
        machines_per_line = {
            'Line-1': [
                'Loader',
                'De Stacker',
                'Laser Marker',
                'Screen Printer-1',
                'Screen Printer-2',
                'Solder Past Inspection',
                'Pick & Place-1',
                'Pick & Place-2',
                'Pick & Place-3',
                'Pick & Place-4',
                'Universal',
                'Pre AOI-1',
                'Pre AOI-2',
                'Reflow Oven',
                'Post AOI',
                'UnLoader'
            ],
            'Line-2': [
                'De Stacker',
                'Laser Marker',
                'Screen Printer-1',
                'Screen Printer-2',
                'Solder Past Inspection',
                'Pick & Place-1',
                'Pick & Place-2',
                'Pick & Place-3',
                'Pick & Place-4',
                'Universal',
                'Pre AOI',
                'Reflow Oven',
                'Post AOI',
                'ICT'
            ],
            'Line-3': [
                'De Stacker',
                'Screen Printer-1',
                'Solder Past Inspection',
                'Pick & Place-1',
                'Pick & Place-2',
                'Pick & Place-3',
                'Pre AOI',
                'Reflow Oven',
                'Post AOI'
            ],
            'Backend': [
                'X-Ray',
                'WaveSoldering-1',
                'Press Fit',
                'Radial Insertion',
                'Router-1',
                'ICT-1',
                'ICT-2',
                'Wave Soldering-2',
                'Router-2'
            ]
        }

        # Track created machines
        created_machines = []

        # Loop through each line and its machines
        for line_name, machines in machines_per_line.items():
            line, _ = Line.objects.get_or_create(name=line_name)
            for machine_name in machines:
                machine, created = Machine.objects.get_or_create(
                    name=machine_name, line=line)
                if created:
                    created_machines.append(machine)

        if created_machines:
            self.stdout.write(self.style.SUCCESS(
                f'{len(created_machines)} machine(s) initialized successfully:'))
            for machine in created_machines:
                self.stdout.write(
                    f'- Name: {machine.name}, Line: {machine.line.name}')
        else:
            self.stdout.write(self.style.WARNING(
                'No new machine instances initialized. Existing instances found.'))
