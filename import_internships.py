"""Legacy data import helper retained for backward compatibility."""
import os
import django
import pandas as pd
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import Company, Internship

# Load your CSV or Excel file
# For CSV:
# df = pd.read_csv('interntrack_jobs.csv')
# For Excel:
df = pd.read_excel('interntrack_jobs.xlsx')
# Only keep internships
if 'job_type' in df.columns:
    df = df[df['job_type'].str.lower() == 'internship']

def to_list(val):
    if pd.isna(val) or val == '—':
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        # Split on common delimiters
        return [v.strip() for v in val.replace(';', ',').split(',') if v.strip()]
    return []

for idx, row in df.iterrows():
    company_name = row.get('company') or row.get('Company') or ''
    company, _ = Company.objects.get_or_create(name=company_name, defaults={
        'description': '',
        'location': row.get('location', ''),
        'industry': '',
    })

    # Avoid duplicates by checking title+company
    if Internship.objects.filter(title=row.get('job_title', row.get('Title', '')), company=company).exists():
        continue

    Internship.objects.create(
        company=company,
        title=row.get('job_title', row.get('Title', '')),
        description=row.get('description', '—'),
        requirements=row.get('requirements', '—'),
        responsibilities=row.get('responsibilities', '—'),
        location=row.get('location', row.get('Location', '')),
        duration=row.get('duration', '3 months'),
        stipend=row.get('stipend', row.get('salary', '')),
        skills_required=to_list(row.get('skills', '')),
        benefits=to_list(row.get('benefits', '')),
        application_deadline=row.get('deadline', datetime.now() + timedelta(days=30)),
        start_date=row.get('start_date', datetime.now() + timedelta(days=7)),
        end_date=row.get('end_date', datetime.now() + timedelta(days=90)),
        status='active'
    )

print("✔ All internships imported into your Django site!")
