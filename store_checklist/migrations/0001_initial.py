# Generated by Django 3.2.5 on 2023-12-05 06:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssemblyStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assemblystage_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillOfMaterials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('total_line_items', models.IntegerField(default=0)),
                ('total_smt_locations', models.IntegerField(default=0)),
                ('total_pth_locations', models.IntegerField(default=0)),
                ('bom_rev_number', models.CharField(max_length=255)),
                ('issue_date', models.DateField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillOfMaterialsLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('level', models.IntegerField(default=0)),
                ('part_number', models.CharField(max_length=255)),
                ('priority_level', models.IntegerField(default=0)),
                ('value', models.CharField(max_length=255)),
                ('pcb_footprint', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('quantity', models.IntegerField(default=0)),
                ('uom', models.CharField(blank=True, max_length=255, null=True)),
                ('ecn', models.CharField(blank=True, max_length=255, null=True)),
                ('msl', models.CharField(blank=True, max_length=255, null=True)),
                ('assembly_stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store_checklist.assemblystage')),
                ('bom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.billofmaterials')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manufacturer_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('product_code', models.CharField(max_length=255)),
                ('product_rev_number', models.CharField(max_length=255)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ManufacturerPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('part_number', models.CharField(max_length=255)),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.manufacturer')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manufacturerpart_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChecklistSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('active_bom', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store_checklist.billofmaterials')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checklistsetting_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('required_quantity', models.IntegerField(default=0)),
                ('present_quantity', models.IntegerField(default=0)),
                ('is_checked', models.BooleanField(default=False)),
                ('bom_line_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.billofmaterialslineitem')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checklistitem_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillOfMaterialsType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billofmaterialstype_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillOfMaterialsLineItemType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billofmaterialslineitemtype_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillOfMaterialsLineItemReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255)),
                ('bom_line_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.billofmaterialslineitem')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billofmaterialslineitemreference_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='billofmaterialslineitem',
            name='line_item_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store_checklist.billofmaterialslineitemtype'),
        ),
        migrations.AddField(
            model_name='billofmaterialslineitem',
            name='manufacturer_parts',
            field=models.ManyToManyField(blank=True, to='store_checklist.ManufacturerPart'),
        ),
        migrations.AddField(
            model_name='billofmaterialslineitem',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billofmaterialslineitem_updates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='billofmaterials',
            name='bom_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store_checklist.billofmaterialstype'),
        ),
        migrations.AddField(
            model_name='billofmaterials',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.product'),
        ),
        migrations.AddField(
            model_name='billofmaterials',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='billofmaterials_updates', to=settings.AUTH_USER_MODEL),
        ),
    ]
