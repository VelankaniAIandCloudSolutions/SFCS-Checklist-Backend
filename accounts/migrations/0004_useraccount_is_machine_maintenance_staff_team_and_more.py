# Generated by Django 4.2.8 on 2024-03-01 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_useraccount_is_design_team_useraccount_is_store_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='is_machine_maintenance_staff_team',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='is_machine_maintenance_supervisor_team',
            field=models.BooleanField(default=False),
        ),
    ]
