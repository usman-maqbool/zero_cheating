import logging
from users.models import User
from push_notification.models import Notification


def signup_notification(name, type):
    try:
        title = f"{type} Signup"
        message = f"{name} has Signup as {type}"
        data = {
            'name1': name,
            'text': 'has Signup as',
            'name2': type,
            'screen_name': 'Notifications'
        }
        uesrs = User.objects.filter(user_type="Admin")
        for user in uesrs:
            Notification.objects.create(title=title, message=message, data=data if data else {}, user=user)
    except Exception as e:
        logging.warning(e)


def feedback_notification(name):
    try:
        title = "Feedback"
        message = ""
        data = {
            'name1': name,
            'text': ' has submitted feedback',
            'name2': '',
            'screen_name': 'Feedback'
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:   
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)


def feedback_reply_notification(user_id):
    try:
        title = "Feedback Response"
        message = "GrowTal has provided a response to your feedback. Please check your email for more details."
        data = {
            'name1': 'Team Growtal',
            'text': ' has replied to your feedback',
            'name2': '',
            'screen_name': ''
        }
        user = User.objects.get(id=user_id)
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=user)
    except Exception as e:
        logging.warning(e)


def profile_notification_admin(instance):
    try:
        title = "Profile"
        message = f"{instance.name} has added expertise to their profile. Please approve of their experience"
        data = {
            'name1': instance.name,
            'text': f'',
            'name2': "",
            'screen_name': ""
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)
