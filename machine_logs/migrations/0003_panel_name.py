# Generated by Django 4.2.8 on 2024-04-23 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('machine_logs', '0002_alter_machinelog_machine'),
    ]

    operations = [
        migrations.AddField(
            model_name='panel',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
