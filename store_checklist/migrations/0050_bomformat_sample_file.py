# Generated by Django 4.2.8 on 2024-05-09 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0049_bomformat_billofmaterials_bom_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='bomformat',
            name='sample_file',
            field=models.FileField(blank=True, null=True, upload_to='bom_format_files/'),
        ),
    ]
