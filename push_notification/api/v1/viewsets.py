import json

from django.db.models import Count, Case, When, Value
from fcm_django.api.rest_framework import FCMDeviceSerializer
from fcm_django.models import FCMDevice
from rest_framework.generics import *
from rest_framework import status, viewsets
from rest_framework import authentication, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dashboard.utils import DefaultListPagination
from push_notification.api.v1.serializers import UserNotificationSerializer, PushNotificationSerializer
from push_notification.models import Notification, PushNotification
from site_admin.notifications import push_notification_to_expert
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from home.tasks import send_email_notification
from users.models import User


class UserFCMDeviceAdd(CreateAPIView):
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = FCMDevice.objects.all()
    serializer_class = FCMDeviceSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, active=True)

    def create(self, request, *args, **kwargs):
        registration_id = request.data.get('registration_id')
        user_device = FCMDevice.objects.filter(user=request.user, registration_id=registration_id)
        if user_device:
            return Response({
                'success': True,
                'message': 'Device Already Exist'
            }, status=200)
        else:
            return super(UserFCMDeviceAdd, self).create(request, *args, **kwargs)


class UserNotifications(viewsets.ModelViewSet):
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all().order_by('-id')

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):

        if self.request.user.user_type == "Admin":
            unread = self.get_queryset().filter(read=False).count()
            notification = self.get_queryset().values()
        else:
            unread = self.get_queryset().filter(read=False).exclude(title__endswith=' Signup').count()
            notification = self.get_queryset().exclude(title__endswith=' Signup').values()

        data = {
            'unread': unread,
            'notification': notification,
        }
        return Response(data)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        read = request.data.get('read')
        obj.read = read
        obj.save()
        ns = Notification.objects.filter(user=self.request.user).order_by('-id')

        if self.request.user.user_type == "Admin":
            unread = ns.filter(read=False).count()
            notification = ns.values()
        else:
            unread = ns.filter(read=False).exclude(title__endswith=' Signup').count()
            notification = ns.exclude(title__endswith=' Signup').values()

        data = {
            'unread': unread,
            'notification': notification,
        }
        return Response(data)


class PushNotificationViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PushNotificationSerializer
    pagination_class = DefaultListPagination
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = PushNotification.objects.select_related('user').all().order_by('-id')

    def list(self, request, *args, **kwargs):
        if self.queryset.exists():
            page = self.paginate_queryset(self.queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        message = request.data.get('message')

        notification_type = request.data.get('notification_type')
        title = request.data.get('title')
        expert_q = request.data.get('expert_q')
        scheduled_time = request.data.get('scheduled_time')
        expert_id = request.data.get('experts')
        data = {
            "user": self.request.user.id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "expert_q": expert_q
        }
        if notification_type == "Scheduled":
            data.update({"scheduled_time": scheduled_time})
        if expert_q == "Selected User":
            experts = request.data.get('experts')
            data.update({"experts": experts})
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            if notification_type == "Send_Now":
                push_notification_to_expert(data, request.get_host())

            if notification_type == "Scheduled":
                schedule, created = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.SECONDS)

                PeriodicTask.objects.create(interval=schedule, name=title,
                                            task='home.tasks.send_notification_expert',
                                            kwargs=json.dumps({"schedule_time": scheduled_time,
                                                               "request": request.get_host()}),
                                            start_time=scheduled_time, one_off=True)

            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
