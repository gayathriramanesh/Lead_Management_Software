from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .models import Lead
from .serializers import LeadSerializer
from .pagination import LeadPagination


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Lead instances.
    Provides CRUD operations: Create, Read, Update, Delete
    
    Endpoints:
    - GET /api/leads/ - List all leads (paginated)
      Query parameters:
        - page: Page number (default: 1)
        - page_size: Number of items per page (default: 10, max: 100)
    - POST /api/leads/ - Create a new lead
    - GET /api/leads/{id}/ - Get a specific lead
    - PUT /api/leads/{id}/ - Update a lead (full update - all fields required)
    - PATCH /api/leads/{id}/ - Partially update a lead (only send fields to update)
    - DELETE /api/leads/{id}/ - Delete a lead
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    pagination_class = LeadPagination
    
    def update(self, request, *args, **kwargs):
        """
        Handle PUT request - Full update of a lead.
        All fields must be provided.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH request - Partial update of a lead.
        Only send the fields you want to update.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """
        Handle DELETE request - Delete a lead from the database.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Lead deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )
