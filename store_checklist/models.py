from django.db import models
from accounts.models import BaseModel
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.


class Project(BaseModel):
    name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=255, blank=True, null=True)
    project_rev_number = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=255)
    product_rev_number = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, related_name='products')

    def __str__(self):
        return self.name


class InspectionBoard(BaseModel):

    detected_board_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='inspection_boards'
    )
    inspection_board_image = models.FileField(
        upload_to='inspection_board_images/'
    )

    def __str__(self):
        return self.name


class DefectType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Defect(BaseModel):
    inspection_board = models.ForeignKey(
        InspectionBoard, on_delete=models.CASCADE, related_name='defects'
    )
    defect_image = models.FileField(upload_to='defect_images/')
    defect_type = models.ForeignKey(
        DefectType, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='defects'
    )

    def __str__(self):
        return f"{self.defect_type} - {self.inspection_board}"


class Manufacturer(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ManufacturerPart(BaseModel):
    part_number = models.CharField(max_length=255)
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.CASCADE, related_name='manufacturer_parts')

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
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='boms')
    bom_type = models.ForeignKey(
        BillOfMaterialsType, on_delete=models.SET_NULL, null=True, blank=True,  related_name='boms')
    total_line_items = models.IntegerField(default=0)
    total_smt_locations = models.IntegerField(default=0)
    total_pth_locations = models.IntegerField(default=0)
    bom_rev_number = models.CharField(max_length=255)
    issue_date = models.DateField(default=timezone.now)
    bom_file = models.FileField(upload_to='bom_files/', null=True, blank=True)
    pcb_bbt_test_report_file = models.FileField(
        upload_to='pcb_bbt_test_report_files/', null=True, blank=True)
    pcb_file_name = models.CharField(max_length=255, null=True, blank=True)
    bom_file_name = models.CharField(max_length=255, null=True, blank=True)
    change_note = models.TextField(null=True, blank=True)

    def __str__(self):
        return "BOM for: " + self.product.name


class BillOfMaterialsLineItemType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class BillOfMaterialsLineItem(BaseModel):
    bom = models.ForeignKey(
        BillOfMaterials, on_delete=models.CASCADE, related_name='bom_line_items')
    level = models.CharField(max_length=10, blank=True, null=True)
    # uuid = models.CharField(max_length=20,blank=True,null=True)
    part_number = models.CharField(max_length=255)
    priority_level = models.CharField(max_length=4, blank=True, null=True)
    value = models.CharField(max_length=255)
    pcb_footprint = models.CharField(max_length=255, null=True, blank=True)
    line_item_type = models.ForeignKey(
        BillOfMaterialsLineItemType, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    manufacturer_parts = models.ManyToManyField(
        ManufacturerPart, blank=True, related_name='bom_line_items')
    customer_part_number = models.CharField(
        max_length=255, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    uom = models.CharField(max_length=255, null=True, blank=True)
    assembly_stage = models.ForeignKey(
        AssemblyStage, on_delete=models.SET_NULL, null=True, blank=True)
    ecn = models.CharField(max_length=255, null=True, blank=True)
    msl = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.part_number + " for BOM ID: " + str(self.bom.id)


class BillOfMaterialsLineItemReference(BaseModel):
    bom_line_item = models.ForeignKey(
        BillOfMaterialsLineItem, on_delete=models.CASCADE, blank=True, null=True, related_name='references')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Checklist(BaseModel):

    STATUS_CHOICES = (
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress'),
        ('Failed', 'Failed'),
        ('Paused', 'Paused'),
    )

    bom = models.ForeignKey(
        BillOfMaterials, on_delete=models.CASCADE, related_name='checklists')
    is_passed = models.BooleanField(default=False)
    is_iqc_passed = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS_CHOICES,
                              max_length=255, null=True, blank=True)
    qr_code_link = models.TextField(null=True, blank=True)
    unique_code = models.CharField(max_length=255, blank=True, null=True)
    batch_quantity = models.IntegerField(default=1)

    def __str__(self):
        return "Checklist for BOM ID: " + str(self.bom.id)


@receiver(pre_save, sender=Checklist)
def ensure_single_in_progress_checklist(sender, instance, **kwargs):
    if instance.status == 'In Progress':
        existing_checklist = Checklist.objects.filter(
            bom=instance.bom, status='In Progress').exclude(pk=instance.pk)
        if existing_checklist.exists():
            raise ValueError(
                'There is already an ongoing checklist for this BOM.')


class ChecklistItemType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ChecklistItem(BaseModel):
    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name='checklist_items', null=True)
    checklist_item_type = models.ForeignKey(
        ChecklistItemType, on_delete=models.SET_NULL, null=True, blank=True)
    bom_line_item = models.ForeignKey(
        BillOfMaterialsLineItem, on_delete=models.CASCADE, related_name='checklist_items')
    required_quantity = models.IntegerField(default=0)
    present_quantity = models.IntegerField(default=0)
    is_present = models.BooleanField(default=False)
    is_quantity_sufficient = models.BooleanField(default=False)
    present_quantity_change_note = models.TextField(null=True, blank=True)
    is_issued_to_production = models.BooleanField(default=False)

    def __str__(self):
        return "Checklist Item for: " + str(self.bom_line_item.part_number)


class ChecklistItemUID(BaseModel):
    checklist_item = models.ForeignKey(
        ChecklistItem, on_delete=models.CASCADE, related_name='checklist_item_uids')
    uid = models.CharField(max_length=30, )
    iqc_file = models.FileField(upload_to='iqc_files/', null=True, blank=True)

    def __str__(self):
        return str(self.uid)

    class Meta:
        # Define unique constraint for uid and checklist_item together
        unique_together = ['uid', 'checklist_item']


class ChecklistSetting(BaseModel):
    active_bom = models.ForeignKey(
        BillOfMaterials, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_settings')
    active_checklist = models.ForeignKey(
        Checklist, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_settings')
    active_inspection_board = models.ForeignKey(
        InspectionBoard, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_settings')

    def __str__(self):
        if self.active_bom:
            return "Active BOM: " + self.active_bom.product.name
        else:
            return "No Active BOM"


class Order(BaseModel):
    bom = models.ForeignKey(
        BillOfMaterials, on_delete=models.CASCADE, related_name='orders')
    batch_quantity = models.IntegerField(default=1)

    def __str__(self):
        return 'Order for:  ' + str(self.bom.product.name)
