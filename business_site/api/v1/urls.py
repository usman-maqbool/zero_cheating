from django.urls import path, include
from rest_framework.routers import DefaultRouter


from business_site.api.v1.viewsets import RequestEngagementViewset, RequestHours, Rating, MyTeams, \
    BusinessContractListing, BusinessContractDownload, EndingEngagementRequest, BillingHistoryViewSet, \
    BusinessProfileViewSet

router = DefaultRouter()
router.register('request_engagement', RequestEngagementViewset, basename='request_engagement')
router.register('request_hours', RequestHours, basename='request_hours')
router.register('my_team', MyTeams, basename='my_team')
router.register('rating', Rating, basename='expert_rating')
router.register('contracts_listing', BusinessContractListing, basename='contracts_listing')
router.register('signed_contract', BusinessContractDownload, basename='signed_contract')
router.register('end_engagement_request', EndingEngagementRequest, basename='user_end_engagement_request')
router.register('billing_history',  BillingHistoryViewSet, basename='billing_history')
router.register('all_business_profile', BusinessProfileViewSet, basename='all_business_profile')

urlpatterns = [
    path("business/", include(router.urls)),
]
