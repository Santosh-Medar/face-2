import json

import numpy as np
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone
from geopy.distance import geodesic

from accounts.models import StaffProfile, StudentEnrollment, StudentProfile
from .models import AttendanceRecord, AttendanceSession, StaffAttendance, SystemSetting
from .utils import compare_faces, decode_base64_frame, encode_face_from_frame

User = get_user_model()


class AttendanceSessionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time attendance processing"""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'attendance_session_{self.session_id}'
        self.student_profile = None
        self.student_encoding = None

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"🟢 WebSocket Connected to session {self.session_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"🔴 WebSocket Disconnected from session {self.session_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'init_student':
            student_id = data.get('student_id')
            await self.initialize_student(student_id)

        elif action == 'mark_attendance':
            await self.process_attendance(data)

        elif action == 'end_session':
            await self.end_session()

        elif action == 'get_session_status':
            await self.send_session_status()

    async def initialize_student(self, student_id):
        try:
            profile, encoding = await self.get_student_data(student_id)
            if profile and encoding is not None:
                self.student_profile = profile
                self.student_encoding = encoding
                await self.send(text_data=json.dumps({
                    'type': 'student_initialized',
                    'success': True,
                    'name': profile.user.get_full_name() or profile.user.username,
                    'roll_no': profile.roll_no
                }))
                print(f"✅ Student initialized: {profile.roll_no}")
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Student profile or face encoding not found'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error initializing student: {str(e)}'
            }))

    async def process_attendance(self, data):
        if not self.student_profile or self.student_encoding is None:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': 'Student not initialized. Please try again.'
            }))
            return

        frame_data = data.get('frame')
        student_lat = float(data.get('latitude', 0))
        student_lon = float(data.get('longitude', 0))

        session = await self.get_session()
        if not session or not session.is_active:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': 'Session is not active'
            }))
            return

        within_radius = self.check_geofence(
            session.latitude, session.longitude,
            student_lat, student_lon,
            session.radius_feet
        )

        if not within_radius:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': f'You are outside the attendance radius ({session.radius_feet} feet)'
            }))
            return

        already_marked = await self.check_already_marked(session)
        if already_marked:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': 'Attendance already marked for this session'
            }))
            return

        is_enrolled = await self.check_enrollment(session)
        if not is_enrolled:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': 'You are not enrolled in this class'
            }))
            return

        face_verified = await self.verify_face(frame_data)

        if face_verified:
            record = await self.create_attendance_record(
                session, student_lat, student_lon, True
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'attendance_update',
                    'data': {
                        'student_name': self.student_profile.user.get_full_name(),
                        'roll_no': self.student_profile.roll_no,
                        'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'Present'
                    }
                }
            )

            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': True,
                'message': 'Attendance marked successfully!',
                'face_verified': True,
                'location_verified': True
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'attendance_result',
                'success': False,
                'message': 'Face verification failed. Please try again.',
                'face_verified': False
            }))

    async def verify_face(self, frame_data):
        try:
            frame = await sync_to_async(decode_base64_frame)(frame_data)
            if frame is None:
                return False

            face_encoding, face_location = await sync_to_async(encode_face_from_frame)(frame)
            if face_encoding is None:
                print("No face detected in frame")
                return False

            match = await sync_to_async(compare_faces)(self.student_encoding, face_encoding)
            return match

        except Exception as e:
            print(f"Error in face verification: {e}")
            return False

    async def end_session(self):
        session = await self.get_session()
        if session:
            await database_sync_to_async(session.end_session)()
            await database_sync_to_async(session.mark_absent_for_missing_students)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'session_ended',
                    'message': 'Attendance session has been ended by the lecturer'
                }
            )

    async def attendance_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'data': event['data']
        }))

    async def session_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'session_ended',
            'message': event['message']
        }))

    async def send_session_status(self):
        session = await self.get_session()
        if session:
            records_count = await self.get_records_count(session)
            enrolled_count = await self.get_enrolled_count(session)

            await self.send(text_data=json.dumps({
                'type': 'session_status',
                'is_active': session.is_active,
                'subject': session.subject.name,
                'section': session.section.name,
                'records_count': records_count,
                'enrolled_count': enrolled_count
            }))

    @staticmethod
    def check_geofence(session_lat, session_lon, student_lat, student_lon, radius_feet):
        session_location = (session_lat, session_lon)
        student_location = (student_lat, student_lon)
        distance = geodesic(session_location, student_location).feet
        return distance <= radius_feet

    @database_sync_to_async
    def get_student_data(self, student_id):
        try:
            profile = StudentProfile.objects.select_related('user').get(user_id=student_id)
            encoding = profile.get_face_encoding()
            return profile, encoding
        except StudentProfile.DoesNotExist:
            return None, None

    @database_sync_to_async
    def get_session(self):
        try:
            return AttendanceSession.objects.select_related(
                'course', 'section', 'subject'
            ).get(id=self.session_id)
        except AttendanceSession.DoesNotExist:
            return None

    @database_sync_to_async
    def check_already_marked(self, session):
        return AttendanceRecord.objects.filter(
            session=session,
            student=self.student_profile
        ).exists()

    @database_sync_to_async
    def check_enrollment(self, session):
        qs = StudentEnrollment.objects.filter(
            student=self.student_profile,
            course=session.course,
            semester=session.semester,
            subjects=session.subject
        )
        if session.section:  # if section is not None, filter by it
            qs = qs.filter(section=session.section)
        return qs.exists()

    @database_sync_to_async
    def create_attendance_record(self, session, lat, lon, face_verified):
        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            student=self.student_profile,
            defaults={
                'student_latitude': lat,
                'student_longitude': lon,
                'location_verified': True,
                'face_verified': face_verified,
                'status': 'Present'
            }
        )
        return record

    @database_sync_to_async
    def get_records_count(self, session):
        return AttendanceRecord.objects.filter(session=session).count()

    @database_sync_to_async
    def get_enrolled_count(self, session):
        return StudentEnrollment.objects.filter(
            course=session.course,
            semester=session.semester,
            section=session.section,
            subjects=session.subject
        ).count()


class LecturerAttendanceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for lecturer self-attendance"""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated or self.user.user_type != 'lecturer':
            await self.close()
            return
        await self.accept()
        self.fixed_location = await self.get_location_settings()
        self.stored_encoding = await self.get_stored_encoding()

    async def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def get_location_settings(self):
        try:
            setting = SystemSetting.objects.get(key='staff_attendance_location')
            import json
            return json.loads(setting.value)
        except SystemSetting.DoesNotExist:
            return {'lat': 15.2740581172022, 'lon': 76.37892989202457, 'radius': 50}

    @database_sync_to_async
    def get_stored_encoding(self):
        try:
            profile = StaffProfile.objects.get(user=self.user)
            return profile.get_face_encoding()
        except StaffProfile.DoesNotExist:
            return None

    @database_sync_to_async
    def check_already_marked(self):
        today = timezone.now().date()
        return StaffAttendance.objects.filter(user=self.user, date=today).exists()

    @database_sync_to_async
    def mark_attendance(self):
        today = timezone.now().date()
        attendance, created = StaffAttendance.objects.get_or_create(
            user=self.user,
            date=today,
            defaults={
                'status': 'present',
                'face_verified': True,
                'location_verified': True
            }
        )
        if not created:
            attendance.face_verified = True
            attendance.location_verified = True
            attendance.save()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'check_location':
            lat = data.get('latitude')
            lon = data.get('longitude')
            if lat is None or lon is None:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': False,
                    'message': 'No location data'
                }))
                return
            distance = geodesic(
                (self.fixed_location['lat'], self.fixed_location['lon']),
                (lat, lon)
            ).meters
            if distance <= self.fixed_location['radius']:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': True,
                    'distance': round(distance, 2)
                }))
            else:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': False,
                    'distance': round(distance, 2),
                    'message': f'You are {distance:.2f}m away, must be within {self.fixed_location["radius"]}m'
                }))

        elif action == 'mark_attendance':
            already_marked = await self.check_already_marked()
            if already_marked:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Attendance already marked today'
                }))
                return

            frame_data = data.get('frame')
            if not frame_data:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'No frame data'
                }))
                return

            frame = decode_base64_frame(frame_data)
            if frame is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Invalid frame'
                }))
                return

            face_encoding, _ = encode_face_from_frame(frame)
            if face_encoding is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'No face detected in the image'
                }))
                return

            if self.stored_encoding is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Face not registered. Please contact admin.'
                }))
                return

            match = compare_faces(self.stored_encoding, face_encoding)
            if match:
                await self.mark_attendance()
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': True,
                    'message': 'Attendance marked successfully!'
                }))
            else:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Face verification failed. Please try again.'
                }))


class StaffAttendanceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for non-teaching staff self-attendance"""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated or self.user.user_type != 'staff':
            await self.close()
            return
        await self.accept()
        self.fixed_location = await self.get_location_settings()
        self.stored_encoding = await self.get_stored_encoding()

    async def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def get_location_settings(self):
        try:
            setting = SystemSetting.objects.get(key='staff_attendance_location')
            import json
            return json.loads(setting.value)
        except SystemSetting.DoesNotExist:
            return {'lat': 15.2740581172022, 'lon': 76.37892989202457, 'radius': 50}

    @database_sync_to_async
    def get_stored_encoding(self):
        try:
            profile = StaffProfile.objects.get(user=self.user)
            return profile.get_face_encoding()
        except StaffProfile.DoesNotExist:
            return None

    @database_sync_to_async
    def check_already_marked(self):
        today = timezone.now().date()
        return StaffAttendance.objects.filter(user=self.user, date=today).exists()

    @database_sync_to_async
    def mark_attendance(self):
        today = timezone.now().date()
        attendance, created = StaffAttendance.objects.get_or_create(
            user=self.user,
            date=today,
            defaults={
                'status': 'present',
                'face_verified': True,
                'location_verified': True
            }
        )
        if not created:
            attendance.face_verified = True
            attendance.location_verified = True
            attendance.save()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'check_location':
            lat = data.get('latitude')
            lon = data.get('longitude')
            if lat is None or lon is None:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': False,
                    'message': 'No location data'
                }))
                return
            distance = geodesic(
                (self.fixed_location['lat'], self.fixed_location['lon']),
                (lat, lon)
            ).meters
            if distance <= self.fixed_location['radius']:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': True,
                    'distance': round(distance, 2)
                }))
            else:
                await self.send(json.dumps({
                    'type': 'location_status',
                    'verified': False,
                    'distance': round(distance, 2),
                    'message': f'You are {distance:.2f}m away, must be within {self.fixed_location["radius"]}m'
                }))

        elif action == 'mark_attendance':
            already_marked = await self.check_already_marked()
            if already_marked:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Attendance already marked today'
                }))
                return

            frame_data = data.get('frame')
            if not frame_data:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'No frame data'
                }))
                return

            frame = decode_base64_frame(frame_data)
            if frame is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Invalid frame'
                }))
                return

            face_encoding, _ = encode_face_from_frame(frame)
            if face_encoding is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'No face detected in the image'
                }))
                return

            if self.stored_encoding is None:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Face not registered. Please contact admin.'
                }))
                return

            match = compare_faces(self.stored_encoding, face_encoding)
            if match:
                await self.mark_attendance()
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': True,
                    'message': 'Attendance marked successfully!'
                }))
            else:
                await self.send(json.dumps({
                    'type': 'attendance_result',
                    'success': False,
                    'message': 'Face verification failed. Please try again.'
                }))