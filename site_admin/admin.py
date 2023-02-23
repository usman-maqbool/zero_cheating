from django.contrib import admin

# Register your models here.
from .models import ExpertRequest, AgreedEngagement, EndingEngagementRequest
admin.site.register(ExpertRequest)
admin.site.register(AgreedEngagement)
admin.site.register(EndingEngagementRequest)
