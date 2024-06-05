from django.db import models
from accounts.models import BaseModel
from store_checklist.models import *
from store_checklist.models import Project, Product


class AccessToken(BaseModel):
    access_token = models.CharField(max_length=255)
    expires_in = models.IntegerField()
    expiry_date_time = models.DateTimeField()

    def __str__(self):
        return self.access_token


class PartPricing(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True)
    part_number = models.CharField(max_length=255, unique=True)
    part_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rate = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    po_json = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.part_number


class Currency(models.Model):
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.name} ({self.symbol})'


class PackageType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ManufacturerPartDistributorDetail(models.Model):
    description = models.TextField()
    product_url = models.URLField()
    datasheet_url = models.URLField()
    stock = models.PositiveIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    manufacturer_part = models.ForeignKey(
        ManufacturerPart, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.manufacturer_part} - {self.distributor}'


class DistributorPackageTypeDetail(models.Model):
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    package_type = models.ForeignKey(PackageType, on_delete=models.CASCADE)
    related_field = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.distributor} - {self.package_type}'


class ManufacturerPartPricing(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    manufacturer_part_distributor_detail = models.ForeignKey(
        ManufacturerPartDistributorDetail, on_delete=models.CASCADE, related_name='pricing_details')

    def __str__(self):
        return f'{self.manufacturer_part_distributor_detail} - {self.quantity} @ {self.price}'
