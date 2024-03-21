import datetime
import time
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

    setting = MaintenancePlanSetting.objects.first()

    if setting is None:
        return []

    days_to_raise_alert = setting.days_to_raise_alert
 # Calculate the date range based on the days_to_raise_alert
    alert_start_date = timezone.now().date(
    ) - timezone.timedelta(days=days_to_raise_alert)
    alert_end_date = timezone.now().date()

    # Filter maintenance plans scheduled within the calculated date range
    recent_scheduled_plans = MaintenancePlan.objects.filter(
        maintenance_date__gte=alert_start_date,
        maintenance_date__lt=alert_end_date
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


@shared_task
def send_maintenance_activity_not_completed_email(maintenance_activity_id):
    try:
        # Retrieve the MaintenanceActivity object
        activity = MaintenanceActivity.objects.get(pk=maintenance_activity_id)

        # Prepare the context data to be passed to the template
        context = {
            'activity': activity,
            # Add more context data as needed
            # Add the website link as needed
            'website_link': 'https://sfcs.xtractautomation.com/machine/calendar-monthly-view'
        }

        print(context)

        # Render the template with the context data
        html_message = render_to_string(
            'maintenance_activity_not_completed.html', context)
        plain_message = strip_tags(html_message)

        subject = 'Maintenance Activity Not Completed Alert'
        sender_email = settings.EMAIL_HOST_USER
        sender_name = 'Velankani SFCS'
        email_from = f'{sender_name} <{sender_email}>'
        recipient_list = UserAccount.objects.filter(
            is_machine_maintenance_supervisor_team=True).values_list('email', flat=True)
        recipient_list.append('katochsatvik@gmail.com')

        # Send the email
        send_mail(subject, plain_message, sender_email,
                  recipient_list, html_message=html_message)
        print("Maintenance activity not completed email sent successfully")
        print("Email sent to the following recipients:")
        for email in recipient_list:
            print(email)
    except MaintenanceActivity.DoesNotExist:
        # Handle the case where the MaintenanceActivity does not exist
        print("Maintenance Activity is missing")

    except Exception as e:
        # Handle other exceptions
        print(f"An error occurred: {e}")


@shared_task
def check_missing_activity_and_send_email_for_today():
    try:

        current_date = timezone.now().date()

        # Get all maintenance plans created before 1:00 PM IST today
        plans_with_no_activities_of_today_query_set = MaintenancePlan.objects.filter(
            maintenance_date=current_date,
            maintenance_activities__isnull=True
        )

        # Prepare the email content and recipients only if there are plans with missing activities
        plans_with_no_activities_of_today = []

        # Filter out plans without maintenance activities
        for plan in plans_with_no_activities_of_today_query_set:
            plans_with_no_activities_of_today.append(plan)

        if plans_with_no_activities_of_today:
            # Prepare the email content
            context = {
                'created_by': plans_with_no_activities_of_today[0].created_by,
                'maintenance_plans_with_no_activities': plans_with_no_activities_of_today,
                'website_link': 'https://sfcs.xtractautomation.com/machine'
                # Add more context data as needed
            }
            print(context)
            html_message = render_to_string(
                'maintenance_activity_missing_alert_email.html', context)
            plain_message = strip_tags(html_message)
            subject = 'Missing Maintenance Activity Alert'
            sender_email = settings.EMAIL_HOST_USER
            sender_name = 'Velankani SFCS'
            email_from = f'{sender_name} <{sender_email}>'

            recipient_emails = set(
                plan.created_by.email for plan in plans_with_no_activities_of_today)
            recipient_emails_list = list(recipient_emails)
            # recipient_emails_list.append('satvikkatoch@velankanigroup.com')
            recipient_emails_list.append('katochsatvik@gmail.com')
            # recipient_emails = [
            #     'katochsatvik@gmail.com']

            # Send the email
            send_mail(subject, plain_message, email_from,
                      recipient_emails, html_message=html_message)

            print("Missing maintenance activity email sent successfully")
            print("Email sent to the following recipients:")
            for email in recipient_emails:
                print(email)

        # Return plans with missing activities
        return

    except Exception as e:
        print(f"An error occurred: {e}")
