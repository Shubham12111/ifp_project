from django.core.management.base import BaseCommand
from django.utils import timezone
from. models import UpdateWindowConfiguration



class Command(BaseCommand):
    help = 'Renew the update window configuration yearly'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        current_year = now.year

        # Check if an active update window exists for the current year
        active_update_window = UpdateWindowConfiguration.objects.filter(
            is_active=True, start_date__year=current_year
        ).first()

        if not active_update_window:
            # If no active window exists, create a new one for the current year
            start_date = timezone.make_aware(timezone.datetime(current_year, 1, 1))
            end_date = timezone.make_aware(timezone.datetime(current_year, 12, 31))
            new_window = UpdateWindowConfiguration.objects.create(
                start_date=start_date, end_date=end_date, is_active=True
            )

            self.stdout.write(self.style.SUCCESS(f'Successfully created a new update window for {current_year}.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Active update window already exists for {current_year}.'))