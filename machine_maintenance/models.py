from django.db import models
from accounts.models import BaseModel
from django.utils import timezone
# Create your models here.


class Line(BaseModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

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


class MaintenancePlan(BaseModel):

    maintenance_date = models.DateField(default=timezone.now)
