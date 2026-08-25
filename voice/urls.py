from django.urls import path
from .views import (
    SessionStartView,
    SessionListView,
    SessionDetailView,
    VapiWebhookView,
    check_health
)

urlpatterns = [
    # Session endpoints
    path('interviews/<int:pk>/session/start/', SessionStartView.as_view(), name='session-start'),
    path('interviews/<int:pk>/sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<int:session_id>/', SessionDetailView.as_view(), name='session-detail'),
    path('health/', check_health, name='check_health'),

    # VAPI webhook — no JWT auth, secured via secret header
    path('webhook/vapi/', VapiWebhookView.as_view(), name='vapi-webhook'),
]