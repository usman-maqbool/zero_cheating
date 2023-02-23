

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from allauth.account.views import confirm_email
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # path("", include("home.urls")),
    path("accounts/", include("allauth.urls")),
    path("modules/", include("modules.urls")),
    # path("api/v1/", include("home.api.v1.urls")),
    # path("api/v1/", include("dashboard.api.v1.urls")),
    # path("api/v1/", include("business_site.api.v1.urls")),
    # path("api/v1/", include("site_admin.api.v1.urls")),
    # path("api/v1/", include("push_notification.api.v1.urls")),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("rest-auth/", include("rest_auth.urls")),
    # Override email confirm to use allauth's HTML view instead of rest_auth's API view
    path("rest-auth/registration/account-confirm-email/<str:key>/", confirm_email),
    path("rest-auth/registration/", include("rest_auth.registration.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
admin.site.site_header = "zero_cheating"
admin.site.site_title = "zero_cheating Admin Portal"
admin.site.index_title = "zero_cheating Admin"

# swagger
api_info = openapi.Info(
    title="zero_cheating API",
    default_version="v1",
    description="API documentation for zero_cheating App",
)

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

urlpatterns += [
    path("api-docs/", schema_view.with_ui("swagger", cache_timeout=0), name="api_docs")
]


urlpatterns += [
    path("", TemplateView.as_view(template_name='index.html')),
    path("firebase-messaging-sw.js", TemplateView.as_view(template_name="firebase-messaging-sw.js",
        content_type='application/javascript'))
]
urlpatterns += [re_path(r"^(?:.*)/?$",
                TemplateView.as_view(template_name='index.html'))]
