from celery import Celery, Task, shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_email_notification_admin(title, email, name=None, subject=None, receiver=None, reply=None, txt_template=None,
                                  increase_hour=None, html_template=None, expertise=None, refer=None, business_name=None,
                                  url=None, user_type=None, message=None, engagement=None, hour=None, request=None,
                                  expert=None, business=None, rate=None, start_date=None, expert_name=None, detail=None):
    context = {
        'title': title,
        'sender': name,
    }
    if detail:
        context['detail'] = detail
    if receiver:
        context['receiver'] = receiver
    if request:
        context['request_host'] = request
    if subject:
        context['subject'] = subject
    if reply:
        context['reply'] = reply
    if expertise:
        context['expertise'] = expertise
    if refer:
        context['refer'] = refer
    if business_name:
        context['business_name'] = business_name
    if url:
        context['url'] = url
    if increase_hour:
        context['increase_hour'] = increase_hour
    if user_type:
        context['user_type'] = user_type
    if message:
        context['message'] = message
    if engagement:
        context['engagement'] = engagement
    if expert:
        context['expert'] = expert
    if business:
        context['business'] = business
    if start_date:
        context['start_date'] = start_date
    if hour:
        context['hour'] = hour
    if rate:
        context['rate'] = rate
    if expert_name:
        context['expert_name'] = expert_name
    print(context)
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
