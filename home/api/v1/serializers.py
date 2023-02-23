from urllib.error import HTTPError
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from allauth.account import app_settings as allauth_settings
from allauth.account.forms import ResetPasswordForm
from allauth.utils import email_address_exists, generate_unique_username
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from rest_framework import serializers
from rest_auth.serializers import PasswordResetSerializer
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.helpers import complete_social_login
from home.models import Feedback, FeedbackReply
from users.models import Profile, UserExpertise, BusinessProfile, AppliedExperties
from django.utils.translation import gettext_lazy as _
from requests.exceptions import HTTPError
from drf_extra_fields.fields import Base64FileField, Base64ImageField
from home.notifications import signup_notification
User = get_user_model()
from home.models import BillingPeriods, UserSetting
from users.models import IndustryExperience, Expertise, UserExpertise, Industry


class PDFBase64File(Base64FileField):
    ALLOWED_TYPES = ['pdf']

    def get_file_extension(self, filename, decoded_file):
        return 'pdf'


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'user_type')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'style': {
                    'input_type': 'password'
                }
            },
            'email': {
                'required': True,
                'allow_blank': False,
            },
            'name': {
                'required': True,
                'allow_blank': False,
            },
            'user_type': {
                'required': True,
                'allow_blank': False,
            }
        }

    def _get_request(self):
        request = self.context.get('request')
        if request and not isinstance(request, HttpRequest) and hasattr(request, '_request'):
            request = request._request
        return request

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."))
        return email

    def create(self, validated_data):
        user = User(
            email=validated_data.get('email'),
            name=validated_data.get('name'),
            username=generate_unique_username([
                validated_data.get('name'),
                validated_data.get('email'),
                'user'
            ]),
            user_type=validated_data.get('user_type')
        )
        user.set_password(validated_data.get('password'))
        user.approve = True
        user.save()
        request = self._get_request()
        setup_user_email(request, user, [])
        signup_notification(user.name, user.user_type)
        return user

    def save(self, request=None):
        """rest_auth passes request so we must override to accept it"""
        return super().save()


class UpdateUserSerializer(serializers.ModelSerializer):
    profile_picture = Base64ImageField(required=False)
    linkedin_profile_url = serializers.URLField(required=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'user_type', 'linkedin_profile_url', 'profile_picture', 'approve']

    def validate_linkedin_profile_url(self, value):
        base_url_linkedin = 'https://www.linkedin.com/in/'
        if value:
            if base_url_linkedin not in value:
                raise serializers.ValidationError()
        return value


class UserExpertiseSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserExpertise
        fields = "__all__"


class ExpertiseSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="expertise.name", read_only=True, required=False)

    class Meta:
        model = UserExpertise
        fields = ('name',)


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = "__all__"


class IndustryExperienceSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source="industry.name", read_only=True)

    class Meta:
        model = IndustryExperience
        fields = "__all__"


class BusinessProfileSerializer(serializers.ModelSerializer):
    logo = Base64ImageField(required=False)

    class Meta:
        model = BusinessProfile
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['user_name'] = instance.user.name
        return rep


class UserSerializer(serializers.ModelSerializer):
    business_detail = BusinessProfileSerializer(source='business_profile', many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'user_type', 'profile_picture', 'linkedin_profile_url', 'approve',
                  'date_joined', 'notification_email', 'notification_app', 'business_detail']


class GetUserProfileSerializer(serializers.ModelSerializer):
    expertise = ExpertiseSerializer(many=True, required=False)

    class Meta:
        model = Profile
        fields = '__all__'



class PasswordSerializer(PasswordResetSerializer):
    """Custom serializer for rest_auth to solve reset password error"""
    password_reset_form_class = ResetPasswordForm


class RestSocialLoginSerializer(SocialLoginSerializer):
    id_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        view = self.context.get('view')
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _("View is not defined, pass it as a context variable")
            )

        adapter_class = getattr(view, 'adapter_class', None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        # Case 1: We received the access_token
        if attrs.get('access_token'):
            access_token = attrs.get('access_token')

        # Case 2: We received the authorization code
        elif attrs.get('code'):
            self.callback_url = getattr(view, 'callback_url', None)
            self.client_class = getattr(view, 'client_class', None)

            if not self.callback_url:
                raise serializers.ValidationError(
                    _("Define callback_url in view")
                )
            if not self.client_class:
                raise serializers.ValidationError(
                    _("Define client_class in view")
                )

            code = attrs.get('code')

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope
            )
            token = client.get_access_token(code)
            access_token = token['access_token']

        else:
            raise serializers.ValidationError(
                _("Incorrect input. access_token or code is required."))

        social_token = social_token = adapter.parse_token({
            'access_token': access_token,
            'id_token': attrs.get('id_token') # For apple login
        })
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, access_token)
            complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        if not login.is_existing:
            # We have an account already signed up in a different flow
            # with the same email address: raise an exception.
            # This needs to be handled in the frontend. We can not just
            # link up the accounts due to security constraints
            if allauth_settings.UNIQUE_EMAIL:
                # Do we have an account already with this email address?
                account_exists = get_user_model().objects.filter(
                    email=login.user.email,
                ).exists()
                if account_exists:
                    raise serializers.ValidationError(
                        _("User is already registered with this e-mail address.")
                    )

            login.lookup()
            login.save(request, connect=True)

        attrs['user'] = login.account.user

        return attrs


# class CustomSocialLoginSerializer(SocialLoginSerializer):
#     access_token = serializers.CharField(required=False, allow_blank=True)
#     code = serializers.CharField(required=False, allow_blank=True)
#     id_token = serializers.CharField(required=False, allow_blank=True)
#     user_type = serializers.CharField(required=True)
#
#     def validate(self, attrs):
#         view = self.context.get('view')
#         request = self._get_request()
#
#         if not view:
#             raise serializers.ValidationError(
#                 _('View is not defined, pass it as a context variable'),
#             )
#
#         adapter_class = getattr(view, 'adapter_class', None)
#         if not adapter_class:
#             raise serializers.ValidationError(_('Define adapter_class in view'))
#
#         adapter = adapter_class(request)
#         app = adapter.get_provider().get_app(request)
#
#         # More info on code vs access_token
#         # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token
#
#         access_token = attrs.get('access_token')
#         code = attrs.get('code')
#         # Case 1: We received the access_token
#         if access_token:
#             tokens_to_parse = {'access_token': access_token}
#             token = access_token
#             # For sign in with apple
#             id_token = attrs.get('id_token')
#             if id_token:
#                 tokens_to_parse['id_token'] = id_token
#
#         # Case 2: We received the authorization code
#         elif code:
#             self.set_callback_url(view=view, adapter_class=adapter_class)
#             self.client_class = getattr(view, 'client_class', None)
#
#             if not self.client_class:
#                 raise serializers.ValidationError(
#                     _('Define client_class in view'),
#                 )
#
#             provider = adapter.get_provider()
#             scope = provider.get_scope(request)
#             client = self.client_class(
#                 request,
#                 app.client_id,
#                 app.secret,
#                 adapter.access_token_method,
#                 adapter.access_token_url,
#                 self.callback_url,
#                 scope,
#                 scope_delimiter=adapter.scope_delimiter,
#                 headers=adapter.headers,
#                 basic_auth=adapter.basic_auth,
#             )
#             token = client.get_access_token(code)
#             access_token = token['access_token']
#             tokens_to_parse = {'access_token': access_token}
#
#             # If available we add additional data to the dictionary
#             for key in ['refresh_token', 'id_token', adapter.expires_in_key]:
#                 if key in token:
#                     tokens_to_parse[key] = token[key]
#         else:
#             raise serializers.ValidationError(
#                 _('Incorrect input. access_token or code is required.'),
#             )
#
#         social_token = adapter.parse_token(tokens_to_parse)
#         social_token.app = app
#
#         try:
#             login = self.get_social_login(adapter, app, social_token, token)
#             # user_email = login.user.email
#             # if not User.objects.filter(email=user_email):
#             #     raise serializers.ValidationError(
#             #         _('No Account is Registered with Email associated with your Social Account')
#             #     )
#             complete_social_login(request, login)
#         except HTTPError:
#             raise serializers.ValidationError(_('Incorrect value'))
#
#         if not login.is_existing:
#             # We have an account already signed up in a different flow
#             # with the same email address: raise an exception.
#             # This needs to be handled in the frontend. We can not just
#             # link up the accounts due to security constraints
#             if allauth_settings.UNIQUE_EMAIL:
#                 # Do we have an account already with this email address?
#                 account_exists = get_user_model().objects.filter(
#                     email=login.user.email,
#                 ).exists()
#                 if account_exists:
#                     raise serializers.ValidationError(
#                         _('User is already registered with this e-mail address.'),
#                     )
#
#             login.lookup()
#             login.save(request, connect=True)
#         login.account.user.user_type = attrs.get('user_type')
#         login.account.user.save()
#         attrs['user'] = login.account.user
#
#         return attrs


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['user_data'] = UserSerializer(instance.user).data
        return rep


class ApproveUserSerializer(serializers.ModelSerializer):
    user_data = serializers.PrimaryKeyRelatedField(source='user.name', read_only=True, required=False)

    class Meta:
        model = Profile
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['user_data'] = UserSerializer(instance.user).data
        return rep


class AdminFeedbackReplySerializer(serializers.ModelSerializer):

    class Meta:
        model = FeedbackReply
        fields = '__all__'


class AppliedExpertiesSerializer(serializers.ModelSerializer):

    class Meta:
        model = AppliedExperties
        fields = '__all__'


class BillingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingPeriods
        fields = "__all__"


class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = "__all__"


class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = "__all__"


class UserExpertiseSErializer(serializers.ModelSerializer):
    detail = ExpertiseSerializer(source='expertise', read_only=True)

    class Meta:
        model = UserExpertise
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    resume = PDFBase64File(required=False)
    hourly_rate = serializers.FloatField(required=True)
    expert_bio = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user_availability = serializers.IntegerField(required=True)
    expertise = UserExpertiseSErializer(source='profile', many=True, required=False)
    user_detail = UserSerializer(source='user', read_only=True)
    expert_data = UserSerializer(source='user', read_only=True)
    industry_experience = IndustryExperienceSerializer(source='industry_profile', read_only=True, many=True)

    class Meta:
        model = Profile
        fields = '__all__'

    def validate_hourly_rate(self, value):
        if value == 0:
            raise serializers.ValidationError('hourly rate may not be 0')
        return value
