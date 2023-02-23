from django.db import models
from users.models import User
from ckeditor.fields import RichTextField


class Feedback(models.Model):
    subject = models.CharField(max_length=100)
    body = RichTextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_reply = models.BooleanField(default=False)

    def __str__(self):
        return self.subject


class FeedbackReply(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    reply = RichTextField()

    def __str__(self):
        return (self.reply[:10] + '...') if len(self.reply) > 10 else self.reply


class BillingPeriods(models.Model):
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class UserSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_setting', null=True, blank=True)
    email = models.BooleanField(default=True)
    app = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
