# Generated by Django 3.2.5 on 2023-12-20 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0019_alter_checklist_qr_code_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklist',
            name='qr_code_link',
            field=models.TextField(blank=True, null=True),
        ),
    ]
