from django.shortcuts import render, redirect
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .serializers import *
from .models import Requirement, RequirementDefect,RequirementDocument, RequirementAsset
from django.contrib import messages
from rest_framework.response import Response
from rest_framework import filters
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new


def filter_requirements(data_access_value, user):
    # Define a mapping of data access values to corresponding filters.
    filter_mapping = {
        "self": Q(user_id=user),
        "all": Q(),  # An empty Q() object returns all data.
    }
    queryset = Requirement.objects.all()
    
    if user.roles.name == "quantity_surveyor":
        queryset =  queryset.filter(
            Q(quantity_surveyor=user) | filter_mapping.get(data_access_value, Q())
        )
    elif user.roles.name == "surveyor":
        queryset = queryset.filter(
            Q(surveyor=user) | filter_mapping.get(data_access_value, Q())
        )
    else:
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q()))
    return queryset 

class RequirementListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'requirement_list.html'
    ordering_fields = ['created_at'] 

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
    @swagger_auto_schema(operation_id='Requirement Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user)

        if request.accepted_renderer.format == 'html':
            context = {'requirements':queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=serializer.data)

class RequirementAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    
    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a requirement.
        If the requirement exists, retrieve the serialized data and render the HTML template.
        If the requirement does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)

    common_post_response = {
        status.HTTP_201_CREATED: 
            docs_schema_response_new(
                status_code=status.HTTP_201_CREATED,
                serializer_class=serializer_class,
                message = "Congratulations! requirement re has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    } 

    @swagger_auto_schema(operation_id='Requirement Add', responses={**common_post_response})  
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        data = request.data.copy()
        # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
        file_list = data.get('file_list', None)

        if file_list is not None and not any(file_list):
            del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
            serializer = self.serializer_class(data = data)
        else:
            serializer = self.serializer_class(data = request.data)
        
        message = "Congratulations! your requirement has been added successfully."
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_list'))

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
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))


class RequirementDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement_detail.html'
    serializer_class = RequirementAddSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user)
        queryset =  queryset.filter(pk=self.kwargs.get('pk')).first()
        

        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                document_paths = []
                requirement_defect = RequirementDefect.objects.filter(requirement_id=instance.id)
                serializer = self.serializer_class(instance=instance, context={'request': request})
                
                
                for document in RequirementAsset.objects.filter(requirement_id=instance):
                    extension = document.document_path.split('.')[-1].lower()

                    is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
                    is_image = extension in ['jpg', 'jpeg', 'png', 'gif']  # Add more image extensions if needed
                    document_paths.append({
                        'presigned_url': generate_presigned_url(document.document_path),
                        'filename': document.document_path,
                        'id': document.id,
                        'is_video': is_video,
                        'is_image': is_image
                    })
                
                        
                # Retrieve users associated with these roles
                users_with_survey_permission = User.objects.filter(roles__name= "surveyor")
                
                context = {
                    'serializer': serializer, 
                    'requirement_instance': instance, 
                    'requirement_defect': requirement_defect, 
                    'document_paths': document_paths,
                    'surveyers': users_with_survey_permission,
                    }
               

                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('requirement_list'))
            
    def post(self, request, *args, **kwargs):
        surveyer_selected = request.POST.get('surveyer')
        instance = self.get_queryset()
        try:
            instance.surveyor = User.objects.filter(pk=surveyer_selected).first()
            instance.save()
            
            message = "Surveyor is assigned successfully."
            
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_view', args=[instance.id]))
            else:
                return create_api_response(
                        status_code=status.HTTP_200_OK,
                        message=message
                    )
        except Exception as e:
            message = "Something went wrong"
            if request.accepted_renderer.format == 'html':
                messages.warning(request, message)
                return redirect(reverse('requirement_view'))
            else:
                return create_api_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=message
                    )

class RequirementUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a requirement.

    This view handles both HTML and API requests for updating a requirement instance.
    If the requirement instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the requirement instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    serializer_class = RequirementAddSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = filter_requirements(data_access_value, self.request.user)
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'requirement_instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('requirement_list'))
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Requirement has been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "You are not authorized to perform this action",
                ),

    }

    @swagger_auto_schema(auto_schema=None) 
    def put(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None) 
    def patch(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(operation_id='Requirement Edit', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a requirement instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the requirement is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        instance = self.get_queryset()
        if instance:
            data = request.data.copy()
            # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
            file_list = data.get('file_list', None)

            if file_list is not None and not any(file_list):
                del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
                serializer = self.serializer_class(data = data)
            else:
                serializer = self.serializer_class(instance=instance, data=request.data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated requirement instance.
                serializer.update(instance, validated_data=serializer.validated_data)
                message = "Your requirement has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to requirement_list.
                    messages.success(request, message)
                    return redirect(reverse('requirement_edit', kwargs={'pk': instance.id}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to requirement_list.
                messages.error(request, error_message)
                return redirect('requirement_list')
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class RequirementDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Requirement has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Requirement not found.",
                ),

    }
    @swagger_auto_schema(operation_id='Requirement Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a requirement.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'delete'
        )

        # Get the requirement instance from the database.
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = filter_requirements(data_access_value, self.request.user)
        instance = queryset.filter(pk=self.kwargs.get('pk')).first()

        if instance:
            # Proceed with the deletion
            instance.delete()
            messages.success(request, "Your requirement has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement has been deleted successfully!", )
        else:
            messages.error(request, "Requirement not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Requirement not found", )
    
class RequirementDefectView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = RequirementDefectAddSerializer
    serializer_class = RequirementDefectAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'defects.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user)
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset
    
    def get_queryset_defect(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset_defect = RequirementDefect.objects.filter(requirement_id = self.get_queryset() ).order_by('-created_at')
        return queryset_defect
    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.
        requirement_instance = self.get_queryset()

        requirement_defects = self.get_queryset_defect()
        defect_instance = requirement_defects.filter(pk=self.kwargs.get('pk')).first()
        
        if defect_instance:
            serializer =  self.serializer_class(instance=defect_instance)
            
        else:
            serializer =  self.serializer_class()
            defect_instance = {}
        
        if request.accepted_renderer.format == 'html':
            context = {
                'serializer': serializer,
                'requirement_instance': requirement_instance,
                'defects_list': self.get_queryset_defect(),
                'defect_instance':defect_instance
                }
            return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('requirement_list'))
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        
        data = request.data.copy()
        
        file_list = data.get('file_list', [])
        
        requirement_instance = self.get_queryset()
        defect_instance = RequirementDefect.objects.filter(requirement_id = requirement_instance, pk=self.kwargs.get('pk')).first()
        
        if not any(file_list):
            del data['file_list']
        
        serializer_data = request.data if any(file_list) else data
        
        message = "Congratulations! your requirement defect has been added successfully."
        
        # Check if the site address instance exists for the customer
        if defect_instance:
            # If the site address instance exists, update it.
            serializer = self.serializer_class(data=serializer_data, instance=defect_instance, context={'request': request})
            message = "Your requirement defect has been updated successfully!"
        else: 
            # If the site address instance does not exist, create a new one.
            serializer = self.serializer_class(data=serializer_data, context={'request': request})
            message = "Your requirement defect has been added successfully!"
        
        
        if serializer.is_valid():
            if  not defect_instance:
                serializer.validated_data['requirement_id'] = requirement_instance
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_defects', kwargs={'requirement_id': self.kwargs.get('requirement_id')}))
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
                           'requirement_instance': requirement_instance,
                           'defects_list': self.get_queryset_defect(),
                            'defect_instance':defect_instance
                           }
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))
   
class RequirementDefectDetailView(CustomAuthenticationMixin, generics.CreateAPIView):
    
    serializer_class = RequirementDefectResponseAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'defect_detail.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset = RequirementDefect.objects.filter(pk=self.kwargs.get('defect_id')).order_by('-created_at')
        return queryset
    
    def get_queryset_response(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        defect_instance = self.get_queryset().first()
        queryset =  RequirementDefectResponse.objects.filter(defect_id = defect_instance).first()
        return queryset

    def get_documents(self):
        """
        Get the filtered document_paths.
        """
        document_paths = []
        
        defect_instance = self.get_queryset().first()
        for document in RequirementDocument.objects.filter(defect_id=defect_instance):
                extension = document.document_path.split('.')[-1].lower()

                is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
                is_image = extension in ['jpg', 'jpeg', 'png', 'gif']  # Add more image extensions if needed
                
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path,
                    'id': document.id,
                    'is_video': is_video,
                    'is_image': is_image
                })
        return document_paths
    
    def get_response_documents(self):
        """
        Get the filtered document_paths.
        """
        response_document_paths = []
        
        defect_instance = self.get_queryset().first()
        defect_response_instance = self.get_queryset_response()
        for document in RequirementDefectResponseImage.objects.filter(defect_response__defect_id=defect_instance,
                                                                      defect_response = defect_response_instance):
                extension = document.document_path.split('.')[-1].lower()

                is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
                is_image = extension in ['jpg', 'jpeg', 'png', 'gif']  # Add more image extensions if needed
                
                response_document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path,
                    'id': document.id,
                    'is_video': is_video,
                    'is_image': is_image
                })
        return response_document_paths

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        defect_instance = self.get_queryset().first()
        
        defect_response_instance = {}
        response_document_paths= []
        
        if defect_instance:
            defect_response_instance = self.get_queryset_response()
            if defect_response_instance:
                defect_response_serializer =  self.serializer_class(instance=defect_response_instance)
                response_document_paths =  self.get_response_documents()
                
            else:
                defect_response_serializer =  self.serializer_class()
                
        else:
            messages.warning(request, "You are not authorized to perform this action")
            return redirect(reverse('requirement_list'))

        # Defect response doesn't exist, prepare context for displaying form
        context = {
            'defect_instance': defect_instance,
            'defect_response_serializer': defect_response_serializer,
            'document_paths':self.get_documents(),
            'defect_response_instance':defect_response_instance,
            'response_document_paths':response_document_paths
        }

        return render_html_response(context, self.template_name)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        data = request.data.copy()
        
        file_list = data.get('file_list', [])
        
        defect_instance = self.get_queryset().first()
        
        defect_response_instance = self.get_queryset_response()
        
        if not any(file_list):
            del data['file_list']
        
        serializer_data = request.data if any(file_list) else data
        
        if defect_response_instance:
            serializer = self.serializer_class(data=serializer_data, instance=defect_response_instance)  
            message = "Congratulations! Your response has been updated successfully."
        else:
            serializer = self.serializer_class(data= serializer_data)
            message = "Congratulations! Your response has been added successfully."
        
        if serializer.is_valid():
            if not defect_response_instance:
                serializer.validated_data['defect_id'] = defect_instance
                serializer.validated_data['surveyor'] = defect_instance.requirement_id.surveyor
            
            submit_type = request.POST.get('submit_type')
            serializer.validated_data['status'] = submit_type
            
            serializer.save()
            
            
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                # Redirect after successful POST
                return redirect(reverse('requirement_defect_detail', kwargs={'defect_id': request.data.get('defect_id')}))  
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {
                    'defect_instance': defect_instance,
                    'defect_response_serializer': serializer,
                    'document_paths':self.get_documents(),
                   
                }
                return render_html_response(context, self.template_name)

class RequirementDefectResponseDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementDefectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a customer.
        """
        # Get the customer instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        queryset = RequirementDefectResponse.objects.filter(pk= self.kwargs.get('pk'),status="draft")
        
        requirement_defect_response = queryset.first()
        
        if requirement_defect_response:
            # Proceed with the deletion
            requirement_defect_response.delete()
            messages.success(request, "Defect resposne has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement resposne has been deleted successfully!", )
        else:
            messages.error(request, "Resposne defect not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Resposne defect not found", )
                  

class RequirementDefectDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementDefectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'defects.html'
    swagger_schema = None
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a customer.
        """
        # Get the customer instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(requirement_id__user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping

        queryset = RequirementDefect.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        requirement_defect = queryset.first()
        
        if requirement_defect:
            # Proceed with the deletion
            requirement_defect.delete()
            messages.success(request, "requirement defect has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement defect has been deleted successfully!", )
        else:
            messages.error(request, "requirement defect not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="requirement defect not found", )
            

class RequirementRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a requirement.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a requirement.
        """
        requirement_id = kwargs.get('requirement_id')
        if requirement_id:
            requirement_instance = RequirementAsset.objects.filter(requirement_id=requirement_id, pk=  kwargs.get('document_id')).get()
            if requirement_instance and requirement_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = requirement_instance.document_path)
                requirement_instance.delete()
            return Response(
                {"message": "Your requirement has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
                  
class RequirementDefectRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a requirement defect.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a requirement defect.
        """
        defect_id = kwargs.get('defect_id')
        if defect_id:
            defect_instance = RequirementDocument.objects.filter(defect_id=defect_id, pk=kwargs.get('pk') ).get()
            if defect_instance and defect_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = defect_instance.document_path)
                defect_instance.delete()
            return Response(
                {"message": "Your requirement defect has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement Defect not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )