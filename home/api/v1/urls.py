from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_auth.views import PasswordChangeView
from django_rest_passwordreset.views import reset_password_confirm
from home.views import SuperUserViewSet
from home.api.v1.viewsets import (
    SignupViewSet,
    LoginViewSet,
    UpdateUserViewset,
    UserProfileViewset,
    GoogleLogin,
    AppleLogin,
    PrivacyPolicyViewset,
    TermsAndConditionsViewset,
    FeedbackViewset,
    LinkedinLogin,
    CustomResetPasswordConfirm,
    GetExpertiseViewset,
    ApproveProfile,
    AdminFeedback, AdminFeedbackReply, BusinessProfileViewset, MyClients, UserContracts, ListIndustryExperiences,
    ApplyExpetieseViewset, MyEngagements,BillingPeriodViewSet, AllUserViewSet, AllExpertViewSet, UserSettingViewSet,
    ExpertiseIndustryViewSet, ExpertProfileViewSet
)

router = DefaultRouter()
# router.register("signup", SignupViewSet.as_view(), basename="signup")
router.register("login", LoginViewSet, basename="login")
router.register("updater_user", UpdateUserViewset, basename="updater_user")
router.register("user_profile", UserProfileViewset, basename="user_profile")
router.register("business_profile", BusinessProfileViewset, basename="user_profile")
router.register("get_expertise", GetExpertiseViewset, basename="get_expertise")
router.register("terms_and_conditions", TermsAndConditionsViewset, basename="terms_and_conditions")
router.register("privacy_policy", PrivacyPolicyViewset, basename="privacy_policy")
router.register("user_feedback", FeedbackViewset, basename="user_feedback")
router.register("superuser", SuperUserViewSet, basename="superuser")
router.register("approve_profile", ApproveProfile, basename="approve_profile")
router.register("admin_feedback", AdminFeedback, basename="admin_feedback")
router.register("admin_feedback_reply", AdminFeedbackReply, basename="admin_feedback_reply")
router.register("my_clients", MyClients, basename="my_clients")
router.register("my_engagements", MyEngagements, basename="my_engagements")
router.register("contract", UserContracts, basename="contract")
router.register("industry_experiences", ListIndustryExperiences, basename="industry_experiences")
router.register("apply_experiences", ApplyExpetieseViewset, basename="apply_experiences")
router.register('billing_periods', BillingPeriodViewSet, basename='billing_period')
router.register('all_user', AllUserViewSet, basename='all_user')
router.register('all_expert', AllExpertViewSet, basename='all_expert')
router.register('user_setting', UserSettingViewSet, basename='user_setting')
router.register('all_expert_profile', ExpertProfileViewSet, basename='all_expert_profile')


urlpatterns = [
    path("", include(router.urls)),
    path("signup/", SignupViewSet.as_view(), name='signup'),
    path("password/change/", PasswordChangeView.as_view(), name='rest_password_change'),
    path("password/reset/confirm/", CustomResetPasswordConfirm.as_view(), name='password_reset_confirm'),
    path("password/reset/", include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('delete_expertise/', ExpertiseIndustryViewSet.as_view(), name='delete_expertise'),
    re_path(r'^login/google/$', GoogleLogin.as_view(), name='google_login'),
    re_path(r'^login/apple/$', AppleLogin.as_view(), name='apple_login'),
    re_path(r'^login/linkedin/$', LinkedinLogin.as_view(), name='linkedin_login'),
    # re_path(r'^login/facebook/$', FacebookLogin.as_view(), name='facebook_login'),
]
