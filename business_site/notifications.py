import logging
from push_notification.models import Notification
from users.models import User


def business_request_engagements_notification(instance):
    try:
        title = f"Engagement Request"
        message = f"{instance.user.name} has requested an Engagement for {instance.expertise_area}"
        data = {
            'name1': instance.user.name,
            'text': 'has requested an engagement',
            'name2': instance.expertise_area,
            'screen_name': 'engagements_opportunity'
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)


def business_request_engagements_accept(instance, status):
    try:
        title = f"Engagement Request {status}"
        message = f"Your request for Engagement has been {status}" 
        data = {
            'name1': f'Your request for Engagement has been {status}',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                            user=instance.user)
    except Exception as e:
        logging.warning(e)


def expert_end_engagement_request_notification(instance):
    try:
        business_profile = instance.agreed_engagement.business.business_profile.get()
        title = f"End engagement Request"
        message = f"{instance.user.name} has requested to end an engagement {instance.agreed_engagement.title}"
        data = {
            'name1': message,
            'text': 'has requested for ending an engagement',
            'name2': business_profile.company_name,
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.agreed_engagement.business)

        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.agreed_engagement.created_by)
    except Exception as e:
        logging.warning(e)


def business_expert_request(instance):
    try:
        business_profile = instance.agreed_engagement.business.business_profile.get()
        title = "Expert Requested by Business"
        message = f"{business_profile.company_name} has requested for an expert. Please check your email for more details."
        data = {
            'name1': business_profile.company_name,
            'text': 'has requested for an expert',
            'name2': '',
            'screen_name': ''
        }
        users = User.objects.filter(user_type="Admin")
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)

    except Exception as e:
        logging.warning(e)


def business_request_hours_notification(instance):
    try:
        business_profile = instance.agreed_engagement.business.business_profile.get()
        title = "Hour Requested by Business"
        message = f"{business_profile.company_name} has requested some additional hours for {instance.engagement.description}. Please check your email for more details."
        data = {
            'name1': f'"{business_profile.company_name}" ',
            'text': 'has request hours for',
            'name2': f'{instance.engagement.description}',
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.engagement.expert)
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.engagement.created_by)   
    except Exception as e:
        logging.warning(e)


def expert_request_hours_notification(instance):
    try:
        title = "Hour Requested by Expert"
        message = f"{ instance.engagement.business.name } has requested an additional team member! Please check your email for more details."
        data = {
            'name1': f'"{instance.engagement.expert.name}" ',
            'text': 'has request hours for',
            'name2': f'{instance.engagement.description}',
            'screen_name': ''
        }
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.engagement.business)
        Notification.objects.create(title=title, message=message, data=data if data else {},
                                    user=instance.engagement.created_by)
    except Exception as e:
        logging.warning(e)


def accept_reject_requested_hour_notification(instance, message, user_type):
    try:
        title = "Requested Hour"
        message = message
        data = {
            'name1': f'New Engagement "{instance.description}"',
            'text': '',
            'name2': '',
            'screen_name': ''
        }
        if user_type == "Expert":
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                                user=instance.engagement.business)
        if user_type == "Business":
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                                user=instance.engagement.business)
        #Notify admin regardless of who is ending the engagement
        Notification.objects.create(title=title, message=message, data=data if data else {},
                        user=instance.engagement.created_by)
    except Exception as e:
        logging.warning(e)


def notification_all_admin(title, message, instance, expertise):
    try:
        title = title
        message = message
        data = {
            'name1': instance.name,
            'text': f'has requested an additional team member for expertise',
            'name2': expertise,
            'screen_name': ""
        }
        users = User.objects.filter(user_type='Admin')
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)


def rating_notification_admin(instance):
    try:
        business_profile = instance.agreed_engagement.business.business_profile.get()
        title = "Rating"
        message = f"{business_profile.company_name} has rating {instance.rating} to an expert {instance}"
        data = {
            'name1': business_profile.company_name,
            'text': f'',
            'name2': "",
            'screen_name': ""
        }
        users = User.objects.filter(user_type='Admin')
        for user in users:
            Notification.objects.create(title=title, message=message, data=data if data else {},
                                        user=user)
    except Exception as e:
        logging.warning(e)
