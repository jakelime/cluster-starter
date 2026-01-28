# joborders/appfilters.py
from django_filters import FilterSet

from joborders import models


class LeadingOrderFilter(FilterSet):
    class Meta:
        model = models.LeadingOrderModel
        fields = {
            "ev_lo_number": ["icontains"],
            "engine__esn": ["icontains"],
            "engine__make__model": ["icontains"],
            "customer__name": ["icontains"],
            "ev_status": ["icontains"],
        }
