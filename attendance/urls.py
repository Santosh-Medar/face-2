from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Lecturer & student dashboards
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    # Attendance session management
    path('start-session/', views.start_session, name='start_session'),
    path('session/<int:session_id>/', views.session_monitor, name='session_monitor'),
    path('session/<int:session_id>/end/', views.end_session, name='end_session'),
    path('session/<int:session_id>/take/', views.take_attendance, name='take_attendance'),
    path('session/<int:session_id>/records/', views.get_session_records, name='get_session_records'),

    # API endpoints for dynamic forms
    path('api/sections/<int:course_id>/<int:semester>/', views.get_sections, name='get_sections'),
    path('api/subjects/<int:course_id>/<int:semester>/', views.get_subjects, name='get_subjects'),

    # Principal dashboard and staff management
    path('principal/', views.principal_dashboard, name='principal_dashboard'),
    path('principal/teaching-staff/', views.principal_teaching_staff, name='principal_teaching_staff'),
    path('principal/non-teaching-staff/', views.principal_non_teaching_staff, name='principal_non_teaching_staff'),
    path('principal/staff/<int:user_id>/', views.principal_staff_detail, name='principal_staff_detail'),
    path('principal/non-teaching-staff/<int:staff_id>/', views.principal_non_teaching_staff_detail,
         name='principal_non_teaching_staff_detail'),
    path('principal/search-students/', views.principal_search_students, name='principal_search_students'),

    # Catch‑all for principal course types – must be LAST
    path('principal/<str:type>/', views.principal_course_types, name='principal_course_types'),

    # Course navigation (shared between principal and HOD)
    path('course/<int:course_id>/years/', views.principal_course_years, name='course_years'),
    path('course/<int:course_id>/year/<int:year>/sections/', views.course_year_sections,
         name='course_year_sections'),
    path('course/<int:course_id>/year/<int:year>/section/<int:section_id>/students/',
         views.section_students, name='section_students'),

    # Student attendance detail
    path('student/<int:student_id>/course/<int:course_id>/attendance/',
         views.student_attendance_detail, name='student_attendance_detail'),

    # HOD URLs
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/faculty/', views.hod_faculty_list, name='hod_faculty_list'),

    # Lecturer mark attendance
    path('lecturer/mark-attendance/', views.lecturer_mark_attendance, name='lecturer_mark_attendance'),

    # Staff (non-teaching) URLs
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/mark-attendance/', views.staff_mark_attendance, name='staff_mark_attendance'),
    path('staff/attendance-history/', views.staff_attendance_history, name='staff_attendance_history'),

    # Lecturer history
    path('lecturer/history/', views.lecturer_history, name='lecturer_history'),
    path('lecturer/history/mine/', views.lecturer_my_attendance, name='lecturer_my_attendance'),
    path('lecturer/history/students/', views.lecturer_student_sessions, name='lecturer_student_sessions'),
    path('lecturer/history/students/session/<int:session_id>/', views.lecturer_session_detail,
         name='lecturer_session_detail'),
]