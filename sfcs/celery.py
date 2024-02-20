from __future__ import absolute_import, unicode_literals
from celery import Celery
import os
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sfcs.settings')

# Create a Celery instance
app = Celery('sfcs')
app.conf.enable_utc = False
app.conf.update(timezone='Asia/Kolkata')
# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-part-pricing-task': {
        'task': 'pricing.tasks.update_pricing_for_all_products',
        'schedule': timedelta(hours=12),
    },

}

# app.conf.beat_schedule = {
#     'update-part-pricing-task': {
#         'task': 'pricing.tasks.update_pricing_for_all_products',
#         'schedule': timedelta(hours=12),
#     },
#     'check-maintenance-activities': {
#         'task': 'tasks.check_maintenance_activities',
#         'schedule': crontab(minute=0, hour=0),
#     },
# }


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
