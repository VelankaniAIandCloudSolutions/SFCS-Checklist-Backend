from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Line)
admin.site.register(Machine)
admin.site.register(Model)
admin.site.register(MaintenanceActivityType)
admin.site.register(MaintenancePlan)
admin.site.register(MaintenanceActivity)
admin.site.register(MaintenancePlanSetting)
