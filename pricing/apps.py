from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError

class PricingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pricing'

    # def ready(self):
    #     super().ready()
    #     self.run_init_db()

    # def run_init_db(self):
    #     try:
    #         call_command('init_db')
    #     except OperationalError as e:
    #         print(f"Database error: {e}")
    #     except Exception as e:
    #         print(f"Unexpected error: {e}")
