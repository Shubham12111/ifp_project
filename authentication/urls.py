from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import LoginView, SignupView, ForgotPasswordView, ResetPasswordView,LogoutView, ProfileView, ChangePasswordView,EnforceChangePasswordView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/',  LogoutView.as_view(), name='logout'),

    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('profile/',  login_required(ProfileView.as_view()), name='profile'),
    path('change_password/',  ChangePasswordView.as_view(), name='change_password'),
    path('enforce/change_password/',  login_required(EnforceChangePasswordView.as_view()), name='enforce_password_change'),
    ]

