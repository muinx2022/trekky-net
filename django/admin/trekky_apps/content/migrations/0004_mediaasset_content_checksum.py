from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0003_mediaasset_cloudinary_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediaasset",
            name="content_checksum",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
