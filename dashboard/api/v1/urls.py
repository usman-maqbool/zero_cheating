from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ReferViewset, TimeLogViewSet, EngagementListViewset, DisclaimerText, EngagementTimeLogs, \
    ExpertEngagements, UpsellViewset, ResourcesViewset, EducationViewset, BenefitsViewset

router = DefaultRouter()
router.register("refer", ReferViewset, basename="refer")
router.register("time_log", TimeLogViewSet, basename="time_log")
router.register("engagement_list", EngagementListViewset, basename="engagement_list")
router.register("upsell_disclaimer", DisclaimerText, basename="upsell_disclaimer")
router.register("engagement_logs", EngagementTimeLogs, basename="engagement_logs")
router.register("expert_engagement", ExpertEngagements, basename="expert_engagement")
router.register("upsell", UpsellViewset, basename="upsell")
router.register("resources", ResourcesViewset, basename="resources")
router.register("education", EducationViewset, basename="education")
router.register("benefits", BenefitsViewset, basename="benefits")

urlpatterns = [
    path("dashboard/", include(router.urls)),
]
