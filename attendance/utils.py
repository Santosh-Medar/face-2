import base64
from io import BytesIO

import cv2
import face_recognition
import numpy as np
from PIL import Image

from .models import HolidaySetting


def encode_face_from_image(image_file):
    """Encode face from uploaded image file"""
    try:
        img = face_recognition.load_image_file(image_file)
        face_encodings = face_recognition.face_encodings(img)

        if len(face_encodings) > 0:
            return face_encodings[0]
        else:
            print("No face found in the image")
            return None
    except Exception as e:
        print(f"Error encoding face: {e}")
        return None


def encode_face_from_frame(frame):
    """Encode face from video frame (numpy array BGR)"""
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) == 0:
            return None, None

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings) > 0:
            return face_encodings[0], face_locations[0]
        return None, None
    except Exception as e:
        print(f"Error encoding face from frame: {e}")
        return None, None


def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
    """Compare two face encodings"""
    try:
        if known_encoding is None or unknown_encoding is None:
            return False

        results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)
        return results[0]
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return False


def decode_base64_frame(frame_data):
    """Decode base64 frame data to OpenCV image"""
    try:
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]

        img_bytes = base64.b64decode(frame_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        return frame
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None


def is_holiday(date):
    try:
        holiday = HolidaySetting.objects.get(date=date)
        return holiday.is_holiday
    except HolidaySetting.DoesNotExist:
        return False

# attendance/utils.py

from django.db import models
from accounts.models import Subject

def get_mandatory_subjects(course, semester, section):
    """Return core subjects (excluding languages) for the given course, semester and section."""
    subjects = Subject.objects.filter(course=course, semester=semester)

    # Exclude language subjects
    language_patterns = ['GEN', 'GHN', 'GKA', 'KAN', 'HIN']
    query = models.Q()
    for pattern in language_patterns:
        query |= models.Q(code__icontains=pattern)
    subjects = subjects.exclude(query)

    # For BSc, filter by section
    if course.code == 'BSc':
        section_name = section.name
        if section_name == 'CBZ':
            patterns = ['BOTN', 'CHEM', 'ZOOL']
        elif section_name == 'PCM':
            patterns = ['CHEM', 'MATH', 'PHYS']
        elif section_name == 'PMCS':
            patterns = ['PHYS', 'MATH', 'COMP']
        else:
            patterns = []
        if patterns:
            query = models.Q()
            for p in patterns:
                query |= models.Q(code__icontains=p)
            subjects = subjects.filter(query)
    return subjects


def get_language_subject(course, semester, lang_code):
    """Return the language subject (Kannada or Hindi) for a given course and semester."""
    if lang_code == 'KAN':
        subject = Subject.objects.filter(
            course=course,
            semester=semester
        ).filter(
            models.Q(code__icontains='KAN') |
            models.Q(code__icontains='GKA') |
            models.Q(name__icontains='Kannada')
        ).first()
    else:  # 'HIN'
        subject = Subject.objects.filter(
            course=course,
            semester=semester
        ).filter(
            models.Q(code__icontains='GHN') |
            models.Q(code__icontains='HIN') |
            models.Q(name__icontains='Hindi')
        ).first()

    if not subject:
        raise Subject.DoesNotExist(
            f"Language subject not found for {course.code} sem {semester} lang {lang_code}"
        )
    return subject


def get_english_subject(course, semester):
    """Return the Basic English subject for a given course and semester."""
    subject = Subject.objects.filter(
        course=course,
        semester=semester,
        code__icontains='GEN'
    ).first()
    if not subject:
        raise Subject.DoesNotExist(
            f"Basic English subject not found for {course.code} sem {semester}"
        )
    return subject