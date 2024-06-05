from django.contrib import admin
from .models import *
from store_checklist.models import *
# Register your models here.
admin.site.register(PartPricing)

admin.site.register(Distributor)
admin.site.register(Currency)
admin.site.register(PackageType)
admin.site.register(ManufacturerPartDistributorDetail)
admin.site.register(DistributorPackageTypeDetail)
admin.site.register(ManufacturerPartPricing)
