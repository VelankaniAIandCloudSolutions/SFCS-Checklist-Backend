from django.db import models
from store_checklist.models import Product
from machine_maintenance.models import Machine
from accounts.models import BaseModel

class Board(BaseModel):
    serial_number  = models.CharField(max_length=20)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='boards')
    type = models.CharField(max_length=6,default='1UP')

    def __str__(self):
        return self.serial_number
    
class Panel(BaseModel):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='panels')
    type = models.CharField(max_length=6,choices=(('Top','Top'),('Bottom','Bottom')), default='Top')

    def __str__(self):
        return self.board.serial_number + ' ' + self.type

class MachineLog(BaseModel):
    date = models.DateField()
    machine = models.ManyToManyField(Machine, related_name='machine_logs')
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name='machine_logs')
    log_file_url = models.URLField()
    begin_date_time = models.DateTimeField(null=True,blank=True)
    end_date_time = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=255,null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.machine.name +  ' ' + self.panel.type + ' ' + str(self.date)