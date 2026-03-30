from django.core.management.base import BaseCommand

from trekky_apps.integrations.ai_automation import run_comment_automation


class Command(BaseCommand):
    help = "Run the AI comment cron immediately."

    def handle(self, *args, **options):
        self.stdout.write(str(run_comment_automation()))
