from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.decorators import authentication_classes, permission_classes
from urllib.parse import urlparse
from .models import *
import datetime

import requests
import os
import tempfile

def parse_log_file(s3_url, product=None, board_type='1UP', log_files_folder=None, date=None, log_type=None):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        response = requests.get(s3_url)
        if response.status_code == 200:
            temp_file.write(response.content)
            with open(temp_file_path, 'r') as file:
                lines = file.readlines()
            if log_type == 'aoi':
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

                board, created = Board.objects.get_or_create(serial_number=serial_number, defaults={
                    'product': product,
                    'type': board_type
                })

                panel, created = Panel.objects.get_or_create(name=panel_name, board=board, defaults={
                    'type': panel_type
                })

                if log_files_folder:
                    machine = Machine.objects.filter(log_files_folder=log_files_folder).first()
                    if machine:
                        board_log, created = BoardLog.objects.get_or_create(
                            log_file_url=s3_url,
                            defaults={
                                'date': date,
                                'panel': panel,
                                'result': result,
                            }
                        )
                        board_log.machine.add(machine)
                        board_log.save()
                    else:
                        aoi_machines = Machine.objects.filter(name__icontains='aoi')
                        if aoi_machines:
                            board_log, created = BoardLog.objects.get_or_create(
                                log_file_url=s3_url,
                                defaults={
                                    'date': date,
                                    'panel': panel,
                                    'result': result,
                                }
                            )
                            board_log.machine.add(*aoi_machines)
                            board_log.save()

            os.unlink(temp_file_path)

            return {
                'board_log': board_log
            }
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
    date = path_components[2]
    log_files_folder = path_components[3]
    if 'aoi' in log_files_folder.lower():
        log_type = 'aoi'
    board_log = parse_log_file(s3_url=s3_url, log_files_folder=log_files_folder, date=date, log_type=log_type)
    board_log_serializer = BoardLogSerializer(board_log)
    return Response({
        'board_log': board_log_serializer.data
    })

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_machine_logs(request):
    if 'board_number' in request.query_params:
        board_number = request.query_params['board_number']
        board_logs = BoardLog.objects.filter(
            panel__board__serial_number=board_number)
        serializer = BoardLogSerializer(board_logs, many=True)
        return Response({"boardLogs": serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Board number not provided in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
