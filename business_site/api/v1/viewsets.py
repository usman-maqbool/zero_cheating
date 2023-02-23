import requests
from django.conf import settings
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, OuterRef, Prefetch, F, Value, CharField, Q
from datetime import datetime, timedelta, date
from home.models import BillingPeriods
from rest_framework.decorators import action
import csv
from datetime import date
from business_site.notifications import accept_reject_requested_hour_notification, expert_request_hours_notification, \
    rating_notification_admin, notification_all_admin

from business_site.api.v1.serializers import RequestEngagementSerializer, RequestHourSerializer, ExpertRatingSerializer, \
    MyTeamsSerializer, BillingHistorySerilzier, BusinessProfileSerializer
from business_site.models import BusinessHourRequest, ExpertRating
from business_site.notifications import business_request_engagements_accept, expert_end_engagement_request_notification, \
    business_request_hours_notification
from dashboard.models import Engagements, TimeLog
from site_admin.models import AgreedEngagement, EndingEngagementRequest
from business_site.api.v1.serializers import EndingEngagementSerializer
from users.models import User, BusinessProfile
today = date.today()

from business_site.tasks import send_email_notification_business


class RequestEngagementViewset(viewsets.ModelViewSet):
    serializer_class = RequestEngagementSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'get', 'patch']
    queryset = Engagements.objects.select_related('user').all().order_by('-id')

    def get_queryset(self):
        queryset = self.queryset.filter(rejected=False)
        queryset = queryset.exclude(rejected=True)
        return queryset

    def create(self, request, *args, **kwargs):
        req_user = self.request.user
        user = User.objects.filter(user_type='Admin')
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            info = serializer.instance.additional_info
            expertise = serializer.instance.expertise_area
            commitment = serializer.instance.commitment
            title = "Add Member"
            message = f"Add additional team member for area of expertise {expertise}"
            notification_all_admin(title, message, req_user, expertise)
            for i in user:
                if i.email:
                    if i.notification_email:
                        send_email_notification_business.delay(title=title, name=self.request.user.name,
                                                               message=message, subject="Engagement Request",
                                                               email=i.email, request=request.get_host(),
                                                               hours=commitment, expertise=expertise,
                                                               description=info,
                                                               html_template="Add_New_Member.html",
                                                               txt_template="Add_New_Member.txt")
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object(), data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        accept = self.request.data.get('accepted', None)
        reject = self.request.data.get('rejected', None)
        instance = self.get_object()

        business_name = instance.user.name
        business_email = instance.user.email
        email = instance.user.notification_email
        if accept:
            request_status = 'accepted'
        if reject:
            request_status = 'rejected'
        if email:
            send_email_notification_business.delay(title="Engagement", name=business_name, email=business_email,
                                                   sender_name=self.request.user.username, status=request_status,
                                                   txt_template="accept_engagement.txt", subject="Engagement Request",
                                                   html_template="accept_engagement.html", request=request.get_host())
        business_request_engagements_accept(instance, request_status)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RequestHours(viewsets.ModelViewSet):
    serializer_class = RequestHourSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'get', 'patch']
    queryset = BusinessHourRequest.objects.select_related('engagement').all().filter(is_show=True).order_by('-id')

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'Business':
            return self.queryset.filter(request_to=user)
        if user.user_type == 'Expert':
            return self.queryset.filter(request_to=user)
        return self.queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        user = self.request.user
        serializer.is_valid(raise_exception=True)
        serializer.save()
        business_name = serializer.instance.engagement.business.name
        business_email = serializer.instance.engagement.business.email
        expert_name = serializer.instance.engagement.expert.name
        expert_email = serializer.instance.engagement.expert.email
        engagement = serializer.instance.engagement.title
        hours = serializer.instance.hours
        increase_hours = serializer.instance.increase_hour
        message = serializer.instance.description
        sender_name = ""
        if user.user_type == "Expert":
            if user.notification_email:
                sender_name = serializer.instance.engagement.expert.name
                send_email_notification_business.delay(title=f"GrowTal: {expert_name} has requested more hours",
                                                       name=business_name, email=business_email,
                                                       sender_name=sender_name, engagement=engagement, hours=hours,
                                                       increase_hour=increase_hours, message=message,
                                                       txt_template="requested_hour.txt", request=request.get_host(),
                                                       subject="Request for Additional Hours",
                                                       html_template="requested_hour.html")
            if user.notification_app:
                expert_request_hours_notification(serializer.instance)
        if user.user_type == 'Business':
            if user.notification_email:
                sender_name = serializer.instance.engagement.business.name
                send_email_notification_business.delay(title="Request Hours", name=expert_name, email=expert_email,
                                                       sender_name=sender_name, subject="Request for Additional Hours",
                                                       engagement=engagement, hours=hours,
                                                       increase_hour=increase_hours, message=message,
                                                       txt_template="requested_hour.txt", request=request.get_host(),
                                                       html_template="requested_hour.html")
        admin = User.objects.filter(user_type="Admin", notification_email=True)
        for i in admin:
            send_email_notification_business.delay(title="Request Hours", name=i.name, email=i.email,
                                                   sender_name=sender_name, subject="Request For Additional Hours",
                                                   engagement=engagement, hours=hours, request=request.get_host(),
                                                   increase_hour=increase_hours, message=message,
                                                   txt_template="requested_hour.txt",
                                                   html_template="requested_hour.html")
        if user.notification_app:
            business_request_hours_notification(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        id_hour = kwargs["pk"]
        instance = self.get_object()
        user = self.request.user
        user_type = user.user_type
        hour = instance.hours
        increase_hour = instance.increase_hour
        engagement = instance.engagement.title
        description = instance.description
        business_name = instance.engagement.business.name
        business_email = instance.engagement.business.email
        expert_name = instance.engagement.expert.name
        expert_email = instance.engagement.expert.email
        admin_email = instance.request_to.email
        admin_name = instance.request_to.name
        notification_business = instance.engagement.business.notification_email
        notification_expert = instance.engagement.expert.notification_email
        notification_admin = instance.request_to.notification_email
        # business1 = BusinessHourRequest.objects.filter(id=id_hour).first()
        accept = request.data.get('accepted')
        message = ""
        if accept == 'true':
            instance.is_show = False
            instance.accepted = True
            instance.save()
            message = "accepted"
        if accept == 'false':
            instance.is_show = False
            instance.accepted = False
            instance.save()
            message = "denied"
        if user_type == "Expert":
            if notification_business:
                title = f"GrowTal:{business_name} has {message} your request for more hours!"
                send_email_notification_business.delay(title=title, request=request.get_host(),
                                                       name=business_name, sender_name=user.name,
                                                       email=business_email, subject=message,
                                                       engagement=engagement, hours=hour, increase_hour=increase_hour,
                                                       description=description, business_name=business_name,
                                                       html_template="requested_hours_accept.html",
                                                       txt_template="requested_hours_accept.txt")

        if user_type == "Business":
            if notification_expert:
                title = f"GrowTal:{expert_name} has {message}your request for more hours!",
                send_email_notification_business.delay(title=title, request=request.get_host(),
                                                       name=expert_name, email=expert_email,
                                                       engagement=engagement, hours=hour, increase_hour=increase_hour,
                                                       description=description, subject=message,sender_name=user.name,
                                                       html_template="requested_hours_accept.html",
                                                       txt_template="requested_hours_accept.txt")
        if notification_admin:
            send_email_notification_business.delay(title=title, name=admin_name,
                                                   sender_name=user.name, request=request.get_host(),
                                                   email=admin_email, subject=message,
                                                   engagement=engagement, hours=hour, increase_hour=increase_hour,
                                                   description=description, business_name=business_name,
                                                   html_template="requested_hours_accept.html",
                                                   txt_template="requested_hours_accept.txt")

        accept_reject_requested_hour_notification(instance, message, user_type)

        return Response({"Message": message + " successfully"})


class Rating(viewsets.ModelViewSet):
    serializer_class = ExpertRatingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']
    queryset = ExpertRating.objects.all()

    def get_queryset(self):
        return self.queryset.filter(business=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = User.objects.filter(user_type='Admin')
            for i in user:
                if i.notification_email:
                    send_email_notification_business.delay(title="Rate An Expert",
                                                           name=serializer.instance.business.name, email=i.email,
                                                           receiver=serializer.instance.expert.name,
                                                           request=request.get_host(),
                                                           message=serializer.instance.rating, subject="New Ratting for"
                                                                                                       "expert",
                                                           txt_template="/rating_to_all_admin.txt",
                                                           html_template="/rating_to_all_admin.html")
            rating_notification_admin(serializer.instance)
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class MyTeams(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MyTeamsSerializer
    queryset = AgreedEngagement.objects.select_related('expert', 'business').distinct('expert').order_by('-expert_id')

    def get_queryset(self):
        queryset = self.queryset.filter(business=self.request.user).exclude(end=True)
        return queryset


class BusinessContractListing(viewsets.ReadOnlyModelViewSet):
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
            return Response(response.json())
        return Response({}, status=status.HTTP_404_NOT_FOUND)


class BusinessContractDownload(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        API_KEY = settings.HELLO_SIGN_API_KEY
        HELLO_SIGN_BASE_URL = f"https://{API_KEY}:@api.hellosign.com/v3/"
        signature_request_id = self.request.query_params.get('sig_id')
        if signature_request_id:
            params = {
                "get_url": True,
                "file_type": "pdf"
            }
            response = requests.get(f"{HELLO_SIGN_BASE_URL}/signature_request/files/{signature_request_id}",
                                    params=params)
            return Response(response.json(), status=status.HTTP_200_OK)

        else:
            return Response({"non_field_error": "Signature ID is required"}, status=status.HTTP_400_BAD_REQUEST)


class EndingEngagementRequest(viewsets.ModelViewSet):
    serializer_class = EndingEngagementSerializer
    queryset = EndingEngagementRequest.objects.all()
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        user = User.objects.filter(user_type='Admin')
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = serializer.instance
        engagement = instance.agreed_engagement.title
        expert_name = instance.agreed_engagement.expert.name
        expert_email = instance.agreed_engagement.expert.email
        business_name = instance.agreed_engagement.business.name
        business_email = instance.agreed_engagement.business.email
        request_user = self.request.user
        name = ""
        email = ""
        send_email = False
        if request_user.user_type == "Expert":
            name = business_name
            email = business_email
            if request_user.notification_email:
                send_email = True

        if request_user.user_type == "Business":
            name = expert_name
            email = expert_email
            if request_user.notification_email:
                send_email = True
        subject = "End Engagement"
        if send_email:
            send_email_notification_business.delay(title=subject, name=name, email=email,
                                                   engagement=engagement, sender_name=request_user.name,
                                                   txt_template="end_engagement.txt", subject=subject,
                                                   request=request.get_host(),
                                                   html_template="end_engagement.html")
        for i in user:
            if i.notification_email:
                send_email_notification_business.delay(title=subject, name=i.name, email=i.email,
                                                       sender_name=request_user.name,
                                                       engagement=engagement, subject=subject,
                                                       request=request.get_host(),
                                                       txt_template="end_engagement.txt",
                                                       html_template="end_engagement.html")
        expert_end_engagement_request_notification(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BillingHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = BillingHistorySerilzier
    queryset = AgreedEngagement.objects.select_related('expert', 'business').all()

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        expert = self.request.query_params.get('expert')
        queryset = self.queryset.filter(business=self.request.user)
        queryset = queryset.annotate(company=F('business__business_profile__company_name'))
        if expert:
            queryset = queryset.filter(expert__name__icontains=expert)
        if start_date and end_date:
            billing_history = queryset.filter(engagement__date__range=(start_date, end_date))
            if billing_history:
                queryset1 = billing_history.annotate(total_hours=Sum('engagement__hour'),
                                                     billing_start_date=Value(str(start_date),
                                                                              output_field=CharField()),
                                                     billing_end_date=Value(str(end_date),
                                                                            output_field=CharField())). \
                    order_by('-total_hours')
                return queryset1
            return AgreedEngagement.objects.none()

        period = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today)
        if period:
            billing_history = queryset.filter(engagement__date__range=(period[0].start_date, period[0].end_date))
            if billing_history:
                queryset1 = billing_history.annotate(total_hours=Sum('engagement__hour'),
                                                     billing_start_date=Value(str(period[0].start_date),
                                                                              output_field=CharField()),
                                                     billing_end_date=Value(str(period[0].end_date),
                                                                            output_field=CharField())). \
                    order_by('-total_hours')
                return queryset1

        return AgreedEngagement.objects.none()

    @action(methods=['get'], detail=False)
    def billing_history_csv(self, request):
        queryset = self.queryset.filter(business=self.request.user)
        period = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="My Gorwtal billing_history.csv"'
        header = ['Expert Name', 'Hours', 'Rate', 'Time Frame']
        writer = csv.writer(response)
        writer.writerow(header)
        if period:
            billing_history = queryset.filter(engagement__date__range=(period[0].start_date, period[0].end_date))
            if billing_history:
                queryset1 = billing_history.annotate(total_hours=Sum('engagement__hour'),
                                                     billing_start_date=Value(str(period[0].start_date),
                                                                              output_field=CharField()),
                                                     billing_end_date=Value(str(period[0].end_date),
                                                                            output_field=CharField())). \
                    order_by('-total_hours')
                for i in queryset1:
                    writer.writerow([
                        i.expert.name,
                        i.total_hours,
                        i.business_rate,
                        '{}'.format(i.billing_start_date + "/" + i.billing_end_date)
                    ])
            return response


class BusinessProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = BusinessProfile.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = BusinessProfile.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(company_name__icontains=search)
        company = []
        for i in queryset:
            data = {
                "value": i.user.id,
                "label": i.company_name
            }
            company.append(data)
        return Response(company)
