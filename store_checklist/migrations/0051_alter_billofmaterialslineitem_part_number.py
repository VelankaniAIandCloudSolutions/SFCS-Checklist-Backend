# Generated by Django 4.2.8 on 2024-05-23 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0050_bomformat_sample_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billofmaterialslineitem',
            name='part_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]