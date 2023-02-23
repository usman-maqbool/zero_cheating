from django.db import models
from users.models import User

# Create your models here.
from site_admin.models import AgreedEngagement


INCREASE_HOURS = [
    ('Weekly', 'Weekly'),
    ('One-Time', 'One-Time')
]


class BusinessHourRequest(models.Model):
    engagement = models.ForeignKey(AgreedEngagement, on_delete=models.CASCADE)
    hours = models.PositiveIntegerField()
    description = models.TextField()
    # ongoing = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    increase_hour = models.CharField(max_length=255, choices=INCREASE_HOURS, null=True, blank=True)
    is_show = models.BooleanField(default=True)
    request_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="engagement_user_request", null=True,
                                   blank=True)

    # def __str__(self):
    #     return self.engagement.title


class ExpertRating(models.Model):
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expert_user')
    business = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_user')
    description = models.CharField(max_length=500)
    rating = models.PositiveIntegerField()

    def __str__(self):
        return self.expert.name
