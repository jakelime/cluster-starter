# engines/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model

from engines import models

UserModel = get_user_model()


admin.site.register(models.EngineMakeModel)
admin.site.register(models.EngineInstanceModel)
admin.site.register(models.EnginePartModel)
