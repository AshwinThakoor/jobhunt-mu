from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import Internship

class Command(BaseCommand):
    help = 'Close expired jobs and listings not seen for a configurable number of days.'
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=14)
        parser.add_argument('--dry-run', action='store_true')
    def handle(self, *args, **options):
        now=timezone.now(); today=timezone.localdate(); cutoff=now-timedelta(days=max(1, options['days']))
        qs=Internship.objects.filter(status='active').filter(models.Q(application_deadline__lt=today)|models.Q(last_seen_at__lt=cutoff))
        count=qs.count()
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'{count} jobs would be archived.')); return
        qs.update(status='closed', source_status='stale', expired_at=now, last_checked_at=now)
        self.stdout.write(self.style.SUCCESS(f'Archived {count} stale or expired jobs.'))

from django.db import models
