from django.shortcuts import render
from .models import *
from rest_framework.decorators import api_view,authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .serializers import *
import pandas as pd
import json
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def test_api(request):

    file_path = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
    excel =  pd.read_excel(file_path,sheet_name=1)
    print(excel.iloc[1])
    print(excel.iloc[2])
    print(excel.iloc[3])
    print(excel.iloc[4])
    excel_data = pd.read_excel(file_path, header=5,sheet_name=1).head(10)
    # print(excel_data.columns.tolist())
    data = excel_data.to_dict('records')
    # for index, row in excel_data.iterrows():

    #     print(row['VEPL Part No'])

    return Response({
        'data': json.dumps(data)
    })
