from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Convert all usernames to lowercase (and optionally email)'

    def handle(self, *args, **options):
        users = User.objects.all()
        updated_count = 0
        conflict_count = 0

        for user in users:
            old_username = user.username
            new_username = old_username.lower()

            if old_username == new_username:
                continue  # already lowercase

            # Check if new_username already exists (case‑insensitive conflict)
            if User.objects.filter(username__iexact=new_username).exclude(pk=user.pk).exists():
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Skipping {old_username} -> {new_username} (conflict exists)"
                ))
                conflict_count += 1
                continue

            # Update username
            user.username = new_username

            # Update email if it matches the old username (common pattern)
            if user.email and user.email.lower() == old_username.lower() + '@example.com':
                user.email = new_username + '@example.com'

            user.save()
            updated_count += 1
            self.stdout.write(f"✅ Converted {old_username} -> {new_username}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Converted {updated_count} users. {conflict_count} conflicts (skipped)."
        ))