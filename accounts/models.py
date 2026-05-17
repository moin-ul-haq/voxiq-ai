from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    EXPERIENCE_CHOICES = [
        ('fresher', 'Fresher'),
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
    ]

    bio = models.TextField(blank=True)
    current_role = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        blank=True
    )
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    resume_text = models.TextField(blank=True)  # extracted text — used in AI system prompt
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email