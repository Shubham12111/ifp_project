from drf_yasg import openapi

def get_status_from_code(status_code):
    """
    Returns the status of an HTTP response based on its status code.

    Parameters:
    status_code (int): The HTTP status code.

    Returns:
    str: The status of the response.
    """
    if status_code >= 200 and status_code < 300:
        return 'success'
    elif status_code >= 400 and status_code < 500:
        return 'warning'
    else:
        return 'error'



def docs_schema_response_new(status_code: str, 
                         message: str, 
                         paginated_response : bool = False,
                         serializer_class: any =None, 
                         is_list: bool = False, 
):  
    status = get_status_from_code(status_code)
    if serializer_class:
        
        if serializer_class :
            serializer = serializer_class(data={})
            serializer.is_valid()
        
        if status.lower() == "success":
            nullable = False
            
            data = serializer_class().data if not is_list else [serializer_class().data]
            
            if not paginated_response:    
                response = {
                    'status': status,
                    'message': message,
                    'data': data
                }
            else:
                response = {
                'status': status,
                'message': message,
                'data': {
                    'count': 1,
                    'next': 'https://www.example.com/?page=3',
                    'previous': 'https://www.example.com/?page=1',
                    'data': data
                }
            }
        else:
            nullable = True
            response = {
            'status':status,
            'message':message,
            'data':serializer.errors
            }
    else:
        nullable = True
        response = {
            'status':status,
            'message':message
            }

    
    response = openapi.Response(
                    description=status,
                    examples={
                        'application/json': response
                    },
                    
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type='string', description=status),
                            'message': openapi.Schema(type='string', description=message),
                            'data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=nullable,  )
                            },
                        required=['status', 'message', 'data']
                    ),
            )
    
    
    return response