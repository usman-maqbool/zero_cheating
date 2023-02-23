from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django_rest_passwordreset.signals import reset_password_token_created
from growtal_35169.settings import BASE_URL_FRONTEND
from django.conf import settings


class User(AbstractUser):
    # WARNING!
    """
    Some officially supported features of Crowdbotics Dashboard depend on the initial
    state of this User model (Such as the creation of superusers using the CLI
    or password reset in the dashboard). Changing, extending, or modifying this model
    may lead to unexpected bugs and or behaviors in the automated flows provided
    by Crowdbotics. Change it at your own risk.


    This model represents the User instance of the system, login system and
    everything that relates with an `User` is represented by this model.
    """

    # First Name and Last Name do not cover name patterns
    # around the globe.
    USER_TYPE = (
        ('Expert', 'Expert'),
        ('Business', 'Business'),
        ('Admin', 'Admin')
    )
    name = models.CharField(_("Name of User"), blank=True, null=True, max_length=255)
    user_type = models.CharField(max_length=10, choices=USER_TYPE, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    linkedin_profile_url = models.URLField(max_length=500, null=True, blank=True)
    approve = models.BooleanField(default=False)
    notification_email = models.BooleanField(default=True)
    notification_app = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def get_avg_rating(self):
        from business_site.models import ExpertRating
        return ExpertRating.objects.filter(expert_id=self.pk).aggregate(rating=Avg('rating'))


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_user')
    resume = models.FileField(upload_to='user_resume/')
    hourly_rate = models.FloatField()
    expert_bio = models.TextField(max_length=800)
    user_availability = models.PositiveIntegerField(default=0)
    admin_note = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Expertise(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    create_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


class UserExpertise(models.Model):
    expertise = models.ForeignKey(Expertise, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name="expertise")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')

    def __str__(self):
        return self.expertise.name


class Industry(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    create_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


class IndustryExperience(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, related_name="industry_name", null=True, blank=True,)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='industry_profile')

    def __str__(self):
        return self.industry.name


class AppliedExperties(models.Model):
    industry_type = models.CharField(max_length=100)
    experties = models.CharField(max_length=100)
    profile = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.industry_type


class BusinessProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_profile')
    logo = models.FileField(upload_to='business_logo/', null=True, blank=True)
    company_name = models.CharField(max_length=250)
    associated_email = models.EmailField()
    invoices_email = models.EmailField()
    admin_note = models.TextField(null=True, blank=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    poc = models.CharField(max_length=250, null=True, blank=True)
    blrub = models.TextField(max_length=800, null=True, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name


class UpsellText(models.Model):
    disclaimer_text = models.CharField(max_length=250)
    active = models.BooleanField()

    def __str__(self):
        return self.disclaimer_text


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'request_host': instance.request.get_host(),
        'name': reset_password_token.user.name,
        'reset_password_url': "{}/?token={}".format(
            BASE_URL_FRONTEND+'auth/change-password',
            urlsafe_base64_encode(force_bytes(reset_password_token.key)))
    }

    # render email text
    email_html_message = render_to_string('email/user_reset_password.html', context)
    email_plaintext_message = render_to_string('email/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="Growtal"),
        # message:
        email_plaintext_message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()
