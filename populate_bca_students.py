#!/usr/bin/env python
"""
Standalone script to:
1) Create PCM and PMCS sections for BSc semesters 1,3,5 (and optionally others)
2) Move existing students from PCM/PMCS to either PCM or PMCS based on roll number.
Usage: python manage.py shell < migrate_bsc_sections.py
Or: python manage.py shell -c "exec(open('migrate_bsc_sections.py').read())"
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # adjust to your actual settings module
django.setup()

from django.db import transaction
from django.db.models import Q
from accounts.models import Course, Section, StudentEnrollment

# ===================== CONFIGURATION =====================
DRY_RUN = False   # Set to True to preview changes without saving
SEMESTERS = [1, 3, 5]   # Semesters to create sections for
# =========================================================

def create_sections():
    """Create PCM and PMCS sections for BSc courses in specified semesters."""
    print("Creating new sections...")
    courses = Course.objects.filter(code__icontains='BSc')
    if not courses.exists():
        print("No BSc courses found.")
        return

    for course in courses:
        for sem in SEMESTERS:
            # Create PCM section if it doesn't exist
            pcm, created = Section.objects.get_or_create(
                course=course,
                semester=sem,
                name='PCM',
                defaults={'name': 'PCM'}
            )
            if created:
                print(f"Created PCM section for {course.code} sem {sem}.")

            # Create PMCS section if it doesn't exist
            pmcs, created = Section.objects.get_or_create(
                course=course,
                semester=sem,
                name='PMCS',
                defaults={'name': 'PMCS'}
            )
            if created:
                print(f"Created PMCS section for {course.code} sem {sem}.")

def move_students():
    """Move enrollments from PCM/PMCS to appropriate section based on roll number."""
    print("\nMoving students...")
    # Get all enrollments where section name is 'PCM/PMCS'
    enrollments = StudentEnrollment.objects.filter(
        section__name='PCM/PMCS'
    ).select_related('student__user', 'course')

    if not enrollments.exists():
        print("No enrollments found in PCM/PMCS.")
        return

    print(f"Found {enrollments.count()} enrollments to process.")
    moved = {'PCM': 0, 'PMCS': 0, 'unknown': 0}

    for enrollment in enrollments:
        roll = enrollment.student.roll_no
        # Determine target section
        if 'PCM' in roll.upper() and 'PMCS' not in roll.upper():
            target_name = 'PCM'
        elif 'PMCS' in roll.upper():
            target_name = 'PMCS'
        else:
            moved['unknown'] += 1
            print(f"⚠️ Roll {roll}: cannot determine section. Skipping.")
            continue

        # Get the target section for the same course & semester
        try:
            target_section = Section.objects.get(
                course=enrollment.course,
                semester=enrollment.semester,
                name=target_name
            )
        except Section.DoesNotExist:
            print(f"❌ Target section {target_name} not found for {enrollment.course} sem {enrollment.semester}.")
            continue

        if not DRY_RUN:
            with transaction.atomic():
                enrollment.section = target_section
                enrollment.save()
            print(f"✅ Moved {enrollment.student.user.get_full_name()} ({roll}) → {target_name}.")
        else:
            print(f"🔍 DRY RUN: Would move {enrollment.student.user.get_full_name()} ({roll}) → {target_name}.")
        moved[target_name] += 1

    print(f"\n📊 Summary: Moved {moved['PCM']} to PCM, {moved['PMCS']} to PMCS, {moved['unknown']} unknown.")


if __name__ == '__main__':
    print("===== BSc Section Migration =====")
    print(f"DRY_RUN = {DRY_RUN}")
    create_sections()
    move_students()
    print("\n✅ Done.")