import csv
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from dashboard.utils import DefaultListPagination, ResourcesPagination
from site_admin.models import AgreedEngagement
from users.models import UpsellText
from .serializers import ReferSerializer, TimeLogSerializer, EngagementListSerializer, EngagementTimeLogSerializer, \
    EngagementHistory, UpsellSerializer, EducationSerializer, ResourcesSerializer, BenefitsSerializer
from dashboard.filters import TimeLogFilters
from dashboard.models import Refer, TimeLog, Upsell, Education, Resources, Benefits
from ...notifications import upsell_notification_admin
from home.models import BillingPeriods
from django.db.models import Q, F
from users.models import User
from dashboard.notifications import refer_notification_admin
from dashboard.tasks import send_email_notification_dashboard


class ReferViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReferSerializer
    pagination_class = DefaultListPagination
    http_method_names = ['post', 'get']

    def get_queryset(self):
        return Refer.objects.select_related('user').filter(user=self.request.user).order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        user_name = user.name
        refer_type = self.request.data.get('referral_type')
        admin_user = User.objects.filter(user_type='Admin')
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            refer = Refer.objects.get(id=serializer.data['id'])
            refer_notification_admin(refer)
            for i in admin_user:
                if i.notification_email:
                    if i.email:
                        send_email_notification_dashboard.delay(title="Team Opportunity", subject=" { sender } has referred an expert",
                                                                name=user_name, email=i.email,
                                                                request=request.get_host(),
                                                                refer=refer_type, html_template='refer.html',
                                                                txt_template="refer.txt")
            return Response(serializer.data, status=200)
        return serializer.errors(serializer.errors, status=400)


class TimeLogViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TimeLogSerializer
    pagination_class = DefaultListPagination
    filterset_class = TimeLogFilters
    http_method_names = ['post', 'get']
    queryset = TimeLog.objects.select_related('expert', 'engagement').all().order_by('-id')

    def get_queryset(self):
        queryset = self.queryset.filter(expert=self.request.user).order_by('-id')
        queryset = queryset.annotate(company=F("engagement__business__business_profile__company_name"))
        client = self.request.query_params.get('client')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if client:
            queryset = queryset.filter(engagement__business__id=client).\
                order_by('-id')
        if start_date and end_date:
            queryset = queryset.filter(date__range=(start_date, end_date))
        return queryset

    @action(methods=['get'], detail=False)
    def time_log_csv(self, request):
        time_logs = TimeLog.objects.select_related('expert', 'engagement').all().order_by('-id')
        time_logs = time_logs.filter(expert=self.request.user).order_by('-id')
        time_logs = time_logs.annotate(company=F("engagement__business__business_profile__company_name"))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="My Gorwtal Time Logs.csv"'
        header = ['Engagement Name', 'Client', 'Description', 'Time', 'Date']
        writer = csv.writer(response)
        writer.writerow(header)
        for logs in time_logs:
            writer.writerow([
                logs.engagement.description,
                logs.company,
                logs.description,
                '{}'.format(logs.hour+round(logs.minute/60, 2)),
                logs.date.strftime("%m/%d/%Y")]
            )
        return response

    def create(self, request, *args, **kwargs):
        date = request.data.get('date')
        hour = request.data.get('hour')
        minute = request.data.get('minute')
        description = request.data.get('description')
        expert = request.data.get('expert')
        engagement = request.data.get('engagement')
        periods = BillingPeriods.objects.all()
        if periods is None:
            return Response({"Message": "There is no active billing Period Please contact to site admin"}, status=400)
        if date:
            query1 = BillingPeriods.objects.filter(start_date__lte=date, is_active=True)
            query2 = query1.filter(end_date__gte=date)
            if query2:
                period_id = query2[0].id
            else:
                return Response({"Message": "You can not enter log in this period"}, status=400)
        else:
            return Response({"Message": "Date is Required"}, status=400)

        engagement_exist = AgreedEngagement.objects.filter(title=engagement, end=False)
        if not engagement_exist.exists():
            return Response({"Message": "Engagement with this name does not exist"}, status=400)

        data = {
            "date": date,
            "hour": hour,
            "minute": minute,
            "description": description,
            "expert": expert,
            "engagement": engagement_exist[0].id,
            "period": period_id
        }
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class EngagementListViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EngagementListSerializer
    pagination_class = DefaultListPagination
    http_method_names = ['get']
    queryset = AgreedEngagement.objects.all().filter(end=False).order_by('-id')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        def custom_response(response):
            if response['business_user']['business_detail']:
                return {"value": response["id"],
                        "label": f"{response['business_user']['business_detail'][0]['company_name']} - "
                                 f"{response['description']}"}
            else:
                return {"value": response["id"], "label": None}

        data = list(map(custom_response, serializer.data))
        return Response(data)


class DisclaimerText(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        disclaimer = UpsellText.objects.filter(active=True)
        if disclaimer:
            return Response({"disclaimer": disclaimer.first().disclaimer_text})
        return Response(data={"disclaimer":None}, status=status.HTTP_204_NO_CONTENT)


class EngagementTimeLogs(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = self.request.user
        engagement = self.request.query_params.get('engagement', None)
        if user and engagement:
            logs = TimeLog.objects.select_related('user', 'engagements').filter(user=user, engagements_id=engagement)
            serializer = EngagementTimeLogSerializer(logs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ExpertEngagements(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logs = TimeLog.objects.select_related('expert', 'engagement').filter(expert=self.request.user).distinct('engagement')
        serializer = EngagementHistory(logs, many=True).data
        if serializer:
            for x in serializer:
                eng_id = x['expert_engagement']['id']
                eng_logs = TimeLog.objects.filter(engagement_id=eng_id)
                x['engagement_logs'] = eng_logs.values() if eng_logs else []
            return Response(serializer, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)


class UpsellViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UpsellSerializer
    pagination_class = DefaultListPagination
    http_method_names = ['post']
    queryset = Upsell.objects.all().order_by('-id')

    def get_queryset(self):
        return self.queryset

    def create(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        business = self.request.data['client']
        agree = AgreedEngagement.objects.filter(business=business).first()
        if agree:
            admin_email = agree.created_by.email
            if agree.created_by.notification_email:
                send_email_notification_dashboard.delay(title= f"GrowTal Opportunity <> {business}", name=user.name,
                                                        subject="New Opportunity", email=admin_email,
                                                        request=request.get_host(),
                                                        txt_template="expert_grow_team.txt",
                                                        html_template="expert_grow_team.html")
        upsell_notification_admin(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EducationViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResourcesSerializer
    pagination_class = ResourcesPagination
    http_method_names = ['get']
    queryset = Resources.objects.all().filter(content="EDUCATION CENTER").order_by('-id')

    def get_queryset(self):
        queryset = self.queryset
        content = self.request.query_params.get('content')
        if content:
            queryset = queryset.filter(content__icontains=content)
        return queryset


class BenefitsViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResourcesSerializer
    pagination_class = ResourcesPagination
    http_method_names = ['get']
    queryset = Resources.objects.all().filter(content="BENEFITS").order_by('-id')

    def get_queryset(self):
        queryset = self.queryset
        content = self.request.query_params.get('content')
        if content:
            queryset = queryset.filter(content__icontains=content)
        return queryset


class ResourcesViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResourcesSerializer
    pagination_class = ResourcesPagination
    queryset = Resources.objects.all().order_by('-id')

    def get_queryset(self):
        queryset = self.queryset
        content = self.request.query_params.get('content')
        if content:
            queryset = queryset.filter(content__icontains=content)
        return queryset
