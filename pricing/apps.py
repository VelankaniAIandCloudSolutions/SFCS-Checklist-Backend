from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError

class PricingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pricing'

    def ready(self):
        super().ready()
        self.run_init_db()

    def run_init_db(self):
        try:
            commands = [
                'init_distributors',
                'init_package_types',
                'init_distributor_package_details'
            ]

            for command in commands:
                call_command(command)
        except OperationalError as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
