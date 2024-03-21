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
    line = models.ForeignKey(
        Line, on_delete=models.CASCADE, related_name='machines')

    def __str__(self):
        return f'{self.name} (Line: {self.line.name})'


class Model(BaseModel):
    name = models.CharField(max_length=255)
    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, related_name='models')

    def __str__(self):
        return self.name


class MaintenanceActivityType(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=5)
    time = models.IntegerField(
        null=True, blank=True, verbose_name="Duration (minutes)")

    def __str__(self):
        return self.name


class MaintenancePlan(BaseModel):
    maintenance_date = models.DateField(default=timezone.now)
    description = models.TextField(null=True, blank=True)
    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, related_name='maintenance_plans')
    maintenance_activity_type = models.ForeignKey(
        MaintenanceActivityType, on_delete=models.SET_NULL, null=True, related_name='maintenance_plans')

    def __str__(self):
        return f"Maintenance plan for Machine ID: {self.machine.id}={self.machine.name}"


class MaintenanceActivity(BaseModel):
    maintenance_plan = models.ForeignKey(
        MaintenancePlan, on_delete=models.CASCADE, related_name='maintenance_activities')
    note = models.TextField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Maintenance activity for Maintenance Plan ID: {self.maintenance_plan.id} "


class MaintenancePlanSetting(BaseModel):
    days_to_raise_alert = models.PositiveBigIntegerField(default=1)
