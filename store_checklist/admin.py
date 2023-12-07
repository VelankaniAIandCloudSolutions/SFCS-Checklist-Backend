from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(BillOfMaterials)
admin.site.register(Product)
admin.site.register(BillOfMaterialsLineItem)
admin.site.register(ManufacturerPart)
admin.site.register(Manufacturer)