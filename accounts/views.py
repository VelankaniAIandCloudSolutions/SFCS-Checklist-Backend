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
@permission_classes([IsAuthenticated])  # Add authentication check
def get_authenticated_user(request):
    user = request.user  # Access the authenticated user
    # Use your serializer to serialize the user
    serializer = UserAccountSerializer(user)
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


# @api_view(['POST'])
# @permission_classes([])
# def create_user(request):
#     # Extract data from the request
#     email = request.data.get('email')
#     password = request.data.get('password')
#     first_name = request.data.get('first_name')
#     last_name = request.data.get('last_name')
#     phone_number = request.data.get('phone_number')
#     is_superuser = request.data.get('is_superuser', False)
#     is_staff = request.data.get('is_staff', False)
#     is_store_team = request.data.get('is_store_team', False)
#     is_design_team = request.data.get('is_design_team', False)
#     # Add more fields as needed

#     # Perform your own validation as needed
#     if not (email and password and first_name):
#         return Response({'error': 'Incomplete data'}, status=status.HTTP_400_BAD_REQUEST)

#     # Create a user using Django ORM
#     user = UserAccount.objects.create(
#         email=email,
#         password=password,  # Note: You should handle password hashing
#         first_name=first_name,
#         last_name=last_name,
#         phone_number=phone_number,
#         is_superuser=is_superuser,
#         is_staff=is_staff,
#         is_store_team=is_store_team,
#         is_design_team=is_design_team,
#         # Add more fields as needed
#     )

#     # Return a success response
#     return Response({'success': 'User created successfully'}, status=status.HTTP_201_CREATED)


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
