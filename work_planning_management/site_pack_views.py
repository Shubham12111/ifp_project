from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.http.response import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework import generics, permissions, filters, status, renderers
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from drf_yasg.utils import swagger_auto_schema

from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.utils import docs_schema_response_new
from django.http import FileResponse, Http404

from .models import *
from .site_pack_serializers import DocumentSerializer,DocumentSelectSerializer
from rest_framework.response import Response
from django.http import QueryDict

def sitepack_image(sitepack_instance):
    """
    Get document paths and types (image or video) associated with a sitepack_image.

    This function retrieves document paths and types (image or video) associated with a given sitepack_image.

    Args:
        sitepack_image (sitepack_image): Thesitepack_image instance.

    Returns:
        list: A list of dictionaries containing document paths and types.
    """
    document_paths = []
    
    for document in SitepackAsset.objects.filter(sitepack_id=sitepack_instance):
        extension = document.document_path.split('.')[-1].lower()

        # is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
        # Remove video upload feature for no support in PDF
        is_video = False
        is_image = extension in ['png', 'jpg', 'jpeg', 'txt', 'pdf', 'doc', 'docx', 'csv', 'xls', 'xlsx', 'zip']  # Add more image extensions if needed
        document_paths.append({
            'presigned_url': generate_presigned_url(document.document_path),
            'filename': document.document_path,
            'id': document.id,
            'is_video': is_video,
            'is_image': is_image
        })
    return document_paths   

class DocumentListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all stw requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = DocumentSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    template_name = 'site_packs/document_list.html'
    ordering_fields = ['created_at'] 

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
    def get_paginated_queryset(self, base_queryset):
        items_per_page = 10 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page
    
    def get_queryset(self):
        """
        Get the queryset based on filtering parameters from the request.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        # base_queryset = RLO.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')

        base_queryset = SitepackDocument.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset 

    common_get_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Data retrieved",
                )
    }
    @swagger_auto_schema(operation_id='Sitepack Document listing', responses={**common_get_response}) 
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'documents': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )
        

class DocumentAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a document.
    Supports both HTML and JSON response formats.
    """
    serializer_class = DocumentSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'site_packs/add_document.html'
    
    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a document.
        If the document exists, retrieve the serialized data and render the HTML template.
        If the document does not exist, render the HTML template with an empty serializer.
        """
    
        
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
        self,"survey", HasCreateDataPermission, 'add'
            )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Filter the queryset based on the user ID
       
        serializer = self.serializer_class(context={'request': request})
            
        if request.accepted_renderer.format == 'html':
            context = {'serializer':serializer
                          }
                
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)
      

  
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a document.
        """
      
        data = request.data
        print(data)
        file_list = data.getlist('file_list', [])
        print(file_list)
            
        if not any(file_list):
            data = data.copy()      # make a mutable copy of data before performing delete.
            del data['file_list']
            
        serializer_data = request.data if any(file_list) else data
            
        serializer = self.serializer_class(data=serializer_data, context={'request': request})
            
        message = "Your Site Pack Document has been added successfully."
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
                
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('sitepack_document_list'))

            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                        message=message,
                                        data=serializer.data
                                        )
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {'serializer':serializer, 
                           }
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                        message="We apologize for the inconvenience, but please review the below information.",
                                        data=convert_serializer_errors(serializer.errors))
            


class DocumentDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a Document.
    Supports both HTML and JSON response formats.
    """
    serializer_class = DocumentSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Site Pack Document has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Site Pack Document not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Document Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a Document.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'delete'
        )

        # Get the stw requirement instance from the database.
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        queryset = SitepackDocument.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        document_instance = queryset.first()
        print(document_instance)

        if document_instance:
            # Proceed with the deletion
            document_instance.delete()
            messages.success(request, "Your Site Pack Document has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your Site Pack Document has been deleted successfully!", )
        else:
            messages.error(request, "Site Pack Document not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Site Pack Document not found OR You are not authorized to perform this action.", )
            

       
class DocumentDownloadView(generics.RetrieveAPIView):
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'site_packs/document_list.html'
    """
    View for downloading a document.
    """
    
    def get(self, request, *args, **kwargs):
        document_id = kwargs.get('document_id')
        print(document_id)

        try:
            sitepack_asset = SitepackAsset.objects.get(sitepack_id=document_id)
            print(sitepack_asset)
            file_path = sitepack_asset.document_path  # Adjust for your file storage configuration
            print(file_path)
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'  # Force download
             # Generate a presigned URL for the S3 object
            presigned_url = generate_presigned_url(file_path)

            # Create a dictionary containing the presigned URL and other information
            context = {
                'presigned_url': presigned_url,
                'filename': file_path.split('/')[-1],  # Extract the filename from the S3 object key
            }

            return render(request, self.template_name, context)
        except SitepackAsset.DoesNotExist:
            return Response({'error': 'Document not found'}, status=404)


class SitepackJobListView(CustomAuthenticationMixin, generics.ListAPIView):
    """
    View to get the listing of all sitepack jobs.
    Supports both HTML and JSON response formats.
    """
    serializer_class = DocumentSerializer  # Replace with your serializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    template_name = 'site_packs/sitepack_job_list.html'
    ordering_fields = ['created_at']
    common_get_response = {
        status.HTTP_200_OK:
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message="Data retrieved",
            )
    }
    def get_paginated_queryset(self, base_queryset):
        items_per_page = 10
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If the page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If the page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        return current_page
    def get_queryset(self):
        """
        Get the queryset based on filtering parameters from the request.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),
        }
        base_queryset = JobDocument.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()
        return base_queryset
    
    common_get_response = {
        status.HTTP_200_OK:
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message="Data retrieved",
            )
    }
    @swagger_auto_schema(operation_id='Sitepack Job listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user
        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'jobs': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )
        

class DocumentSelectView(CustomAuthenticationMixin, generics.CreateAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'site_packs/job_form_sitepack.html'
    serializer_class = DocumentSelectSerializer

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form  to add the new documnet in job.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        job_id = kwargs.get('job_id')

        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class(),'job_id':job_id}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a document to a job.
        """
        # Retrieve the Job instance using job_id from the URL.
        job_id = kwargs.get('job_id')
        print(job_id)
        job = get_object_or_404(Job, id=job_id)  # Retrieve the Job instance using its ID
        print(job)

        serializer_data = request.data

        serializer = self.serializer_class(data=serializer_data, context={'request': request})

        message = "Document is assigned to the job successfully!"
        if serializer.is_valid():
            serializer.validated_data['job'] = job  # Assign the current user instance.
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('sitepack_job_list'))

            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                           message=message,
                                           data=serializer.data
                                           )
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {'serializer': serializer}
                return render_html_response(context, self.template_name)
            else:
                # Return JSON response with an error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                           message="We apologize for the inconvenience, but please review the below information.",
                                           data=convert_serializer_errors(serializer.errors))


class DocumentJobDeleteView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for deleting a Document assigned to job.
    Supports both HTML and JSON response formats.
    """
    serializer_class = DocumentSelectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Assigned Document has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Assigned Document not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='JOb Document Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a Document.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'delete'
        )

        # Get the stw requirement instance from the database.
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        queryset = JobDocument.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        job_document_instance = queryset.first()
        print(job_document_instance)

        if job_document_instance:
            # Proceed with the deletion
            job_document_instance.delete()
            messages.success(request, "Assigned Document has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Assigned Document has been deleted successfully!", )
        else:
            messages.error(request, "Assigned Document not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Assigned Document not found OR You are not authorized to perform this action.", )