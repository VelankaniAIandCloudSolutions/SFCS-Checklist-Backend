# Generated by Django 4.2.8 on 2024-06-05 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_checklist', '0053_alter_distributor_api_url'),
        ('pricing', '0008_accesstoken_token_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('symbol', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='ManufacturerPartDistributorDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('product_url', models.URLField()),
                ('datasheet_url', models.URLField()),
                ('stock', models.PositiveIntegerField()),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.currency')),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.distributor')),
                ('manufacturer_part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.manufacturerpart')),
            ],
        ),
        migrations.CreateModel(
            name='PackageType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ManufacturerPartPricing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField()),
                ('manufacturer_part_distributor_detail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_details', to='pricing.manufacturerpartdistributordetail')),
            ],
        ),
        migrations.CreateModel(
            name='DistributorPackageTypeDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('related_field', models.CharField(max_length=255)),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_checklist.distributor')),
                ('package_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pricing.packagetype')),
            ],
        ),
    ]
