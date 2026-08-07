from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Course,
    Section,
    StaffProfile,
    StudentEnrollment,
    StudentProfile,
    Subject,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "user_type",
        "assigned_course",
        "is_staff",
        "is_active",
    )
    list_filter = ("user_type", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Information", {"fields": ("user_type", "phone_number", "assigned_course")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Information", {"classes": ("wide",), "fields": ("user_type", "phone_number", "assigned_course")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "roll_no", "department", "registration_complete")
    list_filter = ("department", "registration_complete")
    search_fields = ("roll_no", "user__first_name", "user__last_name", "user__username")
    readonly_fields = ("face_encoding",)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "department", "designation", "registration_complete")
    list_filter = ("department", "designation", "registration_complete")
    search_fields = ("employee_id", "user__first_name", "user__last_name", "user__username")
    readonly_fields = ("face_encoding",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "course_type", "duration_years")
    search_fields = ("code", "name")
    list_filter = ("department", "course_type")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "course", "semester")
    search_fields = ("code", "name")
    list_filter = ("course", "semester")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "semester")
    list_filter = ("course", "semester")
    search_fields = ("name",)


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "semester", "section")
    list_filter = ("course", "semester", "section")
    search_fields = ("student__roll_no", "student__user__first_name", "student__user__last_name")
    filter_horizontal = ("subjects",)