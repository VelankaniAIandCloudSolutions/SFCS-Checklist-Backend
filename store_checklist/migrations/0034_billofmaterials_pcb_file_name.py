# Generated by Django 4.2.8 on 2024-02-28 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0033_billofmaterials_pcb_bbt_test_report_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='billofmaterials',
            name='pcb_file_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
