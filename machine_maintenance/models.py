from django.db import models
from accounts.models import BaseModel
from django.utils import timezone
# Create your models here.


class Line(BaseModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Machine(BaseModel):
    name = models.CharField(max_length=255)

    line = models.ForeignKey(Line, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Model(BaseModel):
    name = models.CharField(max_length=255)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class MaintenanceActivityType(BaseModel):

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=5)
    time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class MaintenancePlan(BaseModel):

    maintenance_date = models.DateField(default=timezone.now)
    description = models.TextField(null=True, blank=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    maintenance_activity_type = models.ForeignKey(
        MaintenanceActivityType, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "Maintenance plan for  MACHINE ID: " + str(self.machine.id)


class MaintenanceActivity(BaseModel):
    maintenance_plan = models.ForeignKey(
        MaintenancePlan, on_delete=models.CASCADE)
