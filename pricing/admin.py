from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PartPricing)
admin.site.register(AccessToken)


admin.site.register(Manufacturer)
admin.site.register(ManufacturerPart)
admin.site.register(Currency)
admin.site.register(PackageType)
admin.site.register(ManufacturerPartDistributorDetail)
admin.site.register(DistributorPackageTypeDetail)
admin.site.register(ManufacturerPartPricing)
