from django_filters import rest_framework as filters, DateFilter, CharFilter
from .models import TimeLog


class TimeLogFilters(filters.FilterSet):
    start_date = DateFilter(field_name='date', lookup_expr='gte')
    end_date = DateFilter(field_name='date', lookup_expr='lte')
    engagement = CharFilter(field_name='engagement_id')
    hour = CharFilter(field_name='hour')
    minute = CharFilter(field_name='minute')

    class Meta:
        model = TimeLog
        fields = ['date', 'engagement__business_id', 'engagement_id', 'hour', 'minute']
