from requests import Response
from .models import MaintenancePlan
from accounts.serializers import *

from celery import current_task, shared_task
import pandas as pd
from django.db import transaction
from .models import *
from accounts.models import UserAccount

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
def maintenance_alert_email():
    # Get plans with no activities
    plans_with_no_activities = get_plans_with_no_activities()

    # Send maintenance activity missing email
    send_maintenance_activity_missing_mail(plans_with_no_activities)

    print("Maintenance activity missing email sent successfully")

    return {'success': True, 'message': 'Maintenance activity missing email sent successfully'}


def get_plans_with_no_activities():
    # Define the date range for the last two days excluding today
    two_days_ago = timezone.now().date() - timezone.timedelta(days=2)
    today = timezone.now().date()

    # Filter maintenance plans scheduled in the last two days excluding today
    recent_scheduled_plans = MaintenancePlan.objects.filter(
        maintenance_date__gte=two_days_ago,
        maintenance_date__lt=today
    )

    # Initialize an array to store plans with no maintenance activities created
    plans_with_no_activities = []

    # Filter out plans without maintenance activities
    for plan in recent_scheduled_plans:
        if not plan.maintenance_activities.exists():
            plans_with_no_activities.append(plan)

    # Do something with plans_with_no_activities, like sending alerts or logging
    # For example, just printing their IDs along with maintenance dates
    for plan in plans_with_no_activities:
        print(
            f"Plan ID {plan.id} scheduled on {plan.maintenance_date} has no activities.")

    return plans_with_no_activities


def send_maintenance_activity_missing_mail(plans_with_no_activities):
    try:
        print('inside machine maintenance miss alert task')

        print(plans_with_no_activities)

        if plans_with_no_activities:  # Ensure there are plans with no activities

            recipient_emails = set(
                plan.created_by.email for plan in plans_with_no_activities)
            recipient_emails_list = list(recipient_emails)
            recipient_emails_list.append('satvikkatoch@velankanigroup.com')
            recipient_emails_list.append('katochsatvik@gmail.com')

            context = {
                'created_by': plans_with_no_activities[0].created_by,
                'maintenance_plans_with_no_activities': plans_with_no_activities,
                'website_link': 'https://sfcs.xtractautomation.com/machine'
                # Add other context variables as neededd
            }
            print(context)

            html_message = render_to_string(
                'maintenance_activity_missing_alert_email.html', context)
            plain_message = strip_tags(html_message)

            subject = 'Maintenance Activity Missing Alert'
            sender_email = settings.EMAIL_HOST_USER
            sender_name = 'Velankani SFCS'
            email_from = f'{sender_name} <{sender_email}>'

            # Send email
            send_mail(subject, plain_message, email_from,
                      recipient_emails_list, html_message=html_message)

            print(
                f"Maintenance activity missing email sent to {plans_with_no_activities[0].created_by.email}")

    except Exception as e:
        # Handle any exceptions
        print(f"Error sending maintenance activity missing email: {e}")
