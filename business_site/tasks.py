from celery import Celery, Task, shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_email_notification_business(title, name, email, subject=None, receiver=None, reply=None, message=None,
                                     hours=None, increase_hour=None, engagement=None, request=None,
                                     txt_template=None, html_template=None, expertise=None, refer=None,
                                     sender_name=None, status=None, description=None, business_name=None):
    context = {
        'title': title,
        'sender': name,
    }
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
    if message:
        context['message'] = message
    if hours:
        context['hour'] = hours
    if increase_hour:
        context['increase_hour'] = increase_hour
    if engagement:
        context['engagement'] = engagement
    if sender_name:
        context['sender_name'] = sender_name
    if status:
        context['status'] = status
    if description:
        context['description'] = description
    if business_name:
        context['business_name'] = business_name
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
