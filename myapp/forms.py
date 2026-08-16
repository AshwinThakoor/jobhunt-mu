"""Django forms and validation for user, resume, opportunity, application, and payment workflows."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, CV, Internship, Application, Company, Payment
from django.core.validators import FileExtensionValidator
import json

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPES, required=True)
    phone = forms.CharField(max_length=15, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Update user profile fields (profile is created by signal)
            profile = user.userprofile
            profile.user_type = self.cleaned_data['user_type']
            profile.phone = self.cleaned_data.get('phone', '')
            profile.bio = self.cleaned_data.get('bio', '')
            profile.save()
        return user

class UserProfileForm(forms.ModelForm):
    skills = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter skills separated by commas'}), required=False)
    education = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter education details in JSON format'}), required=False)
    experience = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter experience details in JSON format'}), required=False)
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'bio', 'skills', 'education', 'experience', 'profile_picture']
    
    def clean_skills(self):
        skills = self.cleaned_data.get('skills', '')
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def clean_education(self):
        education = self.cleaned_data.get('education', '')
        if education:
            try:
                return json.loads(education)
            except json.JSONDecodeError:
                raise forms.ValidationError("Please enter valid JSON format for education")
        return []
    
    def clean_experience(self):
        experience = self.cleaned_data.get('experience', '')
        if experience:
            try:
                return json.loads(experience)
            except json.JSONDecodeError:
                raise forms.ValidationError("Please enter valid JSON format for experience")
        return []

class CVUploadForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = ['file', 'title']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter CV title'}),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 5MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 10MB")
            
            # Check file extension
            allowed_extensions = ['pdf', 'docx']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"Only {', '.join(allowed_extensions)} files are allowed")
        
        return file


class CVAnalysisForm(forms.Form):
    target_role = forms.CharField(
        max_length=120,
        required=False,
        label="Target role",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Junior Data Analyst",
                "autocomplete": "off",
            }
        ),
    )
    job_description = forms.CharField(
        max_length=8000,
        required=False,
        label="Job description",
        help_text=(
            "Optional, but recommended. Paste the responsibilities and requirements "
            "for a tailored skill-gap check."
        ),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Paste the relevant job advert here…",
            }
        ),
    )

class InternshipSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Job title, skill or company'}))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Location'}))
    opportunity_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All opportunity types')] + Internship.OPPORTUNITY_TYPE_CHOICES,
    )
    source = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All sources'),
            ('MyJob.mu', 'MyJob.mu'),
            ('Jobs.mu', 'Jobs.mu'),
            ('Mauritius Jobs', 'Mauritius Jobs'),
            ('Remotive', 'Remotive'),
            ('Freelancer.com', 'Freelancer.com'),
            ('Jooble', 'Jooble'),
        ],
    )
    duration = forms.ChoiceField(choices=[
        ('', 'Any Duration'),
        ('1-3 months', '1-3 months'),
        ('3-6 months', '3-6 months'),
        ('6+ months', '6+ months'),
    ], required=False)
    stipend_min = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'placeholder': 'Min stipend'}))
    skills = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Skills (comma separated)'}))

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cv', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Write your cover letter here...'
            }),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cv'].queryset = CV.objects.filter(user=user)

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'logo', 'website', 'location', 'industry', 'size', 'founded_year']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'founded_year': forms.NumberInput(attrs={'min': 1800, 'max': 2024}),
        }

class InternshipForm(forms.ModelForm):
    skills_required = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter skills separated by commas'}),
        required=False
    )
    benefits = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter benefits separated by commas'}),
        required=False
    )
    
    class Meta:
        model = Internship
        fields = [
            'title', 'description', 'requirements', 'responsibilities', 'location',
            'duration', 'stipend', 'application_deadline', 'start_date', 'end_date',
            'max_applications'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'responsibilities': forms.Textarea(attrs={'rows': 4}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_skills_required(self):
        skills = self.cleaned_data.get('skills_required', '')
        if skills:
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return []
    
    def clean_benefits(self):
        benefits = self.cleaned_data.get('benefits', '')
        if benefits:
            return [benefit.strip() for benefit in benefits.split(',') if benefit.strip()]
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        application_deadline = cleaned_data.get('application_deadline')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date")
        
        if application_deadline and start_date and application_deadline >= start_date:
            raise forms.ValidationError("Application deadline must be before start date")
        
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_type', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default amounts based on payment type
        self.fields['amount'].widget.attrs.update({'readonly': 'readonly'})
    
    def clean_amount(self):
        payment_type = self.cleaned_data.get('payment_type')
        amount = self.cleaned_data.get('amount')
        
        # Set standard amounts for different payment types
        if payment_type == 'application_fee':
            return 10.00
        elif payment_type == 'premium_subscription':
            return 29.99
        elif payment_type == 'cv_review':
            return 15.00
        
        return amount 
