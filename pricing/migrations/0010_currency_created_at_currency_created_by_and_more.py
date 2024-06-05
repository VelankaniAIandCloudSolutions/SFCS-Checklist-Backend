# Generated by Django 4.2.8 on 2024-06-05 11:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pricing', '0009_currency_manufacturerpartdistributordetail_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='currency',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='currency',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='currency',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='currency',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributorpackagetypedetail',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='distributorpackagetypedetail',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='distributorpackagetypedetail',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='distributorpackagetypedetail',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='distributorpackagetypedetail',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='manufacturerpartdistributordetail',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='manufacturerpartdistributordetail',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='manufacturerpartdistributordetail',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='manufacturerpartdistributordetail',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='manufacturerpartdistributordetail',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='manufacturerpartpricing',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='manufacturerpartpricing',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='manufacturerpartpricing',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='manufacturerpartpricing',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='manufacturerpartpricing',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='packagetype',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='packagetype',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='packagetype',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='packagetype',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='packagetype',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updates', to=settings.AUTH_USER_MODEL),
        ),
    ]
