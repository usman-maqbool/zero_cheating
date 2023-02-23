from celery import Celery, Task, shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_email_notification_dashboard(title, name, email, subject=None, receiver=None, reply=None, txt_template=None,
                                      html_template=None, expertise=None, refer=None, request=None):
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
    if refer:
        context['refer'] = refer
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
