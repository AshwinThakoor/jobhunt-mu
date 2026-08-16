"""Django Admin registrations used by JobHunt MU operators."""
from django.contrib import admin
from .models import (
    UserProfile, CV, Company, Internship, Application, Payment,
    Recommendation, SavedJob, ImportRun, CareerDocument,
)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ('name','industry','location')

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('title','company','source_name','opportunity_type','work_mode','status','source_status','last_seen_at','posted_date')
    list_filter = ('status','source_status','source_name','opportunity_type','work_mode')
    search_fields = ('title','company__name','description','skills_required')

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('title','user','is_primary','validated','parsed_at','uploaded_at')
    search_fields = ('title','user__username','user__email')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user','internship','score','status','updated_at')
    list_filter = ('status',)

@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ('source_name','status','fetched_count','created_count','updated_count','archived_count','started_at','finished_at')
    list_filter = ('status','source_name')
    readonly_fields = ('started_at','finished_at')

@admin.register(CareerDocument)
class CareerDocumentAdmin(admin.ModelAdmin):
    list_display = ('title','user','internship','document_type','updated_at')
    list_filter = ('document_type','updated_at')
    search_fields = ('title','user__username','internship__title','internship__company__name')

admin.site.register([UserProfile, Application, Payment, SavedJob])
