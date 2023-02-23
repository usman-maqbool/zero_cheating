from django.db import models

# Create your models here.
from django.db.models import Sum
from users.models import User
from ckeditor.fields import RichTextField


class ExpertRequest(models.Model):
    business = models.ForeignKey(User, on_delete=models.CASCADE)
    expertise = models.CharField(max_length=250)
    preferred_rate = models.PositiveIntegerField()
    description = RichTextField()

    def __str__(self):
        return self.business.email


class AgreedEngagement(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    business = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agreed_business')
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agreed_expert')
    expert_rate = models.PositiveIntegerField()
    business_rate = models.PositiveIntegerField()
    rate_per_bill = models.PositiveIntegerField()
    agreement_start_date = models.DateField()
    agreement_end_date = models.DateField(null=True, blank=True)
    description = models.TextField(max_length=800)
    end = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now=True)
    accepted = models.BooleanField(default=False)
    hour = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_engagement_create', null=True,
                                   blank=True)

    def __str__(self):
        return self.description

    @property
    def get_time_logs(self):
        logs = self.engagement.filter(engagement=self.pk).aggregate(hours=Sum('hour'), minutes=Sum('minute'))
        if logs:
            hour = logs['hours']
            minute = logs['minutes']
            if minute and hour:
                if minute > 59:
                    n = 60
                    add_hour = minute // n
                    minute = minute % n
                    hour += add_hour
            data = {'hour': hour, 'minute': minute}
            return data


class EndingEngagementRequest(models.Model):
    agreed_engagement = models.ForeignKey(AgreedEngagement, on_delete=models.CASCADE,
                                          related_name='ending_agreed_engagement')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ending_engagement_user')
    video_call = models.URLField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.user.name
