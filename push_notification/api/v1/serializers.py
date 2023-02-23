from django.contrib.auth import get_user_model
from rest_framework import serializers
from home.api.v1.serializers import UserSerializer

from push_notification.models import Notification, PushNotification

User = get_user_model()

class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class PushNotificationSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    expert_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PushNotification
        fields = '__all__'

    def get_expert_detail(self, obj):
        ids = obj.experts
        return_data = []
        if ids:
            for i in ids.split(","):
                data = User.objects.filter(id=i).first()
                if data:
                    return_data.append({"value": i, "label": data.name})
        return return_data
