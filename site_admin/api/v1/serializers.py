from rest_framework import serializers

from dashboard.models import TimeLog, Refer
from home.api.v1.serializers import UserSerializer
from site_admin.models import ExpertRequest, AgreedEngagement
from users.models import BusinessProfile, Profile, User
from dashboard.models import Engagements
from home.api.v1.serializers import BillingPeriodSerializer, IndustryExperienceSerializer,  ExpertiseSerializer, \
    UserExpertiseSErializer


class BusinessExpertRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpertRequest
        fields = '__all__'

    def validate_preferred_rate(self, value):
        if value == 0:
            raise serializers.ValidationError('Value may not be 0')
        return value


class AdminBusinessSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessProfile
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['business_data'] = UserSerializer(instance.user).data
        return rep


class AdminExpertSerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(read_only=True)
    expertise = UserExpertiseSErializer(source='profile', many=True, read_only=True)
    industry_experience = IndustryExperienceSerializer(source='industry_profile', read_only=True, many=True)

    class Meta:
        model = Profile
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['expert_data'] = UserSerializer(instance.user).data
        eng_names = TimeLog.objects.select_related('expert', 'engagement').filter(expert=instance.user).order_by('-id')
        rep['engagement_name'] = [] if not eng_names else list(set([x.engagement.description for x in eng_names]))
        return rep


class AdminExpertListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name']


class ShareBusinessWithExpert(serializers.Serializer):
    expert_name = serializers.CharField(required=True)
    expert_email = serializers.EmailField(required=True)
    business_web_url = serializers.URLField(required=True)
    details = serializers.CharField(required=True)
    hourly_rate = serializers.IntegerField(required=True)
    business_name = serializers.CharField(required=True)


class AgreedEngagementSerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(source='expert.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    expert_detail = UserSerializer(source='expert', read_only=True)
    business_detail = UserSerializer(source='business', read_only=True)
    company = serializers.CharField(read_only=True)

    class Meta:
        model = AgreedEngagement
        fields = '__all__'


class AdminTimeLogsSerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(source='expert.name', read_only=True)
    engagement_name = serializers.CharField(source='engagement.description', read_only=True)
    client = serializers.CharField(read_only=True)
    period = BillingPeriodSerializer(read_only=True)
    invoice_rate = serializers.CharField(source='engagement.expert_rate', read_only=True)
    payment_rate = serializers.CharField(source='engagement.business_rate', read_only=True)
    invoice_amount = serializers.CharField(read_only=True)
    payment_amount = serializers.CharField(read_only=True)
    total_invoice = serializers.CharField(read_only=True)
    total_payment = serializers.CharField(read_only=True)
    total_hours = serializers.CharField(read_only=True)
    total_invoice_rate = serializers.CharField(read_only=True)
    total_payment_rate = serializers.CharField(read_only=True)

    class Meta:
        model = TimeLog
        fields = '__all__'


class OnBoardSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField()
    user_type = serializers.CharField()


class EngagementHistorySerializer(serializers.ModelSerializer):
    expert_name = serializers.CharField(source='expert.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    company = serializers.CharField(read_only=True)

    class Meta:
        model = AgreedEngagement
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['time'] = instance.get_time_logs
        return rep


class ReferralsSerializer(serializers.ModelSerializer):
     class Meta:
         model = Refer
         fields = '__all__'
