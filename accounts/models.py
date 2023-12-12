from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
       email = self.normalize_email(email)
       user = self.model(email=email, **extra_fields)

       user.set_password(password)
       user.save()

       return user
    
    def create_superuser(self, email, password=None, **extra_fields):   
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class UserAccount(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255,null=True,blank=True)
    phone_number = models.CharField(max_length=13,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        'self', 
        related_name='created_users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field='id'
    )
    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        if self.last_name and self.first_name:
            return "{fname} {lname}".format(fname=self.first_name, lname=self.last_name)
        elif self.last_name=='' and self.first_name:
            return "{fname}".format(fname=self.first_name)
        else:
            return ""

    def __str__(self):
        return self.email
    
class BaseModel(models.Model):
    updated_by = models.ForeignKey(
        'accounts.UserAccount', 
        related_name='%(class)s_updates',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        'accounts.UserAccount', 
        related_name='%(class)s_creators',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)
    created_at = models.DateTimeField(default=timezone.now) 
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
