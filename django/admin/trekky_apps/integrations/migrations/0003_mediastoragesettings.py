from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0002_remove_aiautomationsettings_api_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaStorageSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(choices=[("local", "Local"), ("cloudinary", "Cloudinary"), ("cloudflare_r2", "Cloudflare R2")], default="cloudinary", max_length=32)),
                ("cloudinary_cloud_name", models.CharField(blank=True, max_length=255)),
                ("cloudinary_api_key", models.CharField(blank=True, max_length=255)),
                ("cloudinary_api_secret", models.CharField(blank=True, max_length=255)),
                ("cloudinary_secure", models.BooleanField(default=True)),
                ("r2_account_id", models.CharField(blank=True, max_length=255)),
                ("r2_access_key_id", models.CharField(blank=True, max_length=255)),
                ("r2_secret_access_key", models.CharField(blank=True, max_length=255)),
                ("r2_bucket_name", models.CharField(blank=True, max_length=255)),
                ("r2_public_base_url", models.CharField(blank=True, max_length=255)),
                ("r2_endpoint_url", models.CharField(blank=True, max_length=255)),
                ("r2_custom_domain", models.CharField(blank=True, max_length=255)),
            ],
        ),
    ]
