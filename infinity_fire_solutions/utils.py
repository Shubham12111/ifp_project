import random
import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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

def validate_generated_password(value):
    # Validate password complexity
    validate_password(value)

    # Custom validation rules
    if 'password' in value.lower():
        raise ValidationError('Password should not contain the word "password".')
    if len(value) < 8:
        raise ValidationError('Password should be at least 8 characters long.')
    if value.isnumeric() or value.isalpha():
        raise ValidationError('Password should contain a mix of letters, numbers, and symbols.')
    if not any(char.isupper() for char in value):
        raise ValidationError('Password should contain a capital character')
    if not re.search(r"[!@#$%^&*()\-=_+{}[\]|\\:;\"'<>,.?/]", value):
        raise ValidationError("Password must contain at least one special character.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one numeric character.")
    return value

def generate_random_password(length=12):
    """
    Generate a random password of the specified length.

    Parameters:
    - length: The length of the generated password. Default is 12.

    Returns:
    - A randomly generated password as a string.
    """
    
    while True:
        password = ''.join(random.choice('!@#$%^&*()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(length))

        # Validate the generated password
        errors = []

        try:
            validate_generated_password(password)
        except ValidationError as e:
            errors.extend(e.messages)

        if not errors:
            break

    return password