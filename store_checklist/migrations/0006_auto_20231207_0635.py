# Generated by Django 3.2.5 on 2023-12-07 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0005_auto_20231207_0634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billofmaterialslineitem',
            name='level',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='billofmaterialslineitem',
            name='priority_level',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
    ]
