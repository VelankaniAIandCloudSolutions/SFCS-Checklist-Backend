# Generated by Django 4.2.8 on 2024-02-05 05:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0005_alter_partpricing_po_json'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partpricing',
            old_name='price',
            new_name='total',
        ),
    ]