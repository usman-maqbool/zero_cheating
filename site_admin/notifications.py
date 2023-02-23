import logging
from push_notification.models import Notification
from users.models import User


def share_expert_with_business(email):
    try:
        title = "Expert for your Engagement"
        message = "GrowTal has shared an expert upon your request. Please check your email for more details."
        data = {
            'name1': 'We have shared expert for your requested engagement check your email.',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        user = User.objects.filter(email=email).first()
        if user:
            Notification.objects.create(title=title, message=message, data=data if data else {}, user=user)
    except Exception as e:
        logging.warning(e)


def share_opportunity_with_expert(email):
    try:
        title = "Opportunity For Expert"
        message = "GrowTal has a potential opportunity for you! Please check your email for more details."
        data = {
            'name1': 'We have shared opportunity for your requested engagement check your email',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        user = User.objects.filter(email=email).first()
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=user)
    except Exception as e:
        logging.warning(e)


def create_engagement_notification(instance):
    try:
        title = "New Engagement"
        message = "A new engagement has been created."
        data = {
            'name1': f'New Engagement "{instance.description}"',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.expert)
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.business)
    except Exception as e:
        logging.warning(e)


def accept_end_engagement_notification(instance, message):
    try:
        title = "Engagement update"
        message = message
        data = {
            'name1': message,
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.business)
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.created_by)
    except Exception as e:
        logging.warning(e)


def push_notification_to_expert(instance, request):
    from home.tasks import send_email_notification
    try:
        title = instance["title"]
        message = "A new push notification has been created."
        data = {
            'name1': f'{instance["title"]}',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        agreed_users = ''
        if instance['expert_q'] == "All Expert":
            agreed_users = User.objects.filter(user_type="Expert")
        if instance['expert_q'] == "All Business":
            agreed_users = User.objects.filter(user_type="Business")
        if agreed_users:
            for agreed_user in agreed_users:
                Notification.objects.create(title=title, message=message, data=data if data else {},
                                            user=agreed_user)
                if agreed_user.notification_email:
                    send_email_notification.delay(title=f"Push Notification: {instance['message']}", name=agreed_user.name, request=request,
                                                  email=agreed_user.email, subject=f"{instance['message']}",
                                                  html_template="Expert_business_email.html",
                                                  txt_template="Expert_business_email.txt")

        if instance['expert_q'] == "Selected User":
            expert = instance['experts']
            expert_ids = [int(x) for x in expert.split(',')]
            selected_users = User.objects.filter(id__in=expert_ids)
            for user in selected_users:
                Notification.objects.create(title=title, message=message, data=data if data else {},
                                            user=user)
                if user.notification_email:
                    send_email_notification.delay(title=f"Push Notification: {instance['message']}", name=user.username, request=request,
                                                  email=user.email, subject=instance["message"],
                                                  html_template="Expert_business_email.html",
                                                  txt_template="Expert_business_email.txt")
    except Exception as e:
        logging.warning(e)


def notification_all_expert(title, message):
    try:
        title = title
        message = message
        data = {
            'name1': "",
            'text': message,
            'name2': "",
            'screen_name': ""
        }
        experts = User.objects.filter(user_type="Expert")
        for expert in experts:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=expert)
    except Exception as e:
        logging.warning(e)
