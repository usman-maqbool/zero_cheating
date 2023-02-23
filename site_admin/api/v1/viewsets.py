import csv
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.filters import SearchFilter

from business_site.notifications import business_expert_request
from dashboard.models import TimeLog, Refer
from users.models import BusinessProfile, Profile, User
from .serializers import BusinessExpertRequestSerializer, AdminBusinessSerializer, AdminExpertSerializer, \
    ShareBusinessWithExpert, AdminTimeLogsSerializer, OnBoardSerializer, AgreedEngagementSerializer, \
    EngagementHistorySerializer, ReferralsSerializer, AdminExpertListSerializer
from ...filters import AdminTimeLogFilters, EngagementFilters
from ...models import ExpertRequest, AgreedEngagement
from dashboard.utils import DefaultListPagination
from ...notifications import create_engagement_notification, accept_end_engagement_notification, \
    notification_all_expert, \
    share_opportunity_with_expert, share_expert_with_business
from django.db.models import Sum, F, Value, CharField, Q
from home.models import BillingPeriods
from datetime import date, datetime
from django.conf import settings
from rest_framework.views import APIView
from site_admin.tasks import send_email_notification_admin

today = date.today()


class BusinessExpertRequestViewSets(ModelViewSet):
    serializer_class = BusinessExpertRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultListPagination
    http_method_names = ['post', 'get', 'delete', 'patch']
    queryset = ExpertRequest.objects.select_related('business').all()

    def get_queryset(self):
        return self.queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        business_expert_request(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminBusinessViewSet(ModelViewSet):
    serializer_class = AdminBusinessSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultListPagination
    http_method_names = ['get']
    filter_backends = [SearchFilter]
    search_fields = ['associated_email', 'company_name']
    queryset = BusinessProfile.objects.all().order_by('-id')

    def get_queryset(self):
        return self.queryset


class AdminTimeTracking(ModelViewSet):
    serializer_class = AdminTimeLogsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultListPagination
    http_method_names = ['get', 'patch']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AdminTimeLogFilters
    queryset = TimeLog.objects.select_related('expert', 'engagement').all()

    def get_queryset(self):
        queryset = self.queryset
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        current_billing = False
        queryset = queryset.annotate(client=F('engagement__business__business_profile__company_name'))
        billing_period = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today,
                                                       is_active=True).first()
        if billing_period:
            current_billing = {
                "start_date": billing_period.start_date,
                "end_date": billing_period.end_date
            }

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        client = self.request.query_params.get('client')

        expert = self.request.query_params.get('expert')
        queryset1 = queryset.filter(period__start_date__lte=today, period__end_date__gte=today, period__is_active=True)
        if start_date and end_date:
            queryset1 = queryset.filter(date__range=(start_date, end_date))
        if client:
            queryset1 = queryset1.filter(engagement__business__business_profile__company_name__icontains=client)
        if expert:
            queryset1 = queryset1.filter(expert__name__icontains=expert)
        if start_date and end_date:
            current_billing = {
                "start_date": start_date,
                "end_date": end_date
            }
        else:
            if billing_period:
                current_billing = {
                    "start_date": billing_period.start_date,
                    "end_date": billing_period.end_date
                }
        if not queryset1:
            return Response({"Message": "No log found for billing period", "Data": [], "Total": False,
                             "Current_billing_period": current_billing})
        queryset2 = queryset1.annotate(invoice_amount=F('engagement__expert_rate') * F('hour'),
                                       payment_amount=F('engagement__business_rate') * F('hour')).order_by('-date')
        total_calculation = queryset2.aggregate(total_invoice_rate=Sum(F('engagement__expert_rate')),
                                                total_payment_rate=Sum(F('engagement__business_rate')),
                                                total_invoice=Sum(F('invoice_amount')),
                                                total_payment=Sum(F('payment_amount')),
                                                total_hours=Sum(F('hour')))

        serializer = AdminTimeLogsSerializer(queryset2, many=True)
        return Response(
            {"Data": serializer.data, "Total": total_calculation, "Current_billing_period": current_billing})

    @action(detail=False, methods=['get'])
    def time_logs_csv(self, request):
        # logs = self.serializer_class(self.get_queryset(), many=True).data
        queryset = TimeLog.objects.select_related('expert', 'engagement').all()
        queryset = queryset.annotate(client=F('engagement__business__business_profile__company_name'))
        queryset = queryset.filter(period__start_date__lte=today, period__end_date__gte=today,
                                   period__is_active=True)
        if not queryset:
            return Response({"Message": "No Active period Please check billing period"})
        queryset1 = queryset.annotate(invoice_amount=F('engagement__expert_rate') * F('hour'),
                                      payment_amount=F('engagement__business_rate') * F('hour')).order_by('-date')
        total_calculation = queryset1.aggregate(total_invoice_rate=Sum(F('engagement__expert_rate')),
                                                total_payment_rate=Sum(F('engagement__business_rate'))
                                                , total_invoice=Sum(F('invoice_amount')),
                                                total_payment=Sum(F('payment_amount')),
                                                total_hours=Sum(F('hour')))

        billing_period = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today,
                                                       is_active=True).first()
        serializer = AdminTimeLogsSerializer(queryset1, many=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Expert Time Logs.csv"'
        header1 = ['Current Billing Period', 'Total Invoice Rate', 'Total Invoice Amount', 'Total Payment Rate',
                   'Total Payment Amount']
        writer = csv.writer(response)
        writer.writerow(header1)
        writer.writerow([billing_period.start_date, billing_period.end_date,
                         total_calculation['total_invoice_rate'],
                         total_calculation['total_invoice'], total_calculation['total_payment_rate'],
                         total_calculation['total_payment']])
        header = ['Client Name', 'Expert Name', 'Engagement', 'Billing Period', 'No. of Hours',
                  'Invoice Rate', 'Invoice Amount', 'Payment Rate', 'Payment Amount', ]
        writer = csv.writer(response)
        writer.writerow(header)
        for log in serializer.data:
            writer.writerow([
                log['client'],
                log['expert_name'],
                log['engagement_name'],
                '{}'.format(log["period"]["start_date"] + "/" + log["period"]["end_date"]),
                log['hour'],
                log['invoice_rate'],
                log['payment_rate'],
                log['payment_amount'],
                log['invoice_amount']
            ])
        return response


class AdminExpertViewSet(ModelViewSet):
    serializer_class = AdminExpertSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultListPagination
    http_method_names = ['get']
    filter_backends = [SearchFilter]
    search_fields = ['hourly_rate', 'user__email', 'user__name']
    queryset = Profile.objects.select_related('user').all().order_by('-id')

    def get_queryset(self):
        return self.queryset.filter(user__user_type="Expert").order_by('-id')


class AdminExpertListViewSet(ModelViewSet):
    serializer_class = AdminExpertListSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    queryset = User.objects.filter(user_type="Expert")

    def get_queryset(self):
        return self.queryset


class ShareExpertWithBusiness(ViewSet):

    def create(self, request):
        expert_name = request.data.get('expert_name')
        business_email = request.data.get('business_email')
        bio = request.data.get('bio')
        linkedin_url = request.data.get('linkedin_url')
        company_name = request.data.get('company_name')
        hourly_rate = request.data.get('hourly_rate')

        context = {
            'linkedin_url': linkedin_url,
            'company_name': company_name,
        }
        if company_name:
            context.update({'company_name': company_name})
        else:
            return Response({"company_name": "company name is required"}, status=400)

        if bio:
            context.update({'bio': bio})
        else:
            return Response({"bio": "bio is required"}, status=400)
        if hourly_rate:
            context.update({'hourly_rate': hourly_rate})
        else:
            return Response({"hourly_rate": "hourly rate is required"}, status=400)

        if linkedin_url:
            if 'https://www.linkedin.com/in/' in linkedin_url:
                context.update({"linkedin_url": linkedin_url})
            else:
                return Response("please provide the correct linkedin url", status=400)
        if company_name and bio and hourly_rate:
            share_expert_with_business(business_email)
            send_email_notification_admin.delay(title=f"GrowTal Opportunity <> {company_name}",
                                                email=business_email, subject="GrowTal Opportunity",
                                                message=bio, url=linkedin_url, increase_hour=hourly_rate,
                                                name=company_name, business_name=company_name,
                                                request=request.get_host(),
                                                html_template="share_expert1.html",
                                                txt_template="share_expert1.txt")

            return Response({"info": "Success"}, status=status.HTTP_200_OK)


class ShareBusinessWithExpertViewSet(ViewSet):

    def create(self, request):
        serializer = ShareBusinessWithExpert(data=request.data)
        if serializer.is_valid(raise_exception=True):
            expert_name = request.data.get('expert_name')
            expert_email = request.data.get('expert_email')
            details = request.data.get('details')
            business_web_url = request.data.get('business_web_url')
            hourly_rate = request.data.get('hourly_rate')
            business_name = request.data.get('business_name')
            send_email_notification_admin.delay(title="Expert for your requested engagement", email=expert_email,
                                                message=details, url=business_web_url, increase_hour=hourly_rate,
                                                name=expert_name, business_name=business_name,
                                                request=request.get_host(),
                                                html_template="share_business_with_expert.html",
                                                txt_template="share_business.txt", subject="New Business Opportunity")
            return Response({"info": "Success"}, status=status.HTTP_200_OK)


class OnBoardUsers(ViewSet):

    def create(self, request):
        serializer = OnBoardSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            message = request.data.get('message')
            email = request.data.get('email')
            user_type = request.data.get('user_type')
            detail = ""
            if user_type == "Expert":
                detail = f"detail = GrowTal has invited you to join their platform! The GrowTal platform will allow you to " \
                         f"log hours for your engagements, view your log history, access education and exclusive " \
                         f"resources and refer other experts and businesses. \n If you have any questions, feel free to reach out to GrowTal directly at support@growtal.com."
            if user_type == "Business":
                detail = f"GrowTal has invited you to join their platform! The GrowTal platform will allow you to " \
                         f"access your experts hours, add additional team members, view your billing history, access " \
                         f"exclusive benefits and refer other businesses and experts. \n If you have any questions, feel free to reach out to GrowTal directly at support@growtal.com."
            send_email_notification_admin.delay(title="Invitation to Growtal", email=email, user_type=user_type,
                                                message=message, html_template="onboard.html",
                                                txt_template="onboard.html", detail=detail, request=request.get_host(),
                                                subject="You’ve been invited to join the GrowTal Platform!")
            return Response({"info": "Success"}, status=status.HTTP_200_OK)


class AgreedEngagementViewset(ModelViewSet):
    serializer_class = AgreedEngagementSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'get', 'patch', 'delete']
    pagination_class = DefaultListPagination
    filterset_class = EngagementFilters
    queryset = AgreedEngagement.objects.all().order_by('-id')

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.annotate(company=F('business__business_profile__company_name'))
        queryset = queryset.exclude(end=True)
        user = self.request.user
        query_params = self.request.query_params.get('sort')
        if user.user_type == "Admin":
            queryset = queryset.filter(created_by=user, end=False)
        if user.user_type == 'Expert':
            queryset = queryset.filter(expert=user, end=False)
        if user.user_type == 'Business':
            queryset = queryset.filter(business=user, end=False)
        if query_params:
            return queryset.order_by(query_params)
        return queryset

    def create(self, request, *args, **kwargs):
        data = self.request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        get_id = serializer.data['id']
        agree = AgreedEngagement.objects.filter(id=get_id).first()
        agree.created_by = self.request.user
        agree.save()
        user = self.request.user
        sender = user.name
        engagement = serializer.instance.title
        expert = serializer.instance.expert.name
        business = serializer.instance.business.name
        expert_email = serializer.instance.expert.email
        business_email = serializer.instance.business.email
        hourly = serializer.instance.hour
        expert_hour_rate = serializer.instance.expert_rate
        business_hour_rate = serializer.instance.business_rate
        rate_per_bill = serializer.instance.rate_per_bill
        start_date = serializer.instance.agreement_start_date
        title = "Congratulations on your GrowTal Engagement!"
        if serializer.instance.expert.notification_email:
            send_email_notification_admin.delay(title=title, name=sender, email=expert_email,
                                                receiver=expert,
                                                business_name=business, engagement=engagement, hour=hourly,
                                                business=business_hour_rate, expert=expert_hour_rate,
                                                rate=rate_per_bill,
                                                start_date=datetime.strftime(start_date, "%Y-%m-%d"), expert_name=expert,
                                                subject=serializer.instance.title, txt_template="new_engagement.txt",
                                                html_template="new_engagement.html", request=request.get_host())
        if serializer.instance.business.notification_email:
            send_email_notification_admin.delay(title=title, name=sender, email=business_email,
                                                receiver=business, business_name=business, engagement=engagement,
                                                hour=hourly, expert_name=expert,
                                                business=business_hour_rate, expert=expert_hour_rate,
                                                rate=rate_per_bill,
                                                start_date=datetime.strftime(start_date, "%Y-%m-%d"), subject=serializer.instance.title,
                                                txt_template="new_engagement_business.txt", request=request.get_host(),
                                                html_template="new_engagement_business.html")
        create_engagement_notification(serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = self.request.user
            admin_name = instance.created_by.username
            admin_email = instance.created_by.email
            message = ""
            email = ""
            name = ""
            subject = ""
            if user.user_type == "Expert":
                name = instance.business.name
                email = instance.business.email
            if user.user_type == "Business":
                name = instance.expert.name
                email = instance.expert.email

            if request.data.get("accepted"):
                message = f"{instance.expert and instance.expert.name} has accepted a new engagement \"{instance.description}\" with {instance.business and instance.business.name}"
                subject = "Engagement Accepted"
                accept_end_engagement_notification(instance, message)
            if request.data.get("end"):
                message = f"{instance.expert and instance.expert.name} has ended an engagement \"{instance.description}\" with {instance.business and instance.business.name}"
                subject = "Engagement Rejected"
                accept_end_engagement_notification(instance, message)
            # send_email_notification_admin.delay(title=message, name=user.name, email=email, receiver=name,
            #                                     subject=subject, request=request.get_host(),
            #                                     txt_template="accept_reject_engagement.txt",
            #                                     html_template="accept_reject_engagement.html")
            send_email_notification_admin.delay(title=message, name=name, email=admin_email,
                                                receiver=admin_name.capitalize(),
                                                subject=subject, request=request.get_host(),
                                                txt_template="accept_reject_engagement.txt",
                                                html_template="accept_reject_engagement.html")

            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def expert_engagement_history(self, request):
        minute = self.request.query_params.get('minute')
        hour = self.request.query_params.get('hour')
        user = self.request.user
        queryset = AgreedEngagement.objects.all().order_by('-id')

        data = queryset.annotate(company=F('business__business_profile__company_name'))
        if user.user_type == "Admin":
            data = data.order_by('-id')
        if user.user_type == 'Expert':
            data = data.filter(expert=user).order_by('-id')
        if user.user_type == 'Business':
            data = data.filter(business=user).order_by("-id")

        if data:
            qs = self.filter_queryset(data)
            if qs:
                page = self.paginate_queryset(qs)
                if page is not None:
                    serializer = EngagementHistorySerializer(page, many=True)
                    if hour or minute:
                        time_filter = []
                        for series in serializer.data:
                            if series["time"]['hour'] == int(hour) and series["time"]['minute'] == int(minute):
                                time_filter.append(series)
                        return self.get_paginated_response(time_filter)

                    return self.get_paginated_response(serializer.data)
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def expert_engagement_csv(self, request):

        logs = EngagementHistorySerializer(self.get_queryset(), many=True).data
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Expert engagement Logs.csv"'
        header = ['Engagement Name', 'Client', 'Description', 'Time', 'Status', 'Start Date']
        writer = csv.writer(response)
        writer.writerow(header)
        for log in logs:
            writer.writerow([
                log['description'],
                log['business_name'],
                log['description'],
                ('hours {}, minutes {}'.format(
                    log['time']['hour'] if log['time']['hour'] is not None else 0,
                    log['time']['minute'] if log['time']['minute'] is not None else 0)),
                ('Active' if log['end'] is False else 'Ended'),
                datetime.strptime(log['agreement_start_date'], '%Y-%m-%d').strftime("%m/%d/%Y"),
            ])
        return response


class Referrals(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultListPagination
    http_method_names = ['get', 'patch']
    serializer_class = ReferralsSerializer
    queryset = Refer.objects.select_related('user').all().order_by('-id')

    def get_queryset(self):
        param = self.request.query_params.get("referred_by")
        if param:
            return self.queryset.filter(user__user_type=param)
        return self.queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        paid_status = request.data.get('paid_status')
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            if paid_status:
                if paid_status:
                    return Response({"Message": "Paid Successfully"})
                else:
                    return Response({"Message": "Unpaid Successfully"})
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class OpportunityViewSet(ModelViewSet):
    serializer_class = AgreedEngagementSerializer
    http_method_names = ['get']
    queryset = AgreedEngagement.objects.all().filter(accepted=False, end=False).order_by('-id')


class CloseBillingPeriod(APIView):

    def post(self, request):
        billing = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today, is_active=True).first()
        if billing:
            billing.is_active = False
            billing.save()
            title = "Close Billing Period"
            message = "Billing period is close"
            notification_all_expert(title, message)
            expert = User.objects.filter(user_type="Expert", notification_email=True)
            if expert:
                for i in expert:
                    if i.email:
                        send_email_notification_admin.delay(title=title, message=message, receiver=i.username,
                                                            email=i.email, request=request.get_host(),
                                                            html_template="close_billing_period.html",
                                                            txt_template="close_billing_period.txt"
                                                            )
        else:
            return Response({"Message": "NO Current Billing Period"}, status=400)

        return Response({"Message": "Billing Period Close Successfully"}, status=200)


class HourReminder(APIView):

    def post(self, request):
        title = "Hours Reminder"
        message = "Enter hours for previous 2 weeks if you haven’t already"
        notification_all_expert(title, message)
        expert = User.objects.filter(user_type="Expert", notification_email=True)
        if expert:
            for i in expert:
                if i.email:
                    send_email_notification_admin.delay(title=title, message=message, receiver=i.username,
                                                        email=i.email,  request=request.get_host(),
                                                        html_template="hourly_remainder.html",
                                                        txt_template="hourly_remainder.txt"
                                                        )
        return Response({"Message": "Reminder Send To All Expert Successfully"}, status=200)
