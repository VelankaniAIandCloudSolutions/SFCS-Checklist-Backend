# Generated by Django 5.0.6 on 2024-05-30 03:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0007_alter_partpricing_part_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesstoken',
            name='token_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]