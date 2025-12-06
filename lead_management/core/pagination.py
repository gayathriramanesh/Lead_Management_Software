from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class LeadPagination(PageNumberPagination):
    """
    Custom pagination class for Lead API.
    Provides paginated results with configurable page size.
    """
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Allow client to override page size via query parameter
    max_page_size = 100  # Maximum page size allowed
    
    def get_paginated_response(self, data):
        """
        Return a paginated style Response object with custom metadata.
        """
        return Response({
            'count': self.page.paginator.count,  # Total number of items
            'next': self.get_next_link(),  # URL to next page
            'previous': self.get_previous_link(),  # URL to previous page
            'page_size': self.page_size,  # Current page size
            'total_pages': self.page.paginator.num_pages,  # Total number of pages
            'current_page': self.page.number,  # Current page number
            'results': data  # The actual data
        })

