from django.contrib import admin
from .models import Feedback, FeedbackReply, BillingPeriods, UserSetting


# Register your models here.


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'feedback_reply']

    class Meta:
        model = Feedback
        fields = '__all__'


class FeedbackReplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'feedback']

    class Meta:
        model = FeedbackReply
        fields = '__all__'


@admin.register(BillingPeriods)
class BillingPeriodsAdmin(admin.ModelAdmin):
    list_display = ['id', 'start_date', 'end_date', 'is_active']


@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email', 'app']



admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackReply, FeedbackReplyAdmin)
