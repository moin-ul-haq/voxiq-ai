from django.urls import path
from .views import (
    SessionStartView,
    SessionListView,
    SessionDetailView,
    VapiWebhookView,
)

urlpatterns = [
    # Session endpoints
    path('interviews/<int:pk>/session/start/', SessionStartView.as_view(), name='session-start'),
    path('interviews/<int:pk>/sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<int:session_id>/', SessionDetailView.as_view(), name='session-detail'),

    # VAPI webhook — no JWT auth, secured via secret header
    path('webhook/vapi/', VapiWebhookView.as_view(), name='vapi-webhook'),
]