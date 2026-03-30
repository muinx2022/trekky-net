from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0002_mediaasset_postasset_media_asset"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediaasset",
            name="cloudinary_asset_folder",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="cloudinary_format",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="cloudinary_public_id",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="cloudinary_resource_type",
            field=models.CharField(blank=True, default="image", max_length=32),
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="cloudinary_secure_url",
            field=models.URLField(blank=True),
        ),
    ]
