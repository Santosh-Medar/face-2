from django.contrib import admin

from .models import (
    AttendanceRecord,
    AttendanceSession,
    HolidaySetting,
    StaffAttendance,
    SystemSetting,
)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "course",
        "semester",
        "section",
        "lecturer",
        "is_active",
        "created_at",
        "ended_at",
    )
    list_filter = ("course", "semester", "section", "subject", "is_active")
    search_fields = (
        "subject__name",
        "subject__code",
        "lecturer__first_name",
        "lecturer__last_name",
        "lecturer__username",
    )
    readonly_fields = ("created_at", "ended_at")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "session",
        "status",
        "face_verified",
        "location_verified",
        "timestamp",
    )
    list_filter = ("status", "face_verified", "location_verified", "session__subject", "session__course")
    search_fields = (
        "student__roll_no",
        "student__user__first_name",
        "student__user__last_name",
        "session__subject__code",
    )
    readonly_fields = ("timestamp",)


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "time_in", "time_out", "status", "face_verified", "location_verified")
    list_filter = ("status", "date", "face_verified", "location_verified")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    readonly_fields = ("date", "time_in")


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "description")
    search_fields = ("key", "description")


@admin.register(HolidaySetting)
class HolidaySettingAdmin(admin.ModelAdmin):
    list_display = ("date", "status")
    list_filter = ("status",)
    search_fields = ("date",)