from celery import Celery, Task, shared_task
from home.models import BillingPeriods
from datetime import date, datetime, timedelta
from site_admin.notifications import push_notification_to_expert
from push_notification.models import PushNotification
from home.utils import send_remainder_to_expert
from business_site.models import AgreedEngagement
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

today = date.today()
current_datetime = datetime.now()


@shared_task
def period_check():
    current_billing = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today).first()
    if not current_billing.is_active:
        current_billing.is_active = True
        current_billing.save()
    other_periods = BillingPeriods.objects.exclude(id=current_billing.id)
    other_periods.update(is_active=False)


@shared_task()
def create_billing_periods():
    from datetime import date, timedelta
    last_ending_period = None
    bulk = []
    for i in range(1, 27):
        if last_ending_period:
            starting_period = last_ending_period + timedelta(days=1)
        else:
            starting_period = date(date.today().year, 1, 14)
            offset = -starting_period.weekday()
            starting_period = starting_period + timedelta(offset)
        last_ending_period = starting_period + timedelta(days=13)
        if starting_period <= date.today() <= last_ending_period:
            bulk.append(BillingPeriods(start_date=starting_period, end_date=last_ending_period, is_active=True))
        else:
            bulk.append(BillingPeriods(start_date=starting_period, end_date=last_ending_period, is_active=False))
    BillingPeriods.objects.bulk_create(bulk)


@shared_task
def send_notification_expert(*args, **kwargs):
    data = PushNotification.objects.filter(notification_type="Scheduled", scheduled_time=kwargs['schedule_time'])
    if data:
        for i in data:
            data = {
                "user": i.user,
                "title": i.title,
                "message": i.message,
                "notification_type": i.notification_type,
                "expert_q": i.expert_q,
                "experts": i.experts
                }
            print("send notification successfully")
            push_notification_to_expert(data, kwargs['request'])

    else:
        print('Notification are send')


@shared_task
def remainder_close_period_to_expert():
    current_billing = BillingPeriods.objects.filter(start_date__lte=today, end_date__gte=today).first()
    if current_billing.end_date == today or current_billing.end_date == today + timedelta(days=2):
        agree = AgreedEngagement.objects.all()
        for a in agree:
            if a.expert.email:
                send_remainder_to_expert(a.expert.name, a.expert.email, a.title)
            else:
                print("please enter the email address")


@shared_task
def send_email_notification(title, name, email, subject=None, receiver=None, reply=None, txt_template=None,
                            html_template=None, expertise=None, industries=None, request=None):
    context = {
        'title': title,
        'sender': name,
    }
    if request:
        context['request_host'] = request
    if receiver:
        context['receiver'] = receiver
    if subject:
        context['subject'] = subject
    if reply:
        context['reply'] = reply
    if expertise:
        context['expertise'] = expertise
    if industries:
        context['industries'] = industries
    email_html_message = render_to_string(f'email/{html_template}', context)
    email_plaintext_message = render_to_string(f'email/{txt_template}', context)
    msg = EmailMultiAlternatives(
        # title:
        title,
        # message:
        email_plaintext_message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()

    print("Sending email from shared tasks")
