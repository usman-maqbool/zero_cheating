from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

 
def send_remainder_to_expert(name, email, title):
    context = {
        'title': title,
        'name': name,
        'subject': "Billing Period Close ",
    }
    email_html_message = render_to_string('email/remainder_to_all_expert.html', context)
    email_plaintext_message = render_to_string('email/remainder_to_all_expert.txt', context)
    msg = EmailMultiAlternatives(
        # title:
        "Requested Hours",
        # message:
        email_plaintext_message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()




