from django.db import models
from django.utils import timezone

from accounts.models import Course, Section, StudentEnrollment, StudentProfile, Subject, User


class AttendanceSession(models.Model):
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'lecturer'},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Leave blank for 'All Sections'"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_feet = models.FloatField(help_text="Geofence radius in feet")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject.code} - {self.section} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def end_session(self):
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()

    def mark_absent_for_missing_students(self):
        """Create Absent records for students who haven't marked attendance."""
        # Get all student IDs enrolled in this course and semester for the subject
        enrolled_qs = StudentEnrollment.objects.filter(
            course=self.course,
            semester=self.semester,
            subjects=self.subject,
        )
        if self.section is not None:
            enrolled_qs = enrolled_qs.filter(section=self.section)
        enrolled_student_ids = enrolled_qs.values_list('student_id', flat=True)

        existing_student_ids = AttendanceRecord.objects.filter(
            session=self,
        ).values_list('student_id', flat=True)

        missing_ids = set(enrolled_student_ids) - set(existing_student_ids)

        for student_id in missing_ids:
            AttendanceRecord.objects.create(
                session=self,
                student_id=student_id,
                student_latitude=0.0,
                student_longitude=0.0,
                location_verified=False,
                face_verified=False,
                status='Absent',
            )


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    )

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    student_latitude = models.FloatField()
    student_longitude = models.FloatField()
    location_verified = models.BooleanField(default=False)
    face_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Absent')

    class Meta:
        unique_together = ['session', 'student']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.student.roll_no} - {self.session.subject.code} - {self.status}"


class StaffAttendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_attendance')
    date = models.DateField(auto_now_add=True)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    face_verified = models.BooleanField(default=False)
    location_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date} - {self.status}"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()  # JSON string
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.key


class HolidaySetting(models.Model):
    STATUS_CHOICES = (
        ('holiday', 'Holiday'),
        ('working', 'Working Day'),
    )

    date = models.DateField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {self.get_status_display()}"