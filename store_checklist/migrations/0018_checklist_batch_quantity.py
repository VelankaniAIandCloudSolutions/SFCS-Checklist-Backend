# Generated by Django 3.2.5 on 2023-12-20 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0017_auto_20231214_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklist',
            name='batch_quantity',
            field=models.IntegerField(default=1),
        ),
    ]
