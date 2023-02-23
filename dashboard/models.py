from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from business_site.notifications import business_request_engagements_notification
from dashboard.notifications import refer_notification_admin
from users.models import User
from site_admin.models import AgreedEngagement
from home.models import BillingPeriods


# Create your models here.


class Refer(models.Model):
    USER_TYPE = (
        ('Expert', 'Expert'),
        ('Business', 'Business')
    )
    referral_type = models.CharField(max_length=10, choices=USER_TYPE, )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    date = models.DateField(auto_now=True)
    email = models.EmailField(null=True, blank=True)
    paid_status = models.BooleanField(default=False)
    web_url = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "referrals"


class Engagements(models.Model):
    expertise_area = models.CharField(max_length=50)
    additional_info = models.TextField(500)
    commitment = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="engagements_user")
    ended = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.name)


class TimeLog(models.Model):
    date = models.DateField()
    hour = models.IntegerField()
    minute = models.IntegerField()
    description = models.TextField(max_length=100)
    expert = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='expert_engagement')
    engagement = models.ForeignKey(AgreedEngagement, on_delete=models.CASCADE, related_name='engagement', null=True,
                                   blank=True, )
    period = models.ForeignKey(BillingPeriods, on_delete=models.CASCADE, related_name='timelog_period', null=True,
                               blank=True)
    time_log = models.BooleanField(default=True)

    def __str__(self):
        return str(self.hour)


class Upsell(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upsell_client')
    expertise = models.CharField(max_length=100)
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upsell_expert', null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.client


CONTENT = [
    ('EDUCATION CENTER', 'EDUCATION CENTER'),
    ('BENEFITS', 'BENEFITS'),
    ('RESOURCES', 'RESOURCES')
]


class Resources(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    details = models.TextField()
    image = models.ImageField(upload_to='resources/', )
    url = models.URLField(max_length=500, default='')
    content = models.CharField(max_length=255, choices=CONTENT, null=True, blank=True)

    def __str__(self):
        return self.details


class Education(models.Model):
    details = models.TextField()
    image = models.ImageField(upload_to='education/')
    url = models.URLField(max_length=500, default='')

    def __str__(self):
        return self.details


class Benefits(models.Model):
    details = models.TextField()
    image = models.ImageField(upload_to='benefits/')
    url = models.URLField(max_length=500, default='')

    def __str__(self):
        return self.details
