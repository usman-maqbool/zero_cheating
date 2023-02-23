from django_filters import rest_framework as filters, DateFilter,CharFilter
from dashboard.models import TimeLog
from site_admin.models import AgreedEngagement


class AdminTimeLogFilters(filters.FilterSet):
    start_date = DateFilter(field_name='date', lookup_expr='gte')
    end_date = DateFilter(field_name='date', lookup_expr='lte')
    client = CharFilter(field_name='engagement__business__name', lookup_expr='contains')
    expert = CharFilter(field_name='expert__name', lookup_expr='contains')

    class Meta:
        model = TimeLog
        fields = ['engagement__business__name', 'expert__name', 'date']


class EngagementFilters(filters.FilterSet):
    start_date = DateFilter(field_name='agreement_start_date', lookup_expr='gte')
    end_date = DateFilter(field_name='agreement_start_date', lookup_expr='lte')
    client = CharFilter(field_name='business_id')
    engagement = CharFilter(field_name='id')

    class Meta:
        model = AgreedEngagement
        fields = ['business_id', 'agreement_start_date', 'agreement_end_date', 'description']
