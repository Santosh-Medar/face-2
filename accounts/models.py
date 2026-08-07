import json
import numpy as np

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('principal', 'Principal'),
        ('hod', 'HOD'),
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
        ('staff', 'Non‑Teaching Staff'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    assigned_course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='hod_user')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.user_type})"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    face_encoding = models.TextField(blank=True, null=True)
    face_image = models.ImageField(upload_to='face_images/', blank=True, null=True)
    registration_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.roll_no} - {self.user.get_full_name()}"

    def set_face_encoding(self, encoding_array):
        """Store face encoding as JSON string"""
        if isinstance(encoding_array, np.ndarray):
            encoding_list = encoding_array.tolist()
            self.face_encoding = json.dumps(encoding_list)

    def get_face_encoding(self):
        """Retrieve face encoding as numpy array"""
        if self.face_encoding:
            encoding_list = json.loads(self.face_encoding)
            return np.array(encoding_list)
        return None


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    course_type = models.CharField(max_length=2, choices=[('UG', 'UG'), ('PG', 'PG')], default='UG')
    duration_years = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()

    class Meta:
        unique_together = ['code', 'course', 'semester']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Section(models.Model):
    name = models.CharField(max_length=10)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()

    class Meta:
        unique_together = ['name', 'course', 'semester']

    def __str__(self):
        return f"Section {self.name}"


class StudentEnrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject)

    class Meta:
        unique_together = ['student', 'course', 'semester']

    def __str__(self):
        return f"{self.student.roll_no} - {self.course.code} Sem {self.semester}"


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True)
    face_image = models.ImageField(upload_to='staff_faces/', blank=True, null=True)
    registration_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id or 'No ID'}"

    def set_face_encoding(self, encoding_array):
        """Store face encoding as JSON string"""
        if isinstance(encoding_array, np.ndarray):
            encoding_list = encoding_array.tolist()
            self.face_encoding = json.dumps(encoding_list)

    def get_face_encoding(self):
        """Retrieve face encoding as numpy array"""
        if self.face_encoding:
            encoding_list = json.loads(self.face_encoding)
            return np.array(encoding_list)
        return None