# Generated by Django 4.2.8 on 2024-04-24 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('machine_maintenance', '0007_alter_maintenanceplansetting_days_to_raise_alert'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='log_files_folder',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
