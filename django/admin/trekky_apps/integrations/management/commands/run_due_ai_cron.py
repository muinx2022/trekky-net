from django.core.management.base import BaseCommand

from trekky_apps.integrations.ai_automation import run_due_ai_automation


class Command(BaseCommand):
    help = "Run all due AI automation jobs based on current cron settings."

    def handle(self, *args, **options):
        self.stdout.write(str(run_due_ai_automation()))
