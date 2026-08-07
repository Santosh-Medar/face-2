from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import StudentProfile, Course, Section, StaffProfile

User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)
    phone_number = forms.CharField(max_length=15, required=False)
    assigned_course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False)

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'user_type', 'assigned_course', 'password1', 'password2'
        )


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'user_type', 'assigned_course', 'is_active'
        )


class StudentProfileForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    semester = forms.IntegerField(min_value=1)
    section = forms.ModelChoiceField(queryset=Section.objects.all())
    roll_no = forms.CharField(max_length=20)

    class Meta:
        model = StudentProfile
        fields = ('roll_no', 'department', 'face_image')


class StaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[('', '--------')] + [(d, d) for d in ['FDA', 'SDA', 'Peon', 'Lab Attender', 'Sweeper']],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class TeachingStaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[
            ('', '--------'),
            ('Professor', 'Professor'),
            ('Associate Professor', 'Associate Professor'),
            ('Assistant Professor', 'Assistant Professor'),
            ('Lecturer/Instructor', 'Lecturer/Instructor')
        ],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class NonTeachingStaffProfileForm(forms.ModelForm):
    designation = forms.ChoiceField(
        choices=[('', '--------')] + [
            ('FDA', 'FDA'),
            ('SDA', 'SDA'),
            ('Peon', 'Peon'),
            ('Lab Attender', 'Lab Attender'),
            ('Sweeper', 'Sweeper')
        ],
        required=False
    )

    class Meta:
        model = StaffProfile
        fields = ('employee_id', 'department', 'designation', 'face_image')
        widgets = {
            'face_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class BulkUploadForm(forms.Form):
    user_type = forms.ChoiceField(choices=[
        ('student', 'Student'),
        ('lecturer', 'Teaching Staff'),
        ('staff', 'Non-Teaching Staff')
    ])
    excel_file = forms.FileField(label='Excel File (.xlsx)')


# accounts/forms.py

class StudentRegistrationForm(forms.Form):
    student_name = forms.CharField(max_length=100, label="Student Name")
    uucms_id = forms.CharField(max_length=20, label="UUCMS ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    face_image = forms.ImageField(required=False, label="Face Image")

    course = forms.ModelChoiceField(queryset=Course.objects.all().order_by('code'), label="Course")
    semester = forms.ChoiceField(
        choices=[(1, '1'), (3, '3'), (5, '5')],
        label="Semester",
        initial=1,
    )
    section = forms.ModelChoiceField(queryset=Section.objects.none(), label="Section")

    LANGUAGE_CHOICES = [('KAN', 'Kannada'), ('HIN', 'Hindi')]
    language1 = forms.ChoiceField(choices=LANGUAGE_CHOICES, label="Language 1")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'course' in self.data and 'semester' in self.data:
            try:
                course_id = int(self.data.get('course'))
                semester = int(self.data.get('semester'))
                self.fields['section'].queryset = Section.objects.filter(course_id=course_id, semester=semester)
            except (ValueError, TypeError):
                pass
        else:
            self.fields['section'].queryset = Section.objects.none()

    def clean_face_image(self):
        face_image = self.cleaned_data.get('face_image')
        if face_image:
            from attendance.utils import encode_face_from_image
            encoding = encode_face_from_image(face_image)
            if encoding is None:
                raise forms.ValidationError(
                    "No face detected in the image. Please upload a clear frontal face photo."
                )
            # Store encoding temporarily (will be re-generated in view for safety)
            self._face_encoding = encoding
        return face_image

    def clean_uucms_id(self):
        uucms_id = self.cleaned_data.get('uucms_id')
        if User.objects.filter(username=uucms_id).exists():
            raise forms.ValidationError("This UUCMS ID is already registered.")
        return uucms_id

    def clean_student_name(self):
        name = self.cleaned_data.get('student_name').strip()
        if not name:
            raise forms.ValidationError("Student name is required.")
        return name
    
# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model
from accounts.models import Course, StaffProfile

User = get_user_model()

class TeachingStaffRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    username = forms.CharField(max_length=150, label="Employee ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Course")
    designation = forms.ChoiceField(
        choices=[
            ('', 'Select Designation'),
            ('Professor', 'Professor'),
            ('Associate Professor', 'Associate Professor'),
            ('Assistant Professor', 'Assistant Professor'),
            ('Lecturer/Instructor', 'Lecturer/Instructor'),
        ],
        label="Designation"
    )
    face_image = forms.ImageField(required=False, label="Face Image")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Employee ID is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

# accounts/forms.py
class NonTeachingStaffRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    username = forms.CharField(max_length=150, label="Employee ID")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    designation = forms.ChoiceField(choices=[
        ('', 'Select Designation'),
        ('FDA', 'FDA'),
        ('SDA', 'SDA'),
        ('Peon', 'Peon'),
        ('Lab Attender', 'Lab Attender'),
        ('Sweeper', 'Sweeper'),
    ], label="Designation")
    face_image = forms.ImageField(required=False, label="Face Image")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This Employee ID is already registered.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email