from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(BillOfMaterials)
admin.site.register(Project)
admin.site.register(Product)
admin.site.register(BillOfMaterialsLineItem)
admin.site.register(BillOfMaterialsLineItemType)
admin.site.register(BillOfMaterialsLineItemReference)
admin.site.register(ManufacturerPart)
admin.site.register(Manufacturer)
admin.site.register(Checklist)
admin.site.register(ChecklistItem)
admin.site.register(ChecklistItemUID)
admin.site.register(ChecklistItemType)
admin.site.register(ChecklistSetting)
admin.site.register(AssemblyStage)
