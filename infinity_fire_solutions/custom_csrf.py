from django.middleware.csrf import CsrfViewMiddleware
from django.utils.decorators import decorator_from_middleware
from django.utils.functional import SimpleLazyObject
from django.utils.decorators import method_decorator

def is_api_request(request):
    # Determine if it's an API request based on the 'Accept' header
    return 'application/json' in request.META.get('HTTP_ACCEPT', '')

class CustomCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        print("is_api_request :: ", is_api_request(request))
        print("REQUEST TYPE :: ", request)
        if is_api_request(request):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return super().process_view(request, callback, callback_args, callback_kwargs)

csrf_exempt_for_api = decorator_from_middleware(CustomCsrfMiddleware)

class CustomCsrfMixin:
    @method_decorator(csrf_exempt_for_api)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

CustomCsrfView = csrf_exempt_for_api

def get_request():
    # Lazy object to access the request
    return SimpleLazyObject(lambda: _get_request())

def _get_request():
    # Get the current request from thread local storage
    return CustomCsrfMiddleware.get_request()
