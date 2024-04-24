from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.decorators import authentication_classes, permission_classes
from urllib.parse import urlparse, unquote
from .models import *
from datetime import datetime
from django.utils import timezone
import requests
import os
import tempfile
import xml.etree.ElementTree as ET

def parse_log_file(s3_url, product=None, board_type='1UP', log_files_folder=None, date=None, log_type=None):
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
                        print(panel_name)
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
                    machines = Machine.objects.filter(log_files_folder=log_files_folder)
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
                        aoi_machines = Machine.objects.filter(name__icontains='aoi')
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
                begin_date_time = datetime.strptime(root.attrib.get('dateBegin'), "%Y-%m-%dT%H:%M:%S.%f%z")
                end_date_time = datetime.strptime(root.attrib.get('dateComplete'), "%Y-%m-%dT%H:%M:%S.%f%z")
                first_job = root.find('.//jobs/job')
                panel_type = first_job.attrib.get('boardSide') if first_job is not None else 'Unknown'
                panel_name = first_job.attrib.get('boardName') if first_job is not None else 'Unknown'
                first_panel = root.find('.//panels/panel')
                omit_value = first_panel.attrib.get('omit') if first_panel is not None else None
                serial_number = first_panel.attrib.get('panelID') if first_panel is not None else 'Unknown'
                result  = 'Omit: ' + omit_value if omit_value else 'Unknown' 

                board, created = Board.objects.update_or_create(serial_number=serial_number, defaults={
                    'product': product,
                    'type': board_type
                })

                panel, created = Panel.objects.update_or_create(name=panel_name, board=board, defaults={
                    'type': panel_type
                })

                if log_files_folder:
                    machines = Machine.objects.filter(log_files_folder=log_files_folder)
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
                        pp_machines = Machine.objects.filter(name__icontains='Pick & Place')
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
                pass
            os.unlink(temp_file_path)
            board_log_serializer = BoardLogSerializer(board_log)
            return board_log_serializer.data
        else:
            print("Failed to download file from S3")
            return None

    
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_board_log(request):
    s3_url = request.data.get('s3_url')
    parsed_url = urlparse(s3_url)
    path_components = parsed_url.path.split('/')
    date = path_components[1]
    parse_date_timezone_aware = lambda date_str: timezone.make_aware(datetime.strptime(date_str, "%d-%m-%Y"))
    log_files_folder = unquote(path_components[2])
    if 'aoi' in log_files_folder.lower():
        log_type = 'aoi'
    elif 'p&p' in log_files_folder.lower():
        log_type = 'p&p'
    elif 'spi' in log_files_folder.lower():
        log_type = 'spi'
    board_log = parse_log_file(s3_url=s3_url, log_files_folder=log_files_folder, date = parse_date_timezone_aware(date).date(), log_type=log_type)
    return Response({
        'board_log': board_log
    })

@api_view(['GET'])
def get_machine_logs(request):
    if 'board_number' in request.query_params:
        board_number = request.query_params['board_number']
        board_logs = BoardLog.objects.filter(
            panel__board__serial_number=board_number)
        serializer = BoardLogSerializer(board_logs, many=True)
        return Response({"boardLogs": serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Board number not provided in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
