from rest_framework import serializers
from business_site.models import BusinessHourRequest, ExpertRating
from dashboard.models import Engagements
from site_admin.models import AgreedEngagement
from users.models import User, UserExpertise, BusinessProfile, Expertise
from site_admin.models import EndingEngagementRequest
from home.api.v1.serializers import UserSerializer, UserExpertiseSErializer
from site_admin.api.v1.serializers import AgreedEngagementSerializer


class RequestEngagementSerializer(serializers.ModelSerializer):
    ended = serializers.BooleanField(required=False)
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Engagements
        fields = '__all__'


class RequestHourSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='engagement.business.name', read_only=True)
    engagement_name = serializers.CharField(source='engagement.description', read_only=True)
    engagement_detail = AgreedEngagementSerializer(source='engagement', read_only=True)
    increase_hour = serializers.CharField(required=True, allow_null=False, allow_blank=False)

    class Meta:
        model = BusinessHourRequest
        fields = '__all__'
        # extra_kwargs = {
        #     "increase_hour": {
        #         "required": True,
        #         "allow_null": False
        #     }
        # }

    def validate_hours(self, value):
        if not value:
            raise serializers.ValidationError('hours value may not be 0')
        return value


class ExpertRatingSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(
        required=True, error_messages={
            "required": "please select valid rating",
            "null": "please select valid rating",
            "blank": "please select valid rating",
            'invalid': 'please select valid rating.'
        })

    class Meta:
        model = ExpertRating
        fields = '__all__'


class ExpertSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'profile_picture']


class MyTeamsSerializer(serializers.ModelSerializer):
    expert = ExpertSerializer(many=False, required=False)

    class Meta:
        model = AgreedEngagement
        fields = "__all__"

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['rating'] = instance.expert.get_avg_rating
        expert = UserExpertise.objects.filter(profile__user=instance.expert).values()
        name = []
        res['expertise'] = name
        for i in expert:
            expertise = Expertise.objects.filter(id=i['expertise_id']).first()
            if expertise:
                data = {
                    "id": i['expertise_id'],
                    "name": expertise.name,
                    "profile_id": i['profile_id']
                }
                name.append(data)
        return res


class EndingEngagementSerializer(serializers.ModelSerializer):

    class Meta:
        model = EndingEngagementRequest
        fields = ["id", "description", "agreed_engagement", "user"]


class BillingHistorySerilzier(serializers.ModelSerializer):
    total_hours = serializers.IntegerField(required=False)
    expert_name = serializers.CharField(source='expert.name', read_only=True)
    billing_start_date = serializers.DateField(required=False)
    billing_end_date = serializers.DateField(required=False)
    company = serializers.CharField(read_only=True)

    class Meta:
        model = AgreedEngagement
        fields = "__all__"


class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = "__all__"