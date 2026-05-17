from django.db import models
from interviews.models import Interview


class MockInterviewSession(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='mock_sessions'
    )
    vapi_call_id = models.CharField(max_length=200, blank=True)
    vapi_assistant_id = models.CharField(max_length=200, blank=True)  # temp — deleted after call
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    transcript = models.JSONField(blank=True, null=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.vapi_call_id} — {self.status}"