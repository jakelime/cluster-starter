# creds/appfilters.py
from django.contrib.auth import get_user_model
from django_filters import FilterSet

UserModel = get_user_model()


class UserFilter(FilterSet):

    class Meta:
        model = UserModel
        fields = {
            "username": ["icontains"],
            "email": ["icontains"],
            "preferred_name": ["icontains"],
            "first_name": ["icontains"],
            "last_name": ["icontains"],
        }
