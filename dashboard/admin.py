from django.contrib import admin
from .models import Refer, TimeLog, Engagements, Resources, Education, Benefits


# Register your models here.


class ReferAdmin(admin.ModelAdmin):
    list_display = ['referral_type', 'name', 'email', 'date']

    class Meta:
        model = Refer
        fields = '__all__'


class TimeLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'hour', 'minute']

    class Meta:
        model = TimeLog
        fields = ['id', 'date', 'hour', 'minute', 'period']


# class EngagementsAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'commitment', 'ended', 'expertise_area']
#
#     class Meta:
#         model = Engagements
#         fields = '__all__'

class ResourcesAdmin(admin.ModelAdmin):
    list_display = ['id', 'details', 'content']

    class Meta:
        model = Resources
        fields = '__all__'


class EducationAdmin(admin.ModelAdmin):
    list_display = ['id', 'details']

    class Meta:
        model = Education
        fields = '__all__'


class BenefitsAdmin(admin.ModelAdmin):
    list_display = ['id', 'details']

    class Meta:
        model = Benefits
        fields = '__all__'


admin.site.register(Refer, ReferAdmin)
admin.site.register(TimeLog, TimeLogAdmin)
admin.site.register(Engagements)
admin.site.register(Resources, ResourcesAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Benefits, BenefitsAdmin)

