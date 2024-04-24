from django.shortcuts import render
from .models import *
import datetime
# Create your views here.
def parse_aoi_file(s3_url,file_path,product=None,board_type='1UP', machine = None):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    serial_number = ''
    panel_type = ''
    panel_name = ''
    result = lines[-1].strip() 

    for line in lines:
        if 'Serial Number:' in line:
            serial_number = line.split(':')[-1].strip()
        if 'Panel:' in line:
            panel_info = line.split(':')[-1].strip().lower() 
            if 'top' in panel_info:
                panel_type = 'Top'
            elif 'bot' in panel_info or 'bottom' in panel_info:
                panel_type = 'Bottom'
        # if 'Panel Fail!' in line or 'Panel OK!' in line:
        #     result = line.strip()

    board, created  = Board.objects.get_or_create(serial_number=serial_number, defaults={
        'product': product,
        'type': board_type
    })

    panel, created = Panel.objects.get_or_create(name = panel_name,board=board,defaults={
        'type': panel_type
    })
    
    if machine:
        machine_log = MachineLog.objects.create(
            date=datetime.date.today(),
            panel=panel,
            log_file_url=s3_url, 
            result=result,
            machine=machine
        )
        machine_log.save()


    board_instance = Board(serial_number=serial_number, product=product_instance)
    board_instance.save()

    panel_instance = Panel(board=board_instance, type=panel_type)
    panel_instance.save()

    # Create MachineLog instance
    log_instance = MachineLog(
        date=datetime.date.today(),
        panel=panel_instance,
        log_file_url='http://example.com/logfile',  # Example URL
        result=result
    )
    log_instance.machine.add(machine_instance)
    log_instance.save()

    return {
        'board': board_instance,
        'panel': panel_instance,
        'machine_log': log_instance
    }