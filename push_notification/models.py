from django.db import models
import jsonfield
# Create your models here.
from users.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notification')
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=500)
    read = models.BooleanField(default=False)
    data = jsonfield.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PushNotification(models.Model):
    SEND_NOW = 1
    SCHEDULED = 2

    NOTIFICATION_TYPE = (
        ('Send_Now', 'Send_Now'),
        ('Scheduled', 'Scheduled')
    )
    EXPERT_STATUS = [
        ('All Expert', 'All Expert'),
        ('All Business', 'All Business'),
        ('Selected User', 'Selected User'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_push_notification')
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=500)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    experts = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now=True)
    expert_q = models.CharField(max_length=255, choices=EXPERT_STATUS, null=True, blank=True)

    def __str__(self):
        return self.title


@receiver(post_save, sender=Notification)
def send_push_notification(sender, instance, **kwargs):
    from fcm_django.models import FCMDevice
    devices = FCMDevice.objects.filter(user=instance.user,user__notification_app=True)
    message = instance.message
    title = instance.title
    for device in devices:
        device.send_message(title=title, body=message, data={}, sound=True)
