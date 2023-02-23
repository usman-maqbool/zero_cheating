from django.contrib import admin

# Register your models here.
from push_notification.models import Notification, PushNotification

admin.site.register(Notification)
admin.site.register(PushNotification)
