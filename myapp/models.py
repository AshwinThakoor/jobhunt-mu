"""Persistent domain models for accounts, opportunities, resumes, matching, billing, and imports."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

def cv_upload_path(instance, filename):
    """Generate file path for CV uploads"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_{uuid.uuid4()}.{ext}"
    return os.path.join('cvs', filename)

class UserProfile(models.Model):
    USER_TYPES = [
        ('student', 'Student'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=cv_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    title = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True, null=True)
    extracted_text = models.TextField(blank=True, default='')
    extracted_skills = models.JSONField(default=list, blank=True)
    extraction_warnings = models.JSONField(default=list, blank=True)
    parsed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other CVs for this user as non-primary
            CV.objects.filter(user=self.user).update(is_primary=False)
        super().save(*args, **kwargs)

class Company(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    logo_source_url = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    size = models.CharField(max_length=50, blank=True, null=True)
    founded_year = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Internship(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    ]

    OPPORTUNITY_TYPE_CHOICES = [
        ('local', 'Mauritius job'),
        ('internship', 'Internship'),
        ('graduate', 'Graduate role'),
        ('remote', 'Remote job'),
        ('freelance', 'Freelance project'),
    ]

    WORK_MODE_CHOICES = [
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
        ('unspecified', 'Not specified'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    location = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, default="Not specified")
    job_type = models.CharField(max_length=50, default="Internship")
    opportunity_type = models.CharField(
        max_length=20,
        choices=OPPORTUNITY_TYPE_CHOICES,
        default='local',
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODE_CHOICES,
        default='unspecified',
    )
    stipend = models.CharField(max_length=100, blank=True, null=True)
    skills_required = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    application_deadline = models.DateField(blank=True, null=True)
    posted_date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    max_applications = models.IntegerField(default=100)
    current_applications = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_premium = models.BooleanField(default=False)
    external_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    source_name = models.CharField(max_length=100, default="JobHunt MU")
    source_url = models.URLField(max_length=500, unique=True, blank=True, null=True)
    scraped_at = models.DateTimeField(blank=True, null=True)
    first_seen_at = models.DateTimeField(blank=True, null=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    last_checked_at = models.DateTimeField(blank=True, null=True)
    expired_at = models.DateTimeField(blank=True, null=True)
    source_status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_date", "-created_at"]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    @property
    def is_open(self):
        deadline_is_open = (
            not self.application_deadline
            or self.application_deadline >= timezone.localdate()
        )
        return (
            self.status == 'active'
            and self.current_applications < self.max_applications
            and deadline_is_open
        )

class Application(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'internship']
    
    def __str__(self):
        return f"{self.user.username} - {self.internship.title}"
    
    def save(self, *args, **kwargs):
        if self.pk is None:  # New application
            self.internship.current_applications += 1
            self.internship.save()
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('application_fee', 'Application Fee'),
        ('premium_subscription', 'Premium Subscription'),
        ('cv_review', 'CV Review'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_checkout_session_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.payment_type} - {self.amount}"

class Recommendation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('saved', 'Saved'),
        ('dismissed', 'Not interested'),
        ('applied', 'Applied'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE)
    score = models.FloatField()  # Explainable match score from 0 to 1.
    reason = models.TextField()
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    match_confidence = models.CharField(max_length=10, default='medium')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'internship']
    
    def __str__(self):
        return f"{self.user.username} - {self.internship.title} (Score: {self.score})"



class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'internship'], name='unique_saved_job')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.internship.title}"


class CareerDocument(models.Model):
    DOCUMENT_TYPES = [
        ('tailored_resume', 'Tailored resume'),
        ('cover_letter', 'Cover letter'),
        ('application_email', 'Application email'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_documents')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='career_documents')
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='career_documents')
    document_type = models.CharField(max_length=24, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=240)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()} - {self.internship.title}"


class ImportRun(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    source_name = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    archived_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def duration_seconds(self):
        end = self.finished_at or timezone.now()
        return max(0, int((end - self.started_at).total_seconds()))

    def __str__(self):
        return f"{self.source_name} - {self.status} - {self.started_at:%Y-%m-%d %H:%M}"


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=500)
    filters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.query[:50]}"

# Keep the existing models for backward compatibility
class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.student_id})"

class StudentRecord(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    database_design_and_implementation = models.IntegerField()
    cloud_computing_and_techniques = models.IntegerField()
    python_programming_methodology_2 = models.IntegerField()
    internet_of_things_design_principles = models.IntegerField()
    big_data_architecture_and_programming = models.IntegerField()
    network_technologies_and_design = models.IntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class ModuleMark(models.Model):
    student = models.ForeignKey(StudentRecord, on_delete=models.CASCADE)
    module_name = models.CharField(max_length=100)
    mark = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"{self.student} - {self.module_name}: {self.mark}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
