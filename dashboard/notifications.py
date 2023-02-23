import logging
from users.models import User
from push_notification.models import Notification


def refer_notification_admin(instance):
    try:
        title = f"{instance.referral_type} Refer"
        message = f"{instance.user.name} has requested an Engagement"
        data = {
            'name1': instance.user.name,
            'text': f'has referred {instance.name} as',
            'name2': instance.referral_type,
            'screen_name': 'referrals_expert_history' if instance.user.user_type in ['Expert'] else 'referrals_business'
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)


def upsell_notification_admin(instance):
    try:
        title = "Upsell"
        message = f"{instance.expert.name} has upsell to their client {instance.client.name}"
        data = {
            'name1': instance.expert.name,
            'text': 'has upsell to their client',
            'name2': instance.client.name,
            'screen_name': ''
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)
