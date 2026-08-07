from django.urls import path

from attendance.views import (
    admin_holiday_calendar,
    admin_set_holiday_reason,
    admin_toggle_holiday,
)
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Face Registration
    path('face-registration/', views.face_registration_view, name='face_registration'),
    path('update-face-encoding/', views.update_face_encoding, name='update_face_encoding'),

    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # Student Management (Lecturer only)
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),

    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/register/', views.admin_register_choice, name='admin_register_choice'),
    path('admin/register/student/', views.admin_register_student, name='admin_register_student'),
    path('admin/register/teaching/', views.admin_register_teaching, name='admin_register_teaching'),
    path('admin/register/nonteaching/', views.admin_register_nonteaching, name='admin_register_nonteaching'),

    path('admin/students/', views.admin_student_list, name='admin_student_list'),
    path('admin/teaching/', views.admin_teaching_list, name='admin_teaching_list'),
    path('admin/nonteaching/', views.admin_nonteaching_list, name='admin_nonteaching_list'),

    path('admin/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/bulk-register/', views.admin_bulk_register, name='admin_bulk_register'),
    path('admin/download-sample/<str:user_type>/', views.admin_download_sample, name='admin_download_sample'),

    # Holiday management
    path('admin/holidays/', admin_holiday_calendar, name='admin_holiday_calendar'),
    path('admin/holidays/<int:year>/<int:month>/', admin_holiday_calendar, name='admin_holiday_calendar_month'),
    path('admin/toggle-holiday/', admin_toggle_holiday, name='admin_toggle_holiday'),
    path('admin/set-holiday-reason/', admin_set_holiday_reason, name='admin_set_holiday_reason'),
]