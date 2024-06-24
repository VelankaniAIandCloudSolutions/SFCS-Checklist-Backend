from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError

class MachineMaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'machine_maintenance'

    # def ready(self):
    #     super().ready()
    #     self.run_init_machines_and_lines()
    #     self.run_mainter

    # def run_init_machines_and_lines(self):
    #     try:
    #         call_command('init_machines_and_lines')
    #     except OperationalError as e:
    #         print(f"Database error: {e}")
    #     except Exception as e:
    #         print(f"Unexpected error: {e}")