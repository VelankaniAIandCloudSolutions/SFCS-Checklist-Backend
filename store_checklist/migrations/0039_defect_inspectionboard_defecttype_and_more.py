# Generated by Django 4.2.8 on 2024-04-02 04:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0038_checklistitem_is_issued_to_production'),
    ]

    operations = [
        migrations.CreateModel(
            name='Defect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('defect_image', models.FileField(upload_to='defect_images')),
            ],
        ),
        migrations.CreateModel(
            name='InspectionBoard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('inspection_board_image', models.FileField(upload_to='inspection_board_images')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspection_boards', to='store_checklist.product')),
            ],
        ),
        migrations.CreateModel(
            name='DefectType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('defect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='defect_types', to='store_checklist.defect')),
            ],
        ),
        migrations.AddField(
            model_name='defect',
            name='inspection_board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_boards', to='store_checklist.inspectionboard'),
        ),
    ]
