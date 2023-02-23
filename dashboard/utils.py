from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


class DefaultListPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 10

    def get_page_size(self, request):
        if self.page_size_query_param:
            page_size = min(
                int(request.query_params.get(self.page_size_query_param, self.page_size)),
                self.max_page_size,
            )
            if page_size > 0:
                return page_size
            elif page_size == 0:
                return None
            else:
                pass
        return self.page_size

    def get_paginated_response(self, data):
        return Response({
            'page_size': self.page_size,
            'total_objects': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page_number': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


class ResourcesPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    page_size = 8
    max_page_size = 8

    def get_page_size(self, request):
        if self.page_size_query_param:
            page_size = min(
                int(request.query_params.get(self.page_size_query_param, self.page_size)),
                self.max_page_size,
            )
            if page_size > 0:
                return page_size
            elif page_size == 0:
                return None
            else:
                pass
        return self.page_size

    def get_paginated_response(self, data):
        return Response({
            'page_size': self.page_size,
            'total_objects': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page_number': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })

