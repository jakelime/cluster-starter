# engines/appfilters.py
from django_filters import FilterSet

from engines import models


class EngineInstanceFilter(FilterSet):
    class Meta:
        model = models.EngineInstanceModel
        fields = {
            "make__make": ["icontains"],
            "make__series": ["icontains"],
            "make__model": ["icontains"],
            "make__submodel": ["icontains"],
            "config": ["icontains"],
            "esn": ["icontains"],
            "is_engine_module": ["icontains"],
            "module": ["icontains"],
        }
