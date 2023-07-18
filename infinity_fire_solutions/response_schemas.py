from django.http import JsonResponse


def convert_serializer_errors(errors):
    """
    Converts a Django serializer error object into a standardized API response.

    Parameters:
    errors (dict): A Django serializer error object.

    Returns:
    dict: A standardized API response.
    """
    data = {}

    for field, field_errors in errors.items():
        error_list = []
        for field_error in field_errors:
            error_list.append(str(field_error))
        data[field] = error_list[0]
    return data

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
        return 'error'
    else:
        return 'error'

def create_api_response(status_code, message, data=None):
    """
    Creates a standardized API response.

    Parameters:
    status_code (int): The HTTP status code of the response.
    message (str): A human-readable message providing more information about the response.
    data (dict or None): Additional data that may be relevant to the response.

    Returns:
    JsonResponse: A standardized JSON API response.
    """
    try:
        response = {
            'status': get_status_from_code(status_code),
            'message': message
        }
        if data is not None:
            response['data'] = data
        return JsonResponse(response, status=status_code)
    except Exception as e:
        error_message = f"Error creating API response: {e}"
        error_data = {'error': str(e)}
        return JsonResponse({
            'status': 'error',
            'message': error_message,
            'data': error_data
        }, status=500)