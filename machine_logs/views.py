from django.shortcuts import render

# Create your views here.
def parse_aoi_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    serial_number = None
    panel_type = None
    result = lines[-1].strip() 
    for line in lines:
        if 'Serial Number:' in line:
            serial_number = line.split(':')[-1].strip()
        if 'Panel:' in line:
            panel_type = line.split(':')[-1].strip()
        # if 'Panel Fail!' in line or 'Panel OK!' in line:
        #     result = line.strip()

    # Assume we have some logic to get Product, Machine instances
    product_instance = Product.objects.first()  # Simplified assumption
    machine_instance = Machine.objects.first()  # Simplified assumption

    # Create Board instance
    board_instance = Board(serial_number=serial_number, product=product_instance)
    board_instance.save()

    # Create Panel instance
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
