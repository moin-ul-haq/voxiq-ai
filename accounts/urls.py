from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ResumeUploadView,
    CompleteOnboardingView,
    OAuthAuthURLView,
    OAuthCallbackView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/resume/', ResumeUploadView.as_view(), name='resume-upload'),
    path('onboarding/complete/', CompleteOnboardingView.as_view(), name='onboarding-complete'),

    # OAuth API endpoints
    path('oauth/<str:provider>/auth-url/', OAuthAuthURLView.as_view(), name='oauth-auth-url'),
    path('oauth/<str:provider>/callback/', OAuthCallbackView.as_view(), name='oauth-callback'),
]