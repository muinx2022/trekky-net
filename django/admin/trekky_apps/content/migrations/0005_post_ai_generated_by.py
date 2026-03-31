from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0004_mediaasset_content_checksum"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="ai_generated_by",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
    ]
