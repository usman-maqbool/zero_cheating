from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import BusinessExpertRequestViewSets, AdminBusinessViewSet, AdminExpertViewSet, ShareExpertWithBusiness, \
    ShareBusinessWithExpertViewSet, AdminTimeTracking, OnBoardUsers, AgreedEngagementViewset, Referrals, \
    OpportunityViewSet, CloseBillingPeriod, HourReminder

router = DefaultRouter()
router.register('expert_request', BusinessExpertRequestViewSets, basename='expert_request')
router.register('admin_business', AdminBusinessViewSet, basename='admin_business')
router.register('admin_expert', AdminExpertViewSet, basename='admin_expert')
router.register('share_expert', ShareExpertWithBusiness, basename='share_expert')
router.register('share_business', ShareBusinessWithExpertViewSet, basename='share_business')
router.register('time_tracking', AdminTimeTracking, basename='time_tracking')
router.register('onboard', OnBoardUsers, basename='onboard')
router.register('new_engagement', AgreedEngagementViewset, basename='new_engagement')
router.register('referrals', Referrals, basename='referrals')
router.register('Opportunity', OpportunityViewSet, basename='Opportunity')

urlpatterns = [
    path("siteadmin/", include(router.urls)),
    path('siteadmin/close_period/', CloseBillingPeriod.as_view(), name='close_period'),
    path('siteadmin/hour_reminder/', HourReminder.as_view(), name='hour_reminder')
]
