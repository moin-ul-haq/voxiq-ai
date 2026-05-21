from rest_framework import serializers
from .models import MockInterviewSession


class MockInterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockInterviewSession
        fields = [
            'id',
            'interview',
            'vapi_call_id',
            'status',
            'transcript',
            'evaluation',
            'duration_seconds',
            'started_at',
            'ended_at',
        ]
        read_only_fields = [
            'id',
            'interview',
            'vapi_call_id',
            'status',
            'transcript',
            'evaluation',
            'duration_seconds',
            'started_at',
            'ended_at',
        ]


class SessionStartResponseSerializer(serializers.Serializer):
    """Shape of response when session is initiated."""
    session_id = serializers.IntegerField()
    vapi_assistant_id = serializers.CharField()
    status = serializers.CharField()