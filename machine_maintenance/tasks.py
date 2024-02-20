from .models import MaintenancePlan
from accounts.serializers import *
from .models import Order
from celery import current_task, shared_task
import pandas as pd
from django.db import transaction
from .models import *
from accounts.models import UserAccount
from .serializers import BillOfMaterialsLineItemSerializer
from django.utils import timezone
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from celery.schedules import crontab
logger = logging.getLogger(__name__)


@shared_task
def check_maintenance_activities():
    # Define a timedelta for two consecutive days
    consecutive_days = timezone.now() - timezone.timedelta(days=2)

    # Initialize an empty list to store maintenance plans with missing activities
    missing_activity_plans = []

    # Get all maintenance plans with missing activities for the last two consecutive days
    maintenance_plans = MaintenancePlan.objects.filter(
        maintenance_activities__created_at__lt=consecutive_days
    ).distinct()

    # for now store team profiles rememeber to add created m is_machine_team
    machine_team_profiles = UserAccount.objects.filter(is_store_team=True)
    machine_team_profiles_serializer = UserAccountSerializer(
        machine_team_profiles, many=True).data
    recipient_emails = [profile['email']
                        for profile in machine_team_profiles_serializer]
    recipient_first_names = [profile['first_name']
                             for profile in machine_team_profiles_serializer]

    # Loop through each maintenance plan
    for plan in maintenance_plans:
        # Send the alert email to the boss (created_by)
        boss_email = plan.created_by.email
        boss_first_name = plan.created_by.first_name
        send_maintenance_activity_missing_mail(
            plan, boss_email, boss_first_name, recipient_emails, recipient_first_names)

        # Append the maintenance plan to the list
        missing_activity_plans.append(plan)

    # Return the list of maintenance plans with missing activities
    return missing_activity_plans


def send_maintenance_activity_missing_mail(maintenance_plan, boss_email, boss_first_name, recipient_emails, recipient_first_names):
    try:
        print('inside machine maintenance miss alert task')

        context = {
            'machine_name': maintenance_plan.machine.name,
            'machine_line': maintenance_plan.machine.line.name,
            'created_by': boss_first_name,  # Use the boss's first name
            'created_at': maintenance_plan.created_at,
            'maintenance_date': maintenance_plan.maintenance_date,
            # Concatenate recipient first names
            'recipient_first_names': ', '.join(recipient_first_names),
            'website_link': 'https://sfcs.xtractautomation.com/machine/mark-maintenance-plan'

            # Add other context variables as needed
        }
        html_message = render_to_string(
            'maintenance_activity_missing_alert_email.html', context)
        plain_message = strip_tags(html_message)

        subject = 'Maintenance Activity Missing Alert'
        sender_email = settings.EMAIL_HOST_USER
        sender_name = 'Velankani SFCS'
        email_from = f'{sender_name} <{sender_email}>'

        send_mail(subject, plain_message, email_from, [
                  boss_email], html_message=html_message)

        print(f"Maintenance activity missing email sent to {boss_email}")

    except Exception as e:
        # Handle any exceptions
        print(f"Error sending maintenance activity missing email: {e}")
