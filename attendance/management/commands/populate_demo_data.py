# attendance/management/commands/populate_demo_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, Course, Subject, Section, StudentEnrollment
from attendance.models import AttendanceSession, AttendanceRecord
import json
import numpy as np
import random
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate medium demo data with Principal, HODs (course-based), and students'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🚀 CREATING DEMO DATA WITH COURSE-BASED HODs'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        # Step 1: Clear all existing data
        self.clear_all_data()
        
        # Step 2: Create courses first (needed for HOD assignment)
        self.create_courses()
        
        # Step 3: Create users (Principal, HODs, Lecturers, Students)
        self.create_principal_and_hod()
        self.create_lecturers()
        
        # Step 4: Create sections and subjects
        self.create_sections()
        self.create_subjects()
        
        # Step 5: Create students and enrollments
        self.create_students()
        self.create_enrollments()
        
        # Step 6: Create demo attendance sessions
        self.create_demo_attendance()
        
        # Step 7: Print summary
        self.print_summary()

    def clear_all_data(self):
        """Clear all existing data"""
        self.stdout.write('\n📌 Clearing all existing data...')
        AttendanceRecord.objects.all().delete()
        AttendanceSession.objects.all().delete()
        StudentEnrollment.objects.all().delete()
        Subject.objects.all().delete()
        Section.objects.all().delete()
        StudentProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Course.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('  ✅ All data cleared!'))

    def create_courses(self):
        """Create courses with UG/PG classification"""
        self.stdout.write('\n📌 Creating Courses...')
        
        courses_data = [
            # UG Courses (3 years)
            ('BCA', 'Bachelor of Computer Applications', 'UG', 3),
            ('BBA', 'Bachelor of Business Administration', 'UG', 3),
            ('BCOM', 'Bachelor of Commerce', 'UG', 3),
            ('BA', 'Bachelor of Arts', 'UG', 3),
            ('BSC', 'Bachelor of Science', 'UG', 3),
            
            # PG Courses (2 years)
            ('MCA', 'Master of Computer Applications', 'PG', 2),
            ('MBA', 'Master of Business Administration', 'PG', 2),
            ('MCOM', 'Master of Commerce', 'PG', 2),
            ('MA', 'Master of Arts', 'PG', 2),
            ('MSC', 'Master of Science', 'PG', 2),
        ]
        
        self.courses = {}
        for code, name, course_type, duration in courses_data:
            course = Course.objects.create(
                code=code,
                name=name,
                department=code,
                course_type=course_type,
                duration_years=duration
            )
            self.courses[code] = course
            self.stdout.write(f'  ✅ {code} ({course_type}) - {name} [{duration} years]')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(self.courses)} courses'))

    def create_principal_and_hod(self):
        """Create Principal and Course-based HOD users"""
        self.stdout.write('\n📌 Creating Principal and HODs...')
        
        # Principal
        self.principal = User.objects.create_user(
            username='principal',
            password='principal123',
            first_name='Dr. Suresh',
            last_name='Kumar',
            email='principal@college.edu',
            user_type='principal',
            phone_number='9876543200'
        )
        self.stdout.write(f'  ✅ Principal: {self.principal.get_full_name()}')
        
        # HODs - One for each major course
        hod_assignments = [
            ('hod_bca', 'Dr. Ramesh', 'Gupta', 'BCA', 'Computer Science'),
            ('hod_bba', 'Dr. Sunita', 'Sharma', 'BBA', 'Business Administration'),
            ('hod_bcom', 'Dr. Prakash', 'Rao', 'BCOM', 'Commerce'),
            ('hod_ba', 'Dr. Meera', 'Patel', 'BA', 'Arts'),
            ('hod_bsc', 'Dr. Vikram', 'Singh', 'BSC', 'Science'),
            ('hod_mca', 'Dr. Anil', 'Kumar', 'MCA', 'Computer Science'),
            ('hod_mba', 'Dr. Priya', 'Joshi', 'MBA', 'Business Administration'),
            ('hod_mcom', 'Dr. Venkat', 'Rao', 'MCOM', 'Commerce'),
            ('hod_ma', 'Dr. Kavita', 'Das', 'MA', 'Arts'),
            ('hod_msc', 'Dr. Harish', 'Nair', 'MSC', 'Science'),
        ]
        
        self.hods = {}
        for username, first, last, course_code, display_dept in hod_assignments:
            hod = User.objects.create_user(
                username=username,
                password='hod123',
                first_name=first.replace('Dr. ', ''),
                last_name=last,
                email=f'{username}@college.edu',
                user_type='hod',
                phone_number=f'98{random.randint(10000000, 99999999)}',
                assigned_course=self.courses[course_code]
            )
            self.hods[course_code] = hod
            self.stdout.write(f'  ✅ HOD for {course_code}: {first} {last}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created 1 Principal + {len(self.hods)} HODs'))

    def create_lecturers(self):
        """Create lecturers for each course"""
        self.stdout.write('\n📌 Creating Lecturers...')
        
        lecturers_data = [
            # BCA Lecturers
            ('dr.verma', 'Dr. Rajesh', 'Verma', 'BCA'),
            ('prof.gupta', 'Prof. Anita', 'Gupta', 'BCA'),
            ('dr.kumar_cs', 'Dr. Sanjay', 'Kumar', 'BCA'),
            
            # BBA Lecturers
            ('prof.shah', 'Prof. Deepak', 'Shah', 'BBA'),
            ('dr.joshi_bba', 'Dr. Priya', 'Joshi', 'BBA'),
            
            # BCOM Lecturers
            ('prof.rao', 'Prof. Venkat', 'Rao', 'BCOM'),
            ('dr.nair', 'Dr. Lakshmi', 'Nair', 'BCOM'),
            
            # Other courses
            ('prof.das', 'Prof. Amit', 'Das', 'BA'),
            ('dr.singh_arts', 'Dr. Harpreet', 'Singh', 'BA'),
            ('prof.kumar_mca', 'Prof. Suresh', 'Kumar', 'MCA'),
            ('dr.patel_mba', 'Dr. Mehta', 'Patel', 'MBA'),
            ('prof.sharma', 'Prof. Rakesh', 'Sharma', 'BSC'),
            ('dr.gupta_msc', 'Dr. Neha', 'Gupta', 'MSC'),
        ]
        
        self.lecturers = []
        for username, first, last, course_code in lecturers_data:
            lecturer = User.objects.create_user(
                username=username,
                password='lecturer123',
                first_name=first.replace('Dr. ', '').replace('Prof. ', ''),
                last_name=last,
                email=f'{username}@college.edu',
                user_type='lecturer',
                phone_number=f'98{random.randint(10000000, 99999999)}',
                assigned_course=self.courses[course_code]
            )
            self.lecturers.append(lecturer)
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(self.lecturers)} lecturers'))

    def create_sections(self):
        """Create sections for each course"""
        self.stdout.write('\n📌 Creating Sections...')
        
        self.sections = {}
        for code, course in self.courses.items():
            years = range(1, course.duration_years + 1)
            for year in years:
                for sec_name in ['A', 'B']:
                    section = Section.objects.create(
                        name=sec_name,
                        course=course,
                        semester=year
                    )
                    key = f"{code}_{year}_{sec_name}"
                    self.sections[key] = section
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(self.sections)} sections'))

    def create_subjects(self):
        """Create subjects for each course"""
        self.stdout.write('\n📌 Creating Subjects...')
        
        subjects_map = {
            'BCA': {
                1: [('BCA101', 'Programming in C'), ('BCA102', 'Digital Electronics'), 
                    ('BCA103', 'Mathematics-I'), ('BCA104', 'Communication Skills')],
                2: [('BCA201', 'Data Structures'), ('BCA202', 'OOP with C++'), 
                    ('BCA203', 'Computer Architecture'), ('BCA204', 'DBMS')],
                3: [('BCA301', 'Web Technologies'), ('BCA302', 'Software Engineering'), 
                    ('BCA303', 'Python Programming'), ('BCA304', 'Computer Networks')],
            },
            'BBA': {
                1: [('BBA101', 'Principles of Management'), ('BBA102', 'Business Economics'), 
                    ('BBA103', 'Financial Accounting'), ('BBA104', 'Business Communication')],
                2: [('BBA201', 'Organizational Behavior'), ('BBA202', 'Marketing Management'), 
                    ('BBA203', 'HR Management'), ('BBA204', 'Business Law')],
                3: [('BBA301', 'Strategic Management'), ('BBA302', 'International Business'), 
                    ('BBA303', 'Entrepreneurship'), ('BBA304', 'Project Management')],
            },
            'BCOM': {
                1: [('BCOM101', 'Financial Accounting'), ('BCOM102', 'Business Law'), 
                    ('BCOM103', 'Micro Economics'), ('BCOM104', 'Business Math')],
                2: [('BCOM201', 'Cost Accounting'), ('BCOM202', 'Corporate Law'), 
                    ('BCOM203', 'Macro Economics'), ('BCOM204', 'Statistics')],
                3: [('BCOM301', 'Income Tax'), ('BCOM302', 'Auditing'), 
                    ('BCOM303', 'Banking'), ('BCOM304', 'E-Commerce')],
            },
            'BA': {
                1: [('BA101', 'English Literature'), ('BA102', 'Indian History'), 
                    ('BA103', 'Political Science'), ('BA104', 'Sociology')],
                2: [('BA201', 'Psychology'), ('BA202', 'Economics'), 
                    ('BA203', 'Philosophy'), ('BA204', 'Journalism')],
                3: [('BA301', 'Public Administration'), ('BA302', 'Geography'), 
                    ('BA303', 'Fine Arts'), ('BA304', 'Cultural Studies')],
            },
            'BSC': {
                1: [('BSC101', 'Physics'), ('BSC102', 'Chemistry'), 
                    ('BSC103', 'Mathematics'), ('BSC104', 'Biology')],
                2: [('BSC201', 'Advanced Physics'), ('BSC202', 'Organic Chemistry'), 
                    ('BSC203', 'Calculus'), ('BSC204', 'Genetics')],
                3: [('BSC301', 'Quantum Mechanics'), ('BSC302', 'Biochemistry'), 
                    ('BSC303', 'Statistics'), ('BSC304', 'Research Methods')],
            },
            'MCA': {
                1: [('MCA101', 'Advanced Java'), ('MCA102', 'Advanced DBMS'), 
                    ('MCA103', 'Discrete Math'), ('MCA104', 'Software Engineering')],
                2: [('MCA201', 'Web Frameworks'), ('MCA202', 'Data Science'), 
                    ('MCA203', 'Cloud Computing'), ('MCA204', 'AI & ML')],
            },
            'MBA': {
                1: [('MBA101', 'Management Concepts'), ('MBA102', 'Organizational Behavior'), 
                    ('MBA103', 'Managerial Economics'), ('MBA104', 'Accounting')],
                2: [('MBA201', 'Marketing Management'), ('MBA202', 'Financial Management'), 
                    ('MBA203', 'HR Analytics'), ('MBA204', 'Business Strategy')],
            },
            'MCOM': {
                1: [('MCOM101', 'Advanced Accounting'), ('MCOM102', 'Business Environment'), 
                    ('MCOM103', 'Statistics'), ('MCOM104', 'Marketing')],
                2: [('MCOM201', 'Corporate Finance'), ('MCOM202', 'Taxation'), 
                    ('MCOM203', 'Research Methods'), ('MCOM204', 'International Trade')],
            },
            'MA': {
                1: [('MA101', 'Advanced Literature'), ('MA102', 'Research Methods'), 
                    ('MA103', 'Critical Theory'), ('MA104', 'Cultural Studies')],
                2: [('MA201', 'Postcolonial Studies'), ('MA202', 'Linguistics'), 
                    ('MA203', 'Creative Writing'), ('MA204', 'Dissertation')],
            },
            'MSC': {
                1: [('MSC101', 'Advanced Physics'), ('MSC102', 'Research Methodology'), 
                    ('MSC103', 'Data Analysis'), ('MSC104', 'Lab Work')],
                2: [('MSC201', 'Thesis Work'), ('MSC202', 'Specialization'), 
                    ('MSC203', 'Seminar'), ('MSC204', 'Project')],
            },
        }
        
        self.subjects = {}
        for course_code, years_data in subjects_map.items():
            if course_code in self.courses:
                course = self.courses[course_code]
                for year, subjects_list in years_data.items():
                    for code, name in subjects_list:
                        subject = Subject.objects.create(
                            code=code,
                            name=name,
                            course=course,
                            semester=year
                        )
                        key = f"{code}_{year}"
                        self.subjects[key] = subject
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(self.subjects)} subjects'))

    def create_students(self):
        """Create students for all courses"""
        self.stdout.write('\n📌 Creating Students...')
        
        students_list = [
            # BCA Students (8 students)
            ('rahul.kumar', 'Rahul Kumar', 'BCA2024001', 'BCA', 1, 'A'),
            ('priya.singh', 'Priya Singh', 'BCA2024002', 'BCA', 1, 'A'),
            ('amit.patel', 'Amit Patel', 'BCA2024003', 'BCA', 1, 'B'),
            ('neha.gupta', 'Neha Gupta', 'BCA2024004', 'BCA', 1, 'B'),
            ('rohan.joshi', 'Rohan Joshi', 'BCA2023005', 'BCA', 2, 'A'),
            ('sneha.verma', 'Sneha Verma', 'BCA2023006', 'BCA', 2, 'A'),
            ('vikas.yadav', 'Vikas Yadav', 'BCA2022007', 'BCA', 3, 'A'),
            ('meera.desai', 'Meera Desai', 'BCA2022008', 'BCA', 3, 'B'),
            
            # BBA Students (6 students)
            ('arjun.malhotra', 'Arjun Malhotra', 'BBA2024001', 'BBA', 1, 'A'),
            ('divya.shah', 'Divya Shah', 'BBA2024002', 'BBA', 1, 'B'),
            ('karan.kapoor', 'Karan Kapoor', 'BBA2023003', 'BBA', 2, 'A'),
            ('ananya.rao', 'Ananya Rao', 'BBA2023004', 'BBA', 2, 'B'),
            ('deepak.thakur', 'Deepak Thakur', 'BBA2022005', 'BBA', 3, 'A'),
            ('ritu.saxena', 'Ritu Saxena', 'BBA2022006', 'BBA', 3, 'B'),
            
            # BCOM Students (4 students)
            ('rajesh.pandey', 'Rajesh Pandey', 'BCOM2024001', 'BCOM', 1, 'A'),
            ('sarita.devi', 'Sarita Devi', 'BCOM2024002', 'BCOM', 1, 'B'),
            ('manoj.tiwari', 'Manoj Tiwari', 'BCOM2023003', 'BCOM', 2, 'A'),
            ('sunita.verma', 'Sunita Verma', 'BCOM2022004', 'BCOM', 3, 'A'),
            
            # BA Students (4 students)
            ('vikram.roy', 'Vikram Roy', 'BA2024001', 'BA', 1, 'A'),
            ('anita.kumari', 'Anita Kumari', 'BA2023002', 'BA', 2, 'A'),
            ('sandeep.singh', 'Sandeep Singh', 'BA2023003', 'BA', 2, 'B'),
            ('kavita.rao', 'Kavita Rao', 'BA2022004', 'BA', 3, 'A'),
            
            # BSC Students (4 students)
            ('gaurav.sharma', 'Gaurav Sharma', 'BSC2024001', 'BSC', 1, 'A'),
            ('pooja.agarwal', 'Pooja Agarwal', 'BSC2024002', 'BSC', 1, 'B'),
            ('nitin.chopra', 'Nitin Chopra', 'BSC2023003', 'BSC', 2, 'A'),
            ('rekha.singh', 'Rekha Singh', 'BSC2022004', 'BSC', 3, 'B'),
            
            # MCA Students (4 students)
            ('suresh.mishra', 'Suresh Mishra', 'MCA2024001', 'MCA', 1, 'A'),
            ('kavita.iyer', 'Kavita Iyer', 'MCA2024002', 'MCA', 1, 'B'),
            ('manish.rawat', 'Manish Rawat', 'MCA2023003', 'MCA', 2, 'A'),
            ('sunita.reddy', 'Sunita Reddy', 'MCA2023004', 'MCA', 2, 'B'),
            
            # MBA Students (4 students)
            ('gaurav.mehta', 'Gaurav Mehta', 'MBA2024001', 'MBA', 1, 'A'),
            ('pooja.mba', 'Pooja Agarwal', 'MBA2024002', 'MBA', 1, 'B'),
            ('amit.kumar', 'Amit Kumar', 'MBA2023003', 'MBA', 2, 'A'),
            ('neha.mba', 'Neha Singh', 'MBA2023004', 'MBA', 2, 'B'),
            
            # MCOM Students (2 students)
            ('rajesh.mcom', 'Rajesh Kumar', 'MCOM2024001', 'MCOM', 1, 'A'),
            ('priya.mcom', 'Priya Sharma', 'MCOM2023002', 'MCOM', 2, 'A'),
            
            # MA Students (2 students)
            ('deepak.ma', 'Deepak Verma', 'MA2024001', 'MA', 1, 'A'),
            ('sunita.ma', 'Sunita Devi', 'MA2023002', 'MA', 2, 'B'),
            
            # MSC Students (2 students)
            ('rahul.msc', 'Rahul Gupta', 'MSC2024001', 'MSC', 1, 'A'),
            ('neha.msc', 'Neha Patel', 'MSC2023002', 'MSC', 2, 'A'),
        ]
        
        self.student_profiles = {}
        for username, full_name, roll, course_code, year, sec in students_list:
            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                password='student123',
                first_name=first_name,
                last_name=last_name,
                email=f'{username}@college.edu',
                user_type='student'
            )
            
            profile = StudentProfile.objects.create(
                user=user,
                roll_no=roll,
                department=self.courses[course_code].department,
                registration_complete=False,
                face_encoding=json.dumps(np.random.rand(128).tolist())
            )
            
            self.student_profiles[roll] = {
                'profile': profile,
                'course': course_code,
                'year': year,
                'section': sec
            }
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(self.student_profiles)} students'))

    def create_enrollments(self):
        """Create student enrollments"""
        self.stdout.write('\n📌 Creating Enrollments...')
        
        for roll, data in self.student_profiles.items():
            profile = data['profile']
            course = self.courses[data['course']]
            year = data['year']
            section_key = f"{data['course']}_{year}_{data['section']}"
            section = self.sections.get(section_key)
            
            if section:
                subjects = Subject.objects.filter(course=course, semester=year)
                enrollment = StudentEnrollment.objects.create(
                    student=profile,
                    course=course,
                    semester=year,
                    section=section
                )
                enrollment.subjects.set(subjects)
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created enrollments for all students'))

    def create_non_teaching_staff(self):
        """Create some non‑teaching staff (workers, admin, etc.)"""
        self.stdout.write('\n📌 Creating Non‑Teaching Staff...')
        
        staff_data = [
            ('ramesh_peon', 'Ramesh', 'Kumar', 'Peon'),
            ('suresh_cleaner', 'Suresh', 'Singh', 'Cleaner'),
            ('anjali_admin', 'Anjali', 'Verma', 'Admin Assistant'),
            ('mohan_guard', 'Mohan', 'Rao', 'Security Guard'),
        ]
        
        for username, first, last, role in staff_data:
            user = User.objects.create_user(
                username=username,
                password='staff123',
                first_name=first,
                last_name=last,
                email=f'{username}@college.edu',
                user_type='staff',
                phone_number=f'98{random.randint(10000000, 99999999)}'
            )
            self.stdout.write(f'  ✅ {role}: {first} {last}')

    def create_demo_attendance(self):
        """Create demo attendance sessions and records"""
        self.stdout.write('\n📌 Creating Demo Attendance Data...')
        
        locations = [
            (28.6139, 77.2090),  # Delhi
            (19.0760, 72.8777),  # Mumbai
            (13.0827, 80.2707),  # Chennai
        ]
        
        session_count = 0
        record_count = 0
        
        # Create sessions only for first 5 courses to keep data manageable
        for course_code in ['BCA', 'BBA', 'MCA', 'MBA', 'BCOM']:
            course = self.courses[course_code]
            
            lecturer = User.objects.filter(
                user_type='lecturer',
                assigned_course=course
            ).first()
            
            if not lecturer:
                continue
            
            for year in [1]:
                for sec_name in ['A', 'B']:
                    section_key = f"{course_code}_{year}_{sec_name}"
                    section = self.sections.get(section_key)
                    
                    if not section:
                        continue
                    
                    subjects = Subject.objects.filter(course=course, semester=year)
                    
                    for subject in subjects[:2]:
                        location = random.choice(locations)
                        
                        num_sessions = random.randint(3, 5)
                        for i in range(num_sessions):
                            days_ago = random.randint(1, 30)
                            session = AttendanceSession.objects.create(
                                lecturer=lecturer,
                                course=course,
                                semester=year,
                                section=section,
                                subject=subject,
                                latitude=location[0] + random.uniform(-0.001, 0.001),
                                longitude=location[1] + random.uniform(-0.001, 0.001),
                                radius_feet=random.choice([20, 30, 40]),
                                is_active=False,
                                created_at=timezone.now() - timedelta(days=days_ago),
                                ended_at=timezone.now() - timedelta(days=days_ago, hours=1)
                            )
                            session_count += 1
                            
                            enrollments = StudentEnrollment.objects.filter(
                                course=course,
                                semester=year,
                                section=section
                            )
                            
                            for enrollment in enrollments:
                                if random.random() < 0.8:
                                    AttendanceRecord.objects.create(
                                        session=session,
                                        student=enrollment.student,
                                        student_latitude=location[0] + random.uniform(-0.0001, 0.0001),
                                        student_longitude=location[1] + random.uniform(-0.0001, 0.0001),
                                        location_verified=True,
                                        face_verified=random.choice([True, True, True, False]),
                                        status='Present',
                                        timestamp=session.created_at + timedelta(minutes=random.randint(1, 30))
                                    )
                                    record_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {session_count} sessions with {record_count} records'))

    def print_summary(self):
        """Print complete summary"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ DEMO DATA CREATED SUCCESSFULLY!'))
        self.stdout.write('='*70)
        
        self.stdout.write('\n📊 DATA SUMMARY:')
        self.stdout.write(f'  👑 Principal: 1')
        self.stdout.write(f'  👨‍💼 HODs (Course-based): {User.objects.filter(user_type="hod").count()}')
        self.stdout.write(f'  👨‍🏫 Lecturers: {User.objects.filter(user_type="lecturer").count()}')
        self.stdout.write(f'  👨‍🎓 Students: {User.objects.filter(user_type="student").count()}')
        self.stdout.write(f'  📚 Courses: {Course.objects.count()} ({Course.objects.filter(course_type="UG").count()} UG, {Course.objects.filter(course_type="PG").count()} PG)')
        self.stdout.write(f'  📖 Subjects: {Subject.objects.count()}')
        self.stdout.write(f'  🏫 Sections: {Section.objects.count()}')
        self.stdout.write(f'  📝 Enrollments: {StudentEnrollment.objects.count()}')
        self.stdout.write(f'  📊 Sessions: {AttendanceSession.objects.count()}')
        self.stdout.write(f'  ✅ Records: {AttendanceRecord.objects.count()}')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('🔑 LOGIN CREDENTIALS'))
        self.stdout.write('='*70)
        
        self.stdout.write('\n👑 PRINCIPAL:')
        self.stdout.write('  Username: principal')
        self.stdout.write('  Password: principal123')
        self.stdout.write('  Access: All courses and students')
        
        self.stdout.write('\n👨‍💼 HODs (Password: hod123):')
        self.stdout.write('  HODs are assigned to specific courses:')
        hods = User.objects.filter(user_type='hod').select_related('assigned_course')
        for hod in hods:
            course_name = hod.assigned_course.name if hod.assigned_course else 'No course'
            course_code = hod.assigned_course.code if hod.assigned_course else 'N/A'
            self.stdout.write(f'  • {hod.username} - {hod.get_full_name()} → {course_code} ({course_name})')
        
        self.stdout.write('\n👨‍🏫 LECTURERS (Password: lecturer123):')
        lecturers = User.objects.filter(user_type='lecturer').select_related('assigned_course')
        for lec in lecturers[:5]:
            course_code = lec.assigned_course.code if lec.assigned_course else 'N/A'
            self.stdout.write(f'  • {lec.username} → {course_code}')
        self.stdout.write(f'  ... Total {lecturers.count()} lecturers')
        
        self.stdout.write('\n👨‍🎓 STUDENTS (Password: student123):')
        self.stdout.write('  Sample students:')
        self.stdout.write('  BCA: rahul.kumar, priya.singh, amit.patel, neha.gupta')
        self.stdout.write('  BBA: arjun.malhotra, divya.shah, karan.kapoor')
        self.stdout.write('  MCA: suresh.mishra, kavita.iyer')
        self.stdout.write('  MBA: gaurav.mehta, pooja.mba')
        self.stdout.write(f'  ... Total {User.objects.filter(user_type="student").count()} students')
        
        self.stdout.write('\n📌 HOD DASHBOARD ACCESS:')
        self.stdout.write('  Each HOD sees ONLY their assigned course:')
        self.stdout.write('  • hod_bca → BCA dashboard (BCA students only)')
        self.stdout.write('  • hod_mca → MCA dashboard (MCA students only)')
        self.stdout.write('  • hod_bba → BBA dashboard (BBA students only)')
        self.stdout.write('  • etc.')
        
        self.stdout.write('\n⚠️  NOTES:')
        self.stdout.write('  • HODs are course-based, NOT department-based')
        self.stdout.write('  • Each HOD sees only their assigned course data')
        self.stdout.write('  • Students must register face before attendance')
        self.stdout.write('  • Run: daphne -p 8000 config.asgi:application')
        self.stdout.write('='*70 + '\n')