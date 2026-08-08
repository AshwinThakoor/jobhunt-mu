from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.internship_list, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Internship URLs
    path('internships/', views.internship_list, name='internship_list'),
    path('internships/<int:pk>/', views.internship_detail, name='internship_detail'),
    path('internships/<int:pk>/apply/', views.apply_internship, name='apply_internship'),
    path('internships/<int:pk>/studio/', views.application_studio, name='application_studio'),
    path('career-documents/<int:pk>/', views.career_document_edit, name='career_document_edit'),
    path('career-documents/<int:pk>/download/', views.career_document_download, name='career_document_download'),
    
    # CV Management
    path('cvs/', views.cv_list, name='cv_list'),
    path('cvs/<int:pk>/', views.cv_detail, name='cv_detail'),
    path('cvs/<int:pk>/analyze/', views.cv_analyze, name='cv_analyze'),
    path('cvs/<int:pk>/delete/', views.cv_delete, name='cv_delete'),
    path('cvs/<int:pk>/set-primary/', views.set_primary_cv, name='set_primary_cv'),
    
    # Application Tracking
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Payment
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.create_payment, name='create_payment'),
    path('payments/webhook/', views.stripe_webhook, name='payment_webhook'),
    path('payments/success/', views.payment_success, name='payment_success'),
    path('payments/confirm-success/', views.confirm_premium_success, name='confirm_premium_success'),
    
    # Recommendations and Roadmap
    path('recommendations/', views.recommendations, name='recommendations'),
    path('recommendations/<int:pk>/action/', views.recommendation_action, name='recommendation_action'),
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    path('roadmap/', views.roadmap, name='roadmap'),
    
    # Employer URLs
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/company/create/', views.create_company, name='create_company'),
    path('employer/internship/create/', views.create_internship, name='create_internship'),
    
    # Legacy URLs (for backward compatibility)
    path('form/', views.user_form, name='user_form'),
    path('view-records/', views.view_records, name='view_records'),
    path('home/', views.home, name='home_legacy'),
    path('portal/', views.portal, name='portal'),
    path('download-internships-excel/', views.download_internships_excel, name='download_internships_excel'),
]
