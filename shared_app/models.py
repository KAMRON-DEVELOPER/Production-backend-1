from django.db import models
from uuid import uuid4


class BaseModel(models.Model):
    """id, created_time, updated_time"""
    id = models.UUIDField(default=uuid4, unique=True, editable=False, primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)
