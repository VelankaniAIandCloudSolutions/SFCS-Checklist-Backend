# Generated by Django 4.2.8 on 2024-04-25 06:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('machine_logs', '0005_alter_boardlog_machines'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boardlog',
            name='panel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='machine_logs', to='machine_logs.panel'),
        ),
    ]
