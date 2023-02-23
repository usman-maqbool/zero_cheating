import requests
from datetime import datetime, timedelta
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from rest_auth.registration.views import RegisterView
from rest_framework import status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ViewSet, ReadOnlyModelViewSet
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.models import SocialAccount
from rest_framework.decorators import action
from home.models import Feedback, UserSetting
from home.notifications import feedback_notification, feedback_reply_notification
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from site_admin.models import AgreedEngagement
from users.models import Profile, UserExpertise, BusinessProfile, IndustryExperience, Expertise, Industry
from modules.privacy_policy.models import PrivacyPolicy
from modules.terms_and_conditions.models import TermAndCondition
from django_rest_passwordreset.views import ResetPasswordConfirm
from django_rest_passwordreset.signals import pre_password_reset, post_password_reset
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import exceptions
from django_rest_passwordreset.models import ResetPasswordToken
from django.utils.http import urlsafe_base64_decode
from allauth.account.models import EmailAddress
from home.api.v1.serializers import (
    UserSerializer,
    UpdateUserSerializer,
    RestSocialLoginSerializer,
    UserProfileSerializer,
    FeedbackSerializer,
    GetUserProfileSerializer,
    AdminFeedbackReplySerializer,
    BusinessProfileSerializer, AppliedExpertiesSerializer, BillingPeriodSerializer, UserSettingSerializer,
    IndustryExperienceSerializer, IndustrySerializer
)
from users.models import User
from home.models import BillingPeriods
from growtal_35169.settings import LINKEDIN_REDIRECT_URL_FRONTEND
from home.notifications import profile_notification_admin, feedback_reply_notification
from django.conf import settings
from django.db.models import Value, CharField, F, Q, Min, Max
from home.tasks import send_email_notification
from rest_framework.views import APIView


def save_image_from_url(model, url, name):
    r = requests.get(url)
    if r.status_code == 200:
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(r.content)
        img_temp.flush()
        model.name = name
        model.profile_picture.save("{}.jpg".format(model.username), File(img_temp), save=True)


def get_user_profile(user_id, user_type, req):
    if user_type == 'Expert':
        profile = Profile.objects.filter(user_id=user_id).first()
        user_profile = False if not profile else (
            GetUserProfileSerializer(profile, many=False, context={"request": req})).data
        return user_profile
    if user_type == 'Business':
        profile = BusinessProfile.objects.filter(user_id=user_id).first()
        business_profile = False if not profile else (
            BusinessProfileSerializer(profile, many=False, context={"request": req})).data
        return business_profile
    if user_type == 'Admin':
        return False


# def getLinkedInProfileImage(request):
#     r = requests.get(
#         url='https://api.linkedin.com/v2/me?projection=(id,profilePicture('
#             'displayImage~:playableStreams))&oauth2_access_token={}'.format(
#                 request.data.get("access_token")))
#     if r.status_code == 200:
#         res = r.json()
#         return res['profilePicture']['displayImage~']['elements'][1]['identifiers'][0]['identifier']
#     return 'request_failed'
#
#
# def generate_access_token(code):
#     linkedin_data = SocialApp.objects.filter(provider__contains='linkedin').first()
#     main_url = 'https://www.linkedin.com/oauth/v2/accessToken?client_id={}&client_secret={}&grant_type=authorization_code&redirect_uri={}&code={}'
#     client_id = linkedin_data.client_id
#     client_secret = linkedin_data.secret
#     redirect_uri = LINKEDIN_REDIRECT_URL_FRONTEND
#     code = code
#     access_request = requests.get(url=main_url.format(client_id, client_secret, redirect_uri, code))
#     if access_request.status_code == 200:
#         pass
#     return 'request_failed'


class SignupViewSet(RegisterView):
    pass


class LoginViewSet(ViewSet):
    """Based on rest_framework.authtoken.views.ObtainAuthToken"""

    serializer_class = AuthTokenSerializer

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user_email = request.data.get('username')
        confirmed_email = EmailAddress.objects.filter(email__exact=user_email, verified=True)
        if not confirmed_email:
            return Response(
                # {'non_field_errors': ['Kindly verify your email address']},
                {'non_field_errors': ['First you have to activate your account. Instructions on how to activate your account have been emailed to you. Please check your email.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.approve:
            return Response(
                {'non_field_errors': [
                    'Your account needs to be approved, please wait for account approval.\n This can take up to 24 hours. If you have any questions, please contact support@growtal.com.  '
                ]},
                status=status.HTTP_400_BAD_REQUEST
            )
        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserSerializer(user, context={'request': request})
        user_profile = get_user_profile(user.id, user.user_type, self.request)
        return Response({"token": token.key, "user": user_serializer.data, "profile": user_profile})


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = SocialLoginSerializer
    client_class = OAuth2Client
    permission_classes = [AllowAny, ]
    callback_url = "https://developers.google.com/oauthplayground"

    def get_response(self):
        serializer_class = self.get_response_serializer()
        user = self.user
        if not user.approve:
            user.approve = True
            user.save()
        if not user.user_type:
            user.user_type = self.request.data.get('user_type')
            user.save()
        user_extra_data = SocialAccount.objects.filter(user=self.request.user,
                                                       provider__contains='google').first().extra_data
        name = user_extra_data["name"]
        profile_image_url = user_extra_data["picture"]
        if not user.profile_picture:
            save_image_from_url(user, profile_image_url, name)
        user_detail = UserSerializer(user, many=False, context={"request": self.request})
        serializer = serializer_class(instance=self.token, context={'request': self.request})
        resp = serializer.data
        if not user_detail.data.get('approve'):
            return Response(
                {'non_field_errors': ['Your account needs to be approved, please wait for account approval. This can take up to 24 hours \n If you have any questions, please contact support@growtal.com. ']},
                status=status.HTTP_400_BAD_REQUEST
            )
        resp["token"] = resp["key"]
        resp.pop("key")
        resp["user"] = user_detail.data
        profile = Profile.objects.filter(user_id=user_detail.data.get('id')).first()
        resp['profile'] = False if not profile else (
            GetUserProfileSerializer(profile, many=False, context={"request": self.request})).data
        response = Response(resp, status=status.HTTP_200_OK)
        return response


class AppleLogin(SocialLoginView):
    authentication_classes = []
    permission_classes = [AllowAny]
    adapter_class = AppleOAuth2Adapter
    serializer_class = RestSocialLoginSerializer

    def get_response(self):
        serializer_class = self.get_response_serializer()
        user = self.user
        if not user.approve:
            user.approve = True
            user.save()
        if not user.user_type:
            user.user_type = self.request.data.get('user_type')
            user.save()
        user_detail = UserSerializer(user, many=False, context={'request': self.request})
        serializer = serializer_class(instance=self.token, context={'request': self.request})
        resp = serializer.data
        if not user_detail.data.get('approve'):
            return Response(
                {'non_field_errors': 'There is not an account registered with the email on your social account. \n Please contact support@growtal.com for further instructions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        resp["token"] = resp["key"]
        resp.pop("key")
        resp["user"] = user_detail.data
        profile = Profile.objects.filter(user_id=user_detail.data.get('id')).values()
        resp['profile'] = False if not profile else profile[0]
        response = Response(resp, status=status.HTTP_200_OK)
        return response


class LinkedinLogin(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter
    serializer_class = SocialLoginSerializer
    permission_classes = [AllowAny]
    client_class = OAuth2Client
    callback_url = LINKEDIN_REDIRECT_URL_FRONTEND

    def get_response(self):
        serializer_class = self.get_response_serializer()
        user = self.user
        if not user.user_type:
            user.user_type = self.request.data.get('user_type')
            user.save()
        if not user.approve:
            user.approve = True
            user.save()
        user_detail = UserSerializer(user, many=False, context={'request': self.request})
        serializer = serializer_class(instance=self.token, context={'request': self.request})
        resp = serializer.data
        user_extra_data = SocialAccount.objects.filter(user=self.request.user,
                                                       provider__contains='linkedin').first().extra_data
        if not user.name:
            name = user_extra_data['firstName']['localized']['en_US'] if not user.name else user.name
            user.name = name
            user.save()
            # if not user.profile_picture:
            # token = generate_access_token(self.request.data.get('code'))
            # # if token
            # image_url = getLinkedInProfileImage(self.request)
            name = user_extra_data['firstName']['localized']['en_US'] if not user.name else user.name
            # if image_url != 'request_failed':
            #     save_image_from_url(user, image_url, name)
        if not user_detail.data.get('approve'):
            return Response(
                {'non_field_errors': ['Your account needs to be approved, please wait for account approval. This can take up to 24 hours \n If you have any questions, please contact support@growtal.com. ']},
                status=status.HTTP_400_BAD_REQUEST
            )
        resp["token"] = resp["key"]
        resp.pop("key")
        resp["user"] = user_detail.data
        profile = Profile.objects.filter(user_id=user_detail.data.get('id')).first()
        resp['profile'] = False if not profile else (
            GetUserProfileSerializer(profile, many=False, context={"request": self.request})).data
        response = Response(resp, status=status.HTTP_200_OK)
        return response


class UpdateUserViewset(ModelViewSet):
    serializer_class = UpdateUserSerializer
    http_method_names = ['get', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(id=self.request.user.id)
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileViewset(ModelViewSet):
    serializer_class = UserProfileSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type in ['Admin']:
            return Profile.objects.select_related('user').all()
        queryset = Profile.objects.filter(user_id=self.request.user.id)
        return queryset

    def list(self, request, *args, **kwargs):
        user_profile = self.get_queryset()
        if user_profile:
            serializer = UserProfileSerializer(user_profile.first(), many=False, context={"request": self.request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        data = self.request.data
        user_expertise = request.data.pop('expertise')
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            instance = serializer.instance
            if user_expertise:
                for expertise in user_expertise:
                    UserExpertise.objects.create(expertise_id=expertise, profile=instance)
            user_detail = UserSerializer(self.request.user, many=False, context={"request": self.request})
            data = {
                "user": user_detail.data,
                'profile': serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        user_serializer = UpdateUserSerializer(data=request.data, partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.update(self.request.user, user_serializer.validated_data)
        serializer = self.serializer_class(self.get_object(), data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        user_detail = UserSerializer(self.request.user, many=False, context={"request": self.request})
        profile_detail = UserProfileSerializer(self.get_object(), many=False, context={"request": self.request})
        data = {
            "user": user_detail.data,
            'profile': profile_detail.data
        }
        return Response(data, status=status.HTTP_200_OK)


class BusinessProfileViewset(ModelViewSet):
    serializer_class = BusinessProfileSerializer
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type in ['Admin']:
            return BusinessProfile.objects.all()
        queryset = BusinessProfile.objects.filter(user_id=self.request.user.id)
        return queryset

    def list(self, request, *args, **kwargs):
        business_profile = self.get_queryset()
        if business_profile:
            serializer = BusinessProfileSerializer(business_profile.first(), many=False,
                                                   context={"request": self.request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PrivacyPolicyViewset(ViewSet):
    permission_classes = [AllowAny, ]

    def list(self, request, *args, **kwargs):
        privacy_policy = PrivacyPolicy.objects.filter(is_active=True).first()
        return Response({"privacy_policy": privacy_policy and privacy_policy.body or "" })


class TermsAndConditionsViewset(ViewSet):
    permission_classes = [AllowAny, ]

    def list(self, request, *args, **kwargs):
        terms_and_condition = TermAndCondition.objects.filter(is_active=True).first()
        return Response({"terms_and_condition": terms_and_condition and terms_and_condition.body or ""})


class FeedbackViewset(ModelViewSet):
    serializer_class = FeedbackSerializer
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        admin = User.objects.filter(user_type='Admin', notification_email=True)
        for i in admin:
            if i.email:
                title = "description"
                send_email_notification.delay(title=title, name=self.request.user.name, email=i.email,
                                              subject="Feedback Response", request=request.get_host(),
                                              receiver=i.name, txt_template='feedback.html',
                                              html_template='feedback.txt')
        feedback_notification(serializer.instance.user.name)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomResetPasswordConfirm(ResetPasswordConfirm):

    def post(self, request, *args, **kwargs):
        enc_token = request.data.get('token')
        simple_toke = (urlsafe_base64_decode(enc_token)).decode()
        data = {
            'token': simple_toke,
            'password': request.data.get('password')
        }
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        token = serializer.validated_data['token']

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        # change users password (if we got to this code it means that the user is_active)
        if reset_password_token.user.eligible_for_reset():
            pre_password_reset.send(sender=self.__class__, user=reset_password_token.user)
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_token.user,
                    password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
                )
            except ValidationError as e:
                # raise a validation error for the serializer
                raise exceptions.ValidationError({
                    'password': e.messages
                })

            reset_password_token.user.set_password(password)
            reset_password_token.user.save()
            post_password_reset.send(sender=self.__class__, user=reset_password_token.user)

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()

        return Response({'status': 'OK'})


class GetExpertiseViewset(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        data = Expertise.objects.all()
        expertise = []
        for i in data:
            expertise.append({"value": i.id, "label": i.name})
        data = {
            'user_expertise': expertise,
        }
        return Response(data)


class ApproveProfile(ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']
    serializer_class = UserSerializer
    queryset = User.objects.filter(approve=False, user_type='Admin').order_by('-id')

    def get_queryset(self):
        return self.queryset.exclude(user_type='Admin')


class AdminFeedback(ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    queryset = Feedback.objects.select_related('user').all().order_by('-id')

    # def get_queryset(self):
    #     return self.queryset.filter(feedback_reply=False)


class AdminFeedbackReply(ModelViewSet):
    serializer_class = AdminFeedbackReplySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        feedback = Feedback.objects.filter(id=serializer.instance.feedback.id).first()
        feedback.feedback_reply = True
        feedback.save()
        user = serializer.instance.feedback.user
        user_id = serializer.instance.feedback.user.id
        user_email = serializer.instance.feedback.user.email
        feedback_reply_notification(user_id)
        send_email_notification.delay(title=" {description } Reply", name=user.name, email=user_email,
                                      subject=serializer.instance.feedback.subject, reply=serializer.instance.reply,
                                      request=request.get_host(),
                                      html_template="admin_feedback_reply.html", txt_template="admin_feedback_text.txt")

        return Response(serializer.data, status=status.HTTP_200_OK)


class MyClients(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        engagement = AgreedEngagement.objects.filter(expert=self.request.user)
        business_user = []
        if engagement:
            for x in engagement.distinct("business"):
                company = BusinessProfile.objects.filter(user=x.business).first()
                business_user.append({'value': x.business.id,
                                      'label': company and company.company_name or ""})
        return Response(business_user, status=status.HTTP_200_OK)


class MyEngagements(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        engagement = AgreedEngagement.objects.filter(expert=self.request.user)
        engagements = []
        if engagement:
            for x in engagement:
                engagements.append({'value': x.id,
                                    'label': x.description})
        return Response(engagements, status=status.HTTP_200_OK)


class MyExperts(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        engagement = AgreedEngagement.objects.filter(business=self.request.user)
        business_user = {}
        if engagement:
            for x in engagement:
                business_user[x.expert.id] = x.expert.name
        return Response(business_user, status=status.HTTP_200_OK)


class UserContracts(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        API_KEY = settings.HELLO_SIGN_API_KEY
        HELLO_SIGN_BASE_URL = f"https://{API_KEY}:@api.hellosign.com/v3/"
        params = {
            "query": f"to:{self.request.user.email} AND complete:true",
            "account_id": "all"
        }
        response = requests.get(f"{HELLO_SIGN_BASE_URL}/signature_request/list", params=params)
        if response.status_code == 200:
            # do a check here to ensure that we got 200 status code and there are contracts in reponse. empty list will throw error during indexing.
            if len(response.json()['signature_requests']) != 0:
                signature_request_id = response.json()['signature_requests'][0]['signature_request_id']
                params = {
                    "get_url": True,
                    "file_type": "pdf"
                }
                response = requests.get(f"{HELLO_SIGN_BASE_URL}/signature_request/files/{signature_request_id}",
                                        params=params)
                '''
                file request api call will contain file_url and expires_at. Return file_url to fronted end.
                '''
                return Response({"data": response.json()}, status=status.HTTP_200_OK)
            else:
                return Response({'data': False})
        return Response({'data': False})


class ListIndustryExperiences(ModelViewSet):
    serializer_class = IndustrySerializer
    permission_classes = [IsAuthenticated]
    queryset = Industry.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})


class ApplyExpetieseViewset(ModelViewSet):
    serializer_class = AppliedExpertiesSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        request_user = self.request.user
        expertise = request.data.get("experties")
        industry = request.data.get("industry_type")
        profile = request.data.get("profile")
        expertises = ""
        industries = ""
        if expertise:
            expertises = UserExpertise.objects.create(profile_id=profile, expertise_id=expertise)
        if industry:
            industries = IndustryExperience.objects.create(industry_id=industry, profile_id=profile)
        user = User.objects.filter(user_type='Admin', notification_email=True)
        if expertise or industries:
            profile_notification_admin(request_user)
            for i in user:
                if i.email:
                    send_email_notification.delay(title="Add Area Of Expertise", subject="Expertise Requested",
                                                  name=request_user.name,
                                                  email=i.email, request=request.get_host(),
                                                  expertise=expertises.expertise.name if expertises else "",
                                                  industries=industries.industry.name if industries else "",
                                                  txt_template='area_expertise.txt',
                                                  html_template='area_expertise.html')
            return Response({"msg": "Successfully Applied"}, status=200)
        else:
            return Response({"msg": "please select industry or expertise"}, status=400)
    # return serializer.errors(serializer.errors, status=400)


class BillingPeriodViewSet(ModelViewSet):
    serializer_class = BillingPeriodSerializer
    queryset = BillingPeriods.objects.all().order_by('id')


    @action(detail=False, methods=['get'])
    def billing_filters(self, request):
        queryset = self.get_queryset()
        begin_date = queryset.aggregate(begin=Min('start_date'))
        finish_date = queryset.aggregate(finish=Max('end_date'))

        begin_date = begin_date['begin'] - timedelta(begin_date['begin'].weekday())   # start from monday
        finish_date = finish_date['finish'] + timedelta(6 - finish_date['finish'].weekday())  # end on sunday

        filters_date = {}

        while begin_date < finish_date:
            first_date = datetime.strftime(begin_date, '%Y-%m-%d')
            begin_date = begin_date + timedelta(days=6)
            filters_date[f"{first_date} to {datetime.strftime(begin_date, '%Y-%m-%d')}"] = [first_date,datetime.strftime(begin_date, '%Y-%m-%d')]
            begin_date = begin_date + timedelta(days=1)


        return Response(filters_date, status=200)

class AllUserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        expert = self.request.query_params.get('expert')
        business = self.request.query_params.get('business')
        queryset = self.queryset
        if expert and business:
            queryset = queryset.filter(Q(user_type=expert) | Q(user_type=business)).order_by('-id')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})



class AllExpertViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.filter(user_type="Expert")


class UserSettingViewSet(ModelViewSet):
    serializer_class = UserSettingSerializer
    queryset = UserSetting.objects.all().order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            instance = serializer.instance
            user = User.objects.filter(id=instance.user.id).first()
            user.notification_app = instance.app
            user.notification_email = instance.email
            user.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class ExpertiseIndustryViewSet(APIView):
    def post(self, request):
        expertise = self.request.data.get('expertise')
        industry = self.request.data.get('industry')
        expert = self.request.data.get('expert')
        if expertise:
            expert_data = UserExpertise.objects.filter(id=int(expertise)).first()
            if expert_data:
                expert_data.delete()
        if industry:
            experience = IndustryExperience.objects.filter(id=industry).first()
            if experience:
                experience.delete()
        if expert:
            profile = Profile.objects.filter(id=expert).first()
            if profile:
                serializer = UserProfileSerializer(profile)
                return Response(serializer.data)

        return Response({"Message": "Remove Successfully"})


class ExpertProfileViewSet(ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(user_type="Expert")

    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        search = self.request.query_params.get('search')
        # if search:
        #     queryset = queryset.filter(company_name__icontains=search)
        company = []
        for user in queryset:
            data = {
                "value": user.id,
                "label": user.name
            }
            company.append(data)
        return Response(company)



