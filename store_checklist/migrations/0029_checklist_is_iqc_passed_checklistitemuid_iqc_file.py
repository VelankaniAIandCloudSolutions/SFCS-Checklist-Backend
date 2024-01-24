# Generated by Django 4.2.8 on 2024-01-22 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0028_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklist',
            name='is_iqc_passed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='checklistitemuid',
            name='iqc_file',
            field=models.FileField(blank=True, null=True, upload_to='iqc_files/'),
        ),
    ]