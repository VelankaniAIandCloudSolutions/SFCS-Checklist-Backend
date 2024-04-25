
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from machine_maintenance.serializers import *
from machine_maintenance.models import *
from rest_framework.decorators import authentication_classes, permission_classes
from datetime import datetime
from urllib.parse import urlparse, unquote
from .models import *
from datetime import datetime
from django.utils import timezone
import requests
import os
import tempfile
import xml.etree.ElementTree as ET
from django.db.models import Q
import pandas as pd

def parse_log_file(s3_url, product=None, board_type='1UP', log_files_folder=None, date=None, log_type=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            response = requests.get(s3_url)
            if response.status_code == 200:
                temp_file.write(response.content)
                if log_type == 'aoi':
                    with open(temp_file_path, 'r') as file:
                        lines = file.readlines()

                    serial_number = ''
                    panel_type = ''
                    panel_name = ''
                    result = lines[-1].strip()

                    for line in lines:
                        if 'Serial Number:' in line:
                            serial_number = line.split(':')[-1].strip()
                        if 'Panel:' in line:
                            panel_name = line.split(':')[-1].strip()
                            panel_info = line.split(':')[-1].strip().lower()
                            if 'top' in panel_info:
                                panel_type = 'Top'
                            elif 'bot' in panel_info or 'bottom' in panel_info:
                                panel_type = 'Bottom'

                    board, created = Board.objects.update_or_create(serial_number=serial_number, defaults={
                        'product': product,
                        'type': board_type
                    })

                    panel, created = Panel.objects.update_or_create(name=panel_name, board=board, defaults={
                        'type': panel_type
                    })

                    if log_files_folder:
                        machines = Machine.objects.filter(
                            log_files_folder=log_files_folder)
                        if machines:
                            board_log, created = BoardLog.objects.update_or_create(
                                log_file_url=s3_url,
                                defaults={
                                    'date': date,
                                    'panel': panel,
                                    'result': result,
                                }
                            )
                            board_log.machines.add(*machines)
                            board_log.save()
                        else:
                            aoi_machines = Machine.objects.filter(
                                name__icontains='aoi')
                            if aoi_machines:
                                board_log, created = BoardLog.objects.update_or_create(
                                    log_file_url=s3_url,
                                    defaults={
                                        'date': date,
                                        'panel': panel,
                                        'result': result,
                                    }
                                )
                                board_log.machines.add(*aoi_machines)
                                board_log.save()
                elif log_type == 'p&p':
                    tree = ET.parse(temp_file_path)
                    root = tree.getroot()
                    begin_date_time = datetime.strptime(
                        root.attrib.get('dateBegin'), "%Y-%m-%dT%H:%M:%S.%f%z")
                    end_date_time = datetime.strptime(root.attrib.get(
                        'dateComplete'), "%Y-%m-%dT%H:%M:%S.%f%z")
                    first_job = root.find('.//jobs/job')
                    panel_type = first_job.attrib.get(
                        'boardSide') if first_job is not None else 'Unknown'
                    panel_name = first_job.attrib.get(
                        'boardName') if first_job is not None else 'Unknown'
                    first_panel = root.find('.//panels/panel')
                    omit_value = first_panel.attrib.get(
                        'omit') if first_panel is not None else None
                    if first_panel is not None and first_panel.attrib.get('panelID') != '':
                        serial_number = first_panel.attrib.get('panelID')
                    else:
                        serial_number  = root.attrib.get('boardID') if root.attrib else 'Unknown'

                    result = 'Omit: ' + omit_value if omit_value else 'Unknown'

                    board, created = Board.objects.update_or_create(serial_number=serial_number, defaults={
                        'product': product,
                        'type': board_type
                    })

                    panel, created = Panel.objects.update_or_create(name=panel_name, board=board, defaults={
                        'type': panel_type
                    })

                    if log_files_folder:
                        machines = Machine.objects.filter(
                            log_files_folder=log_files_folder)
                        if machines:
                            board_log, created = BoardLog.objects.update_or_create(
                                log_file_url=s3_url,
                                defaults={
                                    'date': date,
                                    'panel': panel,
                                    'result': result,
                                    'begin_date_time': begin_date_time,
                                    'end_date_time': end_date_time
                                }
                            )
                            board_log.machines.add(*machines)
                            board_log.save()
                        else:
                            pp_machines = Machine.objects.filter(
                                name__icontains='Pick & Place')
                            if pp_machines:
                                board_log, created = BoardLog.objects.update_or_create(
                                    log_file_url=s3_url,
                                    defaults={
                                        'date': date,
                                        'panel': panel,
                                        'result': result,
                                        'begin_date_time': begin_date_time,
                                        'end_date_time': end_date_time
                                    }
                                )
                                board_log.machines.add(*pp_machines)
                                board_log.save()
            
                elif log_type == 'spi':
                    data = pd.read_csv(temp_file_path, header=0)
                    if '<>' in data.loc[0, 'BarCode']:
                        board_serial_number = data.loc[0, 'BarCode'].strip(
                            '<>')
                    else:
                        board_serial_number = data.loc[0, 'BarCode']

                    begin_date_time_str = data.loc[0, 'Date'] + \
                        ' ' + data.loc[0, 'StartTime']

                    end_date_time_str = data.loc[0,
                                                'Date'] + ' ' + data.loc[0, 'EndTime']

                    begin_date_time = datetime.strptime(
                        begin_date_time_str, '%m/%d/%Y %H:%M:%S')

                    end_date_time = datetime.strptime(
                        end_date_time_str, '%m/%d/%Y %H:%M:%S')

                    first_result = data.loc[0, 'Result']

                    panel_name = data.loc[0, 'Recipe']
                    recipe_path = data.loc[0, 'Recipe'].lower()

                    if 'top' in recipe_path:
                        panel_type = 'Top'
                    elif 'bot' in recipe_path or 'bottom' in recipe_path:
                        panel_type = 'Bottom'
                    else:
                        panel_type = 'Unknown'

                    for_result = None
                    for_operator_review = None
                    second_result = None

                    for index, row in data.iterrows():
                        if row['Date'] == 'Result':
                            for_result = f"Result: {data.loc[index + 1, 'Date']}"

                        if row['StartTime'] == "Operator Review":
                            for_operator_review = f"Operator Review: {data.loc[index + 1, 'StartTime']}"

                        if for_result is not None and for_operator_review is not None:
                            second_result = for_result + ","+" " + for_operator_review
                            break
                    board, created = Board.objects.update_or_create(serial_number=board_serial_number, defaults={
                        'product': product,
                        'type': board_type
                    })
                    panel, created = Panel.objects.update_or_create(name=panel_name, board=board, defaults={
                        'type': panel_type
                    })

                    if log_files_folder:
                        machines = Machine.objects.filter(
                            log_files_folder=log_files_folder)
                        if machines:
                            board_log, created = BoardLog.objects.update_or_create(
                                log_file_url=s3_url,
                                defaults={
                                    'date': date,
                                    'panel': panel,
                                    'result': second_result,
                                    'begin_date_time': begin_date_time,
                                    'end_date_time': end_date_time
                                }
                            )
                            board_log.machines.add(*machines)
                            board_log.save()
                        else:
                            spi_machines = Machine.objects.filter(
                                Q(name__icontains='SPI') | Q(name__icontains='Solder Paste Inspection'))
                            if spi_machines:
                                board_log, created = BoardLog.objects.update_or_create(
                                    log_file_url=s3_url,
                                    defaults={
                                        'date': date,
                                        'panel': panel,
                                        'result': second_result,
                                        'begin_date_time': begin_date_time,
                                        'end_date_time': end_date_time
                                    }
                                )
                                board_log.machines.add(*spi_machines)
                                board_log.save()


                os.unlink(temp_file_path)
                board_log_serializer = BoardLogSerializer(board_log)
                return board_log_serializer.data
            else: 
                print("Failed to download file from S3:")
                return None
    except Exception as e:
        print("Error:", e)
        return None


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_board_log(request):
    try:
        s3_url = request.data.get('s3_url')
        parsed_url = urlparse(s3_url)
        path_components = parsed_url.path.split('/')
        date = path_components[1]
        log_files_folder = unquote(path_components[2])
        log_type = ''
        if 'aoi' in log_files_folder.lower():
            log_type = 'aoi'
        elif 'p&p' in log_files_folder.lower():
            log_type = 'p&p'
        elif 'spi' in log_files_folder.lower():
            log_type = 'spi'

        machines = Machine.objects.filter(log_files_folder=log_files_folder)
        if machines:
            board_log, created = BoardLog.objects.update_or_create(log_file_url=s3_url, defaults={
                'date': timezone.make_aware(datetime.strptime(date, "%d-%m-%Y")).date()
            })
            board_log.machines.add(*machines)
            board_log.save()
        else:
            if 'aoi' in log_files_folder.lower():
                machines = Machine.objects.filter(name__icontains='aoi')
            elif 'p&p' in log_files_folder.lower():
                machines = Machine.objects.filter(name__icontains='Pick & Place')
            elif 'spi' in log_files_folder.lower():
                machines = Machine.objects.filter(Q(name__icontains='SPI') | Q(name__icontains='Solder Paste Inspection'))

        board_log = parse_log_file(s3_url=s3_url, log_files_folder=log_files_folder,
                                   date=timezone.make_aware(datetime.strptime(date, "%d-%m-%Y")).date(), log_type=log_type)
        if board_log is not None:
            return Response({'board_log': board_log})
        else:
            return Response({'error': 'Failed to parse log file.'}, status=400)
    except Exception as e:
        print("Error occurred while processing request:", e)
        return Response({'error': 'An unexpected error occurred.'}, status=500)
    
@api_view(['GET'])
def get_board_logs(request):
    if 'board_number' in request.query_params:
        board_number = request.query_params['board_number']
        board_logs = BoardLog.objects.filter(
            Q(panel__board__serial_number__icontains=board_number)
        )
        serializer = BoardLogSerializer(board_logs, many=True)
        return Response({"boardLogs": serializer.data}, status=status.HTTP_200_OK)

    else:
        return Response({"error": "Board number not provided in query parameters"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_machine_list(request):
    try:
        machines = Machine.objects.all()
        serializer = MachineSerializerNew(machines, many=True)
        return Response({"machines": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_machine_reports_by_date_range(request):
    machine_id = request.GET.get('machineId')
    if not machine_id:
        return Response({"error": "Please select a machine."}, status=400)
    print('machine_id', machine_id)
    start_date = request.GET.get('fromDate')
    print('start_date', start_date)
    end_date = request.GET.get('toDate')
    print('end_date', end_date)

    try:
        # Retrieve machine logs based on the provided machine ID
        machine_logs = BoardLog.objects.filter(machines__id=machine_id)

        # Filter logs based on the provided date range
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            machine_logs = machine_logs.filter(
                date__range=(start_date, end_date))
        elif start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            machine_logs = machine_logs.filter(date__gte=start_date)
        elif end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            machine_logs = machine_logs.filter(date__lte=end_date)
        else:
            # If neither start_date nor end_date provided, return all logs
            machine_logs = machine_logs.all()

        # Serialize the machine logs using BoardLogSerializer
        serialized_logs = BoardLogSerializer(machine_logs, many=True).data
        return Response({'machine_reports': serialized_logs})

    except Exception as e:
        return Response({'error': str(e)}, status=500)
