# Generated by Django 4.2.8 on 2024-04-02 05:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0042_alter_defect_defect_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='defect',
            name='defect_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='defects', to='store_checklist.defecttype'),
        ),
        migrations.AlterField(
            model_name='defect',
            name='inspection_board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='defects', to='store_checklist.inspectionboard'),
        ),
    ]
