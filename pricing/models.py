from django.db import models
from accounts.models import BaseModel

class AccessToken(BaseModel):
    access_token = models.CharField(max_length=255)
    expires_in = models.IntegerField()
    expiry_date_time = models.DateTimeField()

    def __str__(self):
        return self.access_token