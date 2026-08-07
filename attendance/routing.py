# attendance/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/attendance/(?P<session_id>\d+)/$', consumers.AttendanceSessionConsumer.as_asgi()),
    re_path(r'ws/lecturer-attendance/$', consumers.LecturerAttendanceConsumer.as_asgi()),
    re_path(r'ws/staff-attendance/$', consumers.StaffAttendanceConsumer.as_asgi()),
]