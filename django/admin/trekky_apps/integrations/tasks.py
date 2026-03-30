from celery import shared_task

from .ai_automation import run_comment_automation, run_content_automation, run_due_ai_automation


@shared_task
def run_due_ai_automation_task():
    return run_due_ai_automation()


@shared_task
def run_content_automation_task():
    return run_content_automation()


@shared_task
def run_comment_automation_task():
    return run_comment_automation()
