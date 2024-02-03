from django.urls import path
from .views import *

urlpatterns = [
    path('check-login',check_login,name='check_login'),
    path('users/', get_all_users, name='get_all_users'),
    path('users/<int:user_id>/', get_user_by_id, name='get_user_by_id'),
    path('users/create/', create_user, name='create_user'),
    path('users/update/<int:user_id>/', update_user, name='update_user'),
    path('users/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('user/authenticated/', get_authenticated_user,name='get_authenticated_user'), 
]
