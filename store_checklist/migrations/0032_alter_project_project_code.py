# Generated by Django 4.2.8 on 2024-02-08 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0031_billofmaterials_change_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='project_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
