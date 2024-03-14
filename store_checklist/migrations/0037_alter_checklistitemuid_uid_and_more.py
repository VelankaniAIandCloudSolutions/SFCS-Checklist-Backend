# Generated by Django 4.2.8 on 2024-03-12 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0036_alter_checklist_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistitemuid',
            name='uid',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterUniqueTogether(
            name='checklistitemuid',
            unique_together={('uid', 'checklist_item')},
        ),
    ]