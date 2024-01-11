import re
import json
import time
import logging
from functools import wraps
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.dispatch import receiver, Signal
from authentication.models import InfinityLogs
SENSITIVE_KEYS = ['password', 'token', 'access', 'refresh']
    
api_request_logged = Signal()

previous_states = {}

http_status_codes = {
    # 1xx Informational Responses
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',
    103: 'Early Hints',

    # 2xx Success
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    # 3xx Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',

    # 4xx Client Errors
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Payload Too Large',
    414: 'URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    421: 'Misdirected Request',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    425: 'Too Early',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    451: 'Unavailable For Legal Reasons',

    # 5xx Server Errors
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    510: 'Not Extended',
    511: 'Network Authentication Required',
}


def capture_previous_state(get_instance_func, serializer_class, description, affected_module=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            instance = get_instance_func(self, *args, **kwargs)
            previous_states['prev_state'] = serializer_class(instance).data
            previous_states['affected_module'] = affected_module
            previous_states['description'] = description
            response = view_func(self, request, *args, **kwargs)
            return response

        return wrapper

    return decorator


def get_headers(request=None):
    regex = re.compile('^HTTP_')
    return dict((regex.sub('', header), value) for (header, value)
                in request.META.items() if header.startswith('HTTP_'))


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    except:
        return ''


def mask_sensitive_data(data, mask_api_parameters=False):
    SENSITIVE_KEYS = ['password', 'token', 'access', 'refresh']

    if type(data) != dict:
        if mask_api_parameters and type(data) == str:
            for sensitive_key in SENSITIVE_KEYS:
                data = re.sub('({}=)(.*?)($|&)'.format(sensitive_key), '\g<1>***FILTERED***\g<3>'.format(sensitive_key.upper()), data)
        return data

    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            data[key] = "***FILTERED***"

        if type(value) == dict:
            data[key] = mask_sensitive_data(data[key])

        if type(value) == list:
            data[key] = [mask_sensitive_data(item) for item in data[key]]

    return data


@receiver(api_request_logged)
def log_api_request(sender, **kwargs):
    request = kwargs.get('request')
    response = kwargs.get('response')
    api_route = resolve(request.path_info).route
    module_name = api_route.split('/')[0]
    namespace = resolve(request.path_info).namespace
    namespaces = ['admin', 'docs']

    if namespace in namespaces or api_route == 'dashboard/' or api_route == '':
        return response

    start_time = time.time()
    headers = get_headers(request=request)
    method = request.method
    request_data = kwargs.get('request_data')

    # Check if the request path starts with "auth" and, if true, remove request payload and body
    if api_route.startswith("auth"):
        request_data = None

    if response.get('content-type') in ('application/json', 'application/vnd.api+json', 'application/gzip', 'application/octet-stream', 'text/html; charset=utf-8'):
        if response.get('content-type') == 'application/gzip':
            response_body = '** GZIP Archive **'
        elif response.get('content-type') == 'application/octet-stream':
            response_body = '** Binary File **'
        elif getattr(response, 'streaming', False):
            response_body = '** Streaming **'

        api = request.build_absolute_uri()
        routes = ['auth/login/', 'auth/verify-token/<str:token>/', 'auth/confirm-email-update/', 'auth/forgot-password/', 'auth/reset-password/<str:token>/', 'auth/admin/activate/<str:token>/', 'operations/timezones/']
        username = [request.user.first_name if api_route not in routes and not isinstance(request.user, AnonymousUser) and request.user else None]
        user_id = [request.user.id if api_route not in routes and not isinstance(request.user, AnonymousUser) and request.user else 0][0]

        if request_data is not None:
                if not isinstance(request_data, str) and not isinstance(request_data, bytes):
                            request_payload = json.loads(mask_sensitive_data(request_data.decode('utf-8')))
                else:
                    request_payload = mask_sensitive_data(request_data)
        else:
                request_payload = None
        api = request.build_absolute_uri()
        response_body = response.data if hasattr(response, 'data') else None
        outcome = f'{http_status_codes.get(response.status_code, "Unknown")}'
        response_payload = mask_sensitive_data(response_body)
        response_body = response.data if hasattr(response, 'data') else None

        if response_body:
            if response.get('content-type') == 'application/gzip':
                response_payload = '** GZIP Archive **'
            elif response.get('content-type') == 'application/octet-stream':
                response_payload = '** Binary File **'
            elif getattr(response, 'streaming', False):
                response_payload = '** Streaming **'
            else:
                response_payload = mask_sensitive_data(response_body)
        else:
            response_payload = 'No response body'
            logging.basicConfig(level=logging.DEBUG)

        data = dict(
            api=mask_sensitive_data(api, mask_api_parameters=True),
            access_type=headers['USER_AGENT'].split('/')[0],
            ip_address=get_client_ip(request),
            page_slug=api_route,
            module=module_name,
            action_type=['create' if method == 'POST' else 'update' if method == 'PUT' or 'PATCH' else 'delete' if method == "DELETE" else 'get'][0],
            timestamp=timezone.now(),
            user_id=user_id,
            username=username[0],
            device_type=request.user_agent.device.family,
            browser=request.user_agent.browser,
            outcome=outcome,
            request_payload=request_payload,
            response_payload=response_payload,
            elapsed_time=time.time() - start_time,
            affected_modules=module_name,
            change_description=[previous_states['description'] if 'description' in previous_states else None][0],
            previous_state = (
            previous_states['prev_state']
            if 'prev_state' in previous_states and response_body and response_body.get('status') != 'error'
            else None
            ),

            user_role='admin',
            body=api_route,
            method=method,
            status_code=response.status_code,
        )
        InfinityLogs.objects.create(**data)
    else:
        return response

    return response

def get_client_ip(request):
    # Function to get the client's IP address from the request
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    except:
        return ''


def log_api_request(request, response):
    # Log the request and response or relevant information
    logging.debug(f"Request: {request}")
    logging.debug(f"Response: {response}")
    logging.basicConfig(level=logging.DEBUG)



    # Log the index and list length before accessing the index
    logging.debug(f"Index: {InfinityLogs}, List length: {len(50)}")

    # Log any relevant information after accessing the list
    logging.debug("Code after accessing the list")
   


def update_object(request, obj_id):
    # Get the existing object
    obj = InfinityLogs.objects.get(id=obj_id)
    
    # Capture the previous state
    previous_state = {
        'field1': obj.field1,
        'field2': obj.field2,
        # Add other fields as needed
    }
    
    # Update the object with the new data
    obj.field1 = request.data.get('field1', obj.field1)
    obj.field2 = request.data.get('field2', obj.field2)
    # Update other fields as needed
    obj.save()
    
    # Capture the new state
    new_state = {
        'field1': obj.field1,
        'field2': obj.field2,
        # Add other fields as needed
    }
    

