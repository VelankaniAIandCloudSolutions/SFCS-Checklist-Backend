# Generated by Django 4.2.8 on 2024-01-24 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0029_checklist_is_iqc_passed_checklistitemuid_iqc_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='project_rev_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
