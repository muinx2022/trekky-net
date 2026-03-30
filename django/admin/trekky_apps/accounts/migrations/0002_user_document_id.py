from django.db import migrations, models


def backfill_user_document_ids(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    from trekky_apps.common.models import generate_document_id

    for user in User.objects.filter(models.Q(document_id__isnull=True) | models.Q(document_id="")).iterator():
        for _ in range(10):
            candidate = generate_document_id()
            if not User.objects.filter(document_id=candidate).exists():
                user.document_id = candidate
                user.save(update_fields=["document_id"])
                break
        else:
            raise RuntimeError(f"Could not backfill document_id for user {user.pk}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="document_id",
            field=models.CharField(blank=True, db_index=True, max_length=24, null=True),
        ),
        migrations.RunPython(backfill_user_document_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="document_id",
            field=models.CharField(blank=True, db_index=True, max_length=24, unique=True),
        ),
    ]
