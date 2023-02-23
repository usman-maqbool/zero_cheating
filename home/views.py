from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from users.models import User
from rest_framework.response import Response


def home(request):
    packages = [
	{'name':'django-allauth', 'url': 'https://pypi.org/project/django-allauth/0.38.0/'},
	{'name':'django-bootstrap4', 'url': 'https://pypi.org/project/django-bootstrap4/0.0.7/'},
	{'name':'djangorestframework', 'url': 'https://pypi.org/project/djangorestframework/3.9.0/'},
    ]
    context = {
        'packages': packages
    }
    return render(request, 'home/index.html', context)


class SuperUserViewSet(ViewSet):
    http_method_names = ["post"]

    @action(detail=False, methods=['post'])
    def create_super_user(self, request):
        user_data = self.request.data
        super_user = User.objects.create(email=user_data.get('email'), name=user_data.get('name'),
                                         username=user_data.get('username'))
        super_user.set_password(user_data.get('password'))
        super_user.is_superuser = True
        super_user.is_staff = True
        super_user.is_active = True
        super_user.approve = True
        super_user.save()
        return Response('Admin Access Granted')
