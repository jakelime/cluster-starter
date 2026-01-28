# joborders/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model

from joborders import models

UserModel = get_user_model()


admin.site.register(models.LeadingOrderModel)
admin.site.register(models.ReferenceOrderModel)
