from pkg_resources import _
from rest_framework import serializers
from dashboard.models import Refer, TimeLog, Upsell, Education, Resources, Benefits
from site_admin.models import AgreedEngagement
from users.models import User, Profile
from home.api.v1.serializers import BillingPeriodSerializer, UserSerializer


class ReferSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = Refer
        fields = '__all__'


class EngagementListSerializer(serializers.ModelSerializer):
    expert_name = serializers.PrimaryKeyRelatedField(source='expert.name', read_only=True, required=False)
    business_name = serializers.PrimaryKeyRelatedField(source='business.name', read_only=True, required=False)
    business_user = UserSerializer(source='business', read_only=True)

    class Meta:
        model = AgreedEngagement
        fields = '__all__'


class TimeLogSerializer(serializers.ModelSerializer):
    expert_name = serializers.PrimaryKeyRelatedField(source='expert.name', read_only=True, required=False)
    expert = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # engagement = serializers.PrimaryKeyRelatedField(queryset=AgreedEngagement.objects.all(), required=True)
    period_detail = BillingPeriodSerializer(source="period", read_only=True)
    description = serializers.CharField(required=True, error_messages={"blank": "This Field is required"})
    company = serializers.CharField(read_only=True)

    class Meta:
        model = TimeLog
        fields = '__all__'

    def validate_engagement(self, value):
        if not value:
            raise serializers.ValidationError('This Field is required')
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['user_engagement'] = EngagementListSerializer(instance.engagement).data
        return rep


class EngagementTimeLogSerializer(serializers.ModelSerializer):
    expert_name = serializers.PrimaryKeyRelatedField(source='expert.name', read_only=True, required=False)

    class Meta:
        model = TimeLog
        fields = '__all__'


class EngagementHistory(serializers.ModelSerializer):
    class Meta:
        model = TimeLog
        fields = ['expert']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['expert_engagement'] = EngagementListSerializer(instance.engagement).data
        rep['rate'] = Profile.objects.filter(user=instance.expert).first().hourly_rate
        return rep


class UpsellSerializer(serializers.ModelSerializer):
    expert = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    class Meta:
        model = Upsell
        fields = '__all__'


class EducationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Education
        fields = '__all__'


class ResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resources
        fields = '__all__'


class BenefitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefits
        fields = '__all__'
