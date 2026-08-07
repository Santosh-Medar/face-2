#!/usr/bin/env python
"""
Assign teaching designations in the specified order.
Run with: python assign_teaching_designations.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import User, StaffProfile

def main():
    # EXACT ORDER as requested
    TEACHING_DESIGNATIONS = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer/Instructor']

    staff_users = User.objects.filter(user_type='lecturer')

    if not staff_users.exists():
        print("❌ No teaching staff found.")
        return

    print(f"📌 Found {staff_users.count()} teaching staff.\n")
    created_count = 0
    updated_count = 0

    # Round‑robin assignment
    for i, user in enumerate(staff_users):
        profile, created = StaffProfile.objects.get_or_create(user=user)
        if created:
            created_count += 1
            print(f"🆕 Created StaffProfile for {user.get_full_name()}")
        else:
            print(f"📌 Existing StaffProfile for {user.get_full_name()}")

        designation = TEACHING_DESIGNATIONS[i % len(TEACHING_DESIGNATIONS)]
        profile.designation = designation
        profile.save()
        updated_count += 1
        print(f"✅ {user.get_full_name():20} → {designation}\n")

    # Optional: Custom mapping (uncomment if needed)
    # custom_map = {
    #     'dr.verma': 'Professor',
    #     'prof.gupta': 'Associate Professor',
    #     'dr.kumar_cs': 'Assistant Professor',
    #     # add more
    # }
    # for username, designation in custom_map.items():
    #     try:
    #         user = User.objects.get(username=username)
    #         profile, created = StaffProfile.objects.get_or_create(user=user)
    #         if created:
    #             created_count += 1
    #             print(f"🆕 Created StaffProfile for {user.get_full_name()}")
    #         profile.designation = designation
    #         profile.save()
    #         updated_count += 1
    #         print(f"✅ {user.get_full_name():20} → {designation}")
    #     except User.DoesNotExist:
    #         print(f"❌ User '{username}' not found.\n")

    print(f"\n🎯 Done! Created {created_count} new profiles, updated {updated_count} staff members.")

if __name__ == '__main__':
    main()