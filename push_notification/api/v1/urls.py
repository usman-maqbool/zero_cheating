from django.urls import path, include
from rest_framework.routers import DefaultRouter

from push_notification.api.v1.viewsets import UserFCMDeviceAdd, UserNotifications, PushNotificationViewset

router = DefaultRouter()
router.register('notification_list', UserNotifications, basename='notification_list')
router.register('push_notification', PushNotificationViewset, basename='notification_list')

urlpatterns = [
    path('notification/', include(router.urls)),
    path('user_fcm_device_add/', UserFCMDeviceAdd.as_view(), name='user_fcm_device_add'),
]
