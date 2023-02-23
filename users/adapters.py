from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings

from .models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = request.META.get('HTTP_HOST')
        # HTTP_REFERER check to make sure email is received from valid HOST.
        print("CURRENT HOST", current_site)
        # if current_site not in settings.ALLOWED_HOSTS:
        #     return

        # activate_url = f"https://{current_site}{reverse('account_confirm_email', args=[emailconfirmation.key])}"
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "account_activation_url": activate_url,
            "current_site": current_site,
            "request_host": request.get_host()
        }
        if signup:
            email_template = "email/email_confirmation_signup"
        else:
            email_template = "email/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

    def send_mail(self, template_prefix, email, context):
        email_html_message = render_to_string('email/email_confirmation_signup.html', context)
        email_plaintext_message = render_to_string('email/email_confirmation_signup_subject.txt', context)
        msg = EmailMultiAlternatives(
            # title:
            "Confirm GrowTal Account!",
            # message:
            email_plaintext_message,
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [email]
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "SOCIALACCOUNT_ALLOW_REGISTRATION", True)

    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return
        if not user.email:
            return
        try:
            user = User.objects.get(
                email=user.email)  # if user exists, connect the account to the existing account and login
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
