from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import *
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.decorators import authentication_classes, permission_classes


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
