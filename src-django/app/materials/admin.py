# materials/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model

from materials import models

UserModel = get_user_model()


admin.site.register(models.EnginePartShortage)
admin.site.register(models.EnginePartShortageBatch)
