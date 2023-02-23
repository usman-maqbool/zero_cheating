from django.contrib import admin

# Register your models here.
from business_site.models import BusinessHourRequest, ExpertRating

admin.site.register(BusinessHourRequest)
admin.site.register(ExpertRating)
