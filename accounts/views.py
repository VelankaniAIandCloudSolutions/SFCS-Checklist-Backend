from django.shortcuts import render
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .serializers import UserAccountSerializer, UserCreateSerializer
from .models import UserAccount

@api_view(['GET'])
@permission_classes([])
def get_all_users(request):
    users = UserAccount.objects.all()
    serializer = UserAccountSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([])
def get_user_by_id(request, user_id):
    user = get_object_or_404(UserAccount, id=user_id)
    serializer = UserAccountSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([])
def update_user(request, user_id):
    user = get_object_or_404(UserAccount, id=user_id)
    serializer = UserAccountSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([])
def delete_user(request, user_id):
    user = get_object_or_404(UserAccount, id=user_id)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

