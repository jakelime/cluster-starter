import django_filters
from django_filters.widgets import RangeWidget
from django.db.models import Q

from sales import models

class SalesFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method="filter_search", label="Search (UUID | ESN | Customer | Status | Engine Type | Program Type | Facility | Salesperson | Bid Status)"
    )

    # TODO: look into implementations for date range filtering using DateInput or similar
    dt_input_target = django_filters.DateFromToRangeFilter(
        field_name="dt_input_target",
        label="Input Date Range (Target)",
        widget=RangeWidget(attrs={"type": "date"}),
    )
    dt_input_actual = django_filters.DateFromToRangeFilter(
        field_name="dt_input_actual",
        label="Input Date Range (Actual)",
        widget=RangeWidget(attrs={"type": "date"}),
    )
    dt_induction_target = django_filters.DateFromToRangeFilter(
        field_name="dt_induction_target",
        label="Induction Date Range (Target)",
        widget=RangeWidget(attrs={"type": "date"}),
    )
    dt_induction_actual = django_filters.DateFromToRangeFilter(
        field_name="dt_induction_actual",
        label="Induction Date Range (Actual)",
        widget=RangeWidget(attrs={"type": "date"}),
    )
    dt_shipment_target = django_filters.DateFromToRangeFilter(
        field_name="dt_shipment_target",
        label="Shipment Date Range (Target)",
        widget=RangeWidget(attrs={"type": "date"}),
    )
    dt_shipment_actual = django_filters.DateFromToRangeFilter(
        field_name="dt_shipment_actual",
        label="Shipment Date Range (Actual)",
        widget=RangeWidget(attrs={"type": "date"}),
    )

    class Meta:
        model = models.SalesModel
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(uuid__iexact=value)
            | Q(esn__icontains=value)
            | Q(customer__icontains=value)
            | Q(status__icontains=value)
            | Q(engine_type__icontains=value)
            | Q(program_type__icontains=value)
            | Q(salesperson__icontains=value)
            | Q(bid_status__icontains=value)
            | Q(facility__icontains=value)
        )
