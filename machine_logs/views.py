
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import *
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from machine_maintenance.serializers import *
from machine_maintenance.models import *
from rest_framework.decorators import authentication_classes, permission_classes
from datetime import datetime


# Create your views here.
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
            return Response({"error": "Please provide at least one date."}, status=400)

        # Serialize the machine logs using BoardLogSerializer
        serialized_logs = BoardLogSerializer(machine_logs, many=True).data
        return JsonResponse({'machine_reports': serialized_logs})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
