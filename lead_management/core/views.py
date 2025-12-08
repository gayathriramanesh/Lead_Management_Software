import csv
import io
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Lead, Status
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
    - POST /api/leads/upload-csv/ - Upload CSV file and create leads in bulk
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
    
    @action(detail=False, methods=['post'], url_path='upload-csv')
    def upload_csv(self, request):
        """
        Handle CSV file upload via multipart form data.
        Parses CSV, validates each row, and creates valid leads.
        Returns detailed results with success/error counts and per-row errors.
        """
        # Check if file is present in request
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided. Please upload a CSV file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES['file']
        
        # Check if file is CSV
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'Invalid file type. Please upload a CSV file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read and decode the CSV file
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
        except Exception as e:
            return Response(
                {'error': f'Error reading CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get existing emails from database to check for duplicates
        existing_emails = set(Lead.objects.values_list('email', flat=True))
        
        # Track results
        success_count = 0
        error_count = 0
        errors = []
        created_leads = []
        seen_emails_in_csv = set()
        
        # Process each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            row_errors = []
            
            # Extract and validate required fields
            name = row.get('name', '').strip()
            age_str = row.get('age', '').strip()
            email = row.get('email', '').strip()
            place = row.get('place', '').strip()
            status_str = row.get('status', '').strip()
            
            # Optional fields
            image_url = row.get('image_url', '').strip() or None
            remarks = row.get('remarks', '').strip() or None
            
            # Validate name
            if not name:
                row_errors.append('Name is required')
            elif len(name) > 100:
                row_errors.append('Name must be 100 characters or less')
            
            # Validate age
            age = None
            if not age_str:
                row_errors.append('Age is required')
            else:
                try:
                    age = int(age_str)
                    if age < 0:
                        row_errors.append('Age must be a positive number')
                except ValueError:
                    row_errors.append('Age must be a valid integer')
                    age = None
            
            # Validate email
            if not email:
                row_errors.append('Email is required')
            else:
                # Check email format
                try:
                    from django.core.validators import validate_email
                    validate_email(email)
                except ValidationError:
                    row_errors.append('Invalid email format')
                
                # Check for duplicates in CSV
                if email in seen_emails_in_csv:
                    row_errors.append('Duplicate email in CSV file')
                seen_emails_in_csv.add(email)
                
                # Check for duplicates in database
                if email in existing_emails:
                    row_errors.append('Email already exists in database')
            
            # Validate place
            if not place:
                row_errors.append('Place is required')
            elif len(place) > 100:
                row_errors.append('Place must be 100 characters or less')
            
            # Validate status
            if not status_str:
                row_errors.append('Status is required')
            else:
                valid_statuses = ['New', 'Converted']  # From Status.TextChoices
                if status_str not in valid_statuses:
                    row_errors.append(f'Status must be one of: {", ".join(valid_statuses)}')
            
            # Validate image_url if provided
            if image_url and len(image_url) > 200:
                row_errors.append('Image URL must be 200 characters or less')
            
            # If there are errors, add to errors list
            if row_errors:
                error_count += 1
                errors.append({
                    'row': row_num,
                    'email': email if email else 'N/A',
                    'message': '; '.join(row_errors)
                })
            else:
                # Try to create the lead
                try:
                    lead = Lead.objects.create(
                        name=name,
                        age=age,
                        email=email,
                        place=place,
                        status=status_str,
                        image_url=image_url,
                        remarks=remarks
                    )
                    created_leads.append(lead.id)
                    existing_emails.add(email)  # Add to existing emails to prevent duplicates
                    success_count += 1
                except IntegrityError as e:
                    error_count += 1
                    errors.append({
                        'row': row_num,
                        'email': email,
                        'message': f'Database error: Email already exists or constraint violation'
                    })
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'row': row_num,
                        'email': email,
                        'message': f'Unexpected error: {str(e)}'
                    })
        
        # Prepare response
        response_data = {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors,
            'created_leads': created_leads
        }
        
        # Return appropriate status code
        if error_count == 0:
            return Response(response_data, status=status.HTTP_201_CREATED)
        elif success_count > 0:
            # Partial success - some rows succeeded, some failed
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # All rows failed
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
