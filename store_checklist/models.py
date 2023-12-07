from django.db import models
from accounts.models import BaseModel
from django.utils import timezone

# Create your models here.
class Product(BaseModel):
    name = models.CharField(max_length=255)
    product_code  = models.CharField(max_length=255)
    product_rev_number  = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Manufacturer(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
        
class ManufacturerPart(BaseModel):
    part_number = models.CharField(max_length=255)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)

    def __str__(self):
        return self.part_number

class AssemblyStage(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class BillOfMaterialsType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class BillOfMaterials(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bom_type = models.ForeignKey(BillOfMaterialsType, on_delete=models.SET_NULL, null=True, blank=True)
    total_line_items = models.IntegerField(default=0)
    total_smt_locations = models.IntegerField(default=0)
    total_pth_locations = models.IntegerField(default=0)
    bom_rev_number = models.CharField(max_length=255)
    issue_date = models.DateField(default=timezone.now)
    bom_file = models.FileField(upload_to='bom_files/', null=True, blank=True)

    def __str__(self):
        return "BOM for : " +  self.product.name 
    
class BillOfMaterialsLineItemType(BaseModel):    
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class BillOfMaterialsLineItem(BaseModel):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE,related_name='bom_line_items')
    level = models.CharField(max_length=4,blank = True, null = True)
    part_number = models.CharField(max_length=255)
    priority_level = models.CharField(max_length=4,blank = True, null = True)
    value = models.CharField(max_length=255)
    pcb_footprint = models.CharField(max_length=255,null=True, blank=True)
    line_item_type = models.ForeignKey(BillOfMaterialsLineItemType, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    manufacturer_parts = models.ManyToManyField(ManufacturerPart, blank=True)
    customer_part_number = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    uom = models.CharField(max_length=255, null=True, blank=True)
    assembly_stage = models.ForeignKey(AssemblyStage, on_delete=models.SET_NULL, null=True, blank=True)
    ecn = models.CharField(max_length=255, null=True, blank=True)
    msl = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.part_number + " for BOM ID: " + str(self.bom.id)
    
class BillOfMaterialsLineItemReference(BaseModel):
    bom_line_item = models.ForeignKey(BillOfMaterialsLineItem, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class ChecklistItem(BaseModel):
    bom_line_item = models.ForeignKey(BillOfMaterialsLineItem, on_delete=models.CASCADE)
    required_quantity = models.IntegerField(default=0)
    present_quantity = models.IntegerField(default=0)
    is_checked = models.BooleanField(default=False)

    def __str__(self):
        return "Checklist for : " +  self.bom_line_item
    
class ChecklistSetting(BaseModel):
    active_bom = models.ForeignKey(BillOfMaterials, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.active_bom:
            return "Active BOM : " +  self.active_bom.product.name
        else:
            return "No Active BOM"