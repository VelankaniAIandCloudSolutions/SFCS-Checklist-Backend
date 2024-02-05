from django.db import models
from accounts.models import BaseModel
from store_checklist.models import Project,Product


class AccessToken(BaseModel):
    access_token = models.CharField(max_length=255)
    expires_in = models.IntegerField()
    expiry_date_time = models.DateTimeField()

    def __str__(self):
        return self.access_token
    
class PartPricing(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank = True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank = True)
    part_number = models.CharField(max_length=255)
    part_name = models.CharField(max_length=255,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    po_json  = models.JSONField(blank=True,null =True)

    def __str__(self):
        return self.part_number