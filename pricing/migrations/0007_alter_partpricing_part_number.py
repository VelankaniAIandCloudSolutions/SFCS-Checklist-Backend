# Generated by Django 4.2.8 on 2024-03-18 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0006_rename_price_partpricing_total'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partpricing',
            name='part_number',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
