# Generated by Django 3.2.5 on 2023-12-07 06:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0003_billofmaterialslineitem_customer_part_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billofmaterialslineitem',
            name='bom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bom_line_items', to='store_checklist.billofmaterials'),
        ),
    ]
