from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from trekky_apps.content.models import Comment, Page, Post
from trekky_apps.content.post_media_service import get_post_media_assets, sync_post_media
from trekky_apps.engagement.models import Report
from trekky_apps.integrations.models import AIAutomationSettings, EmailAuthSettings, GA4AnalyticsSettings, GoogleOAuthSettings, MediaStorageSettings
from trekky_apps.moderation.models import ModeratorCategoryAssignment
from trekky_apps.taxonomy.models import Category, Tag
from trekky_apps.common.models import trekky_slugify


User = get_user_model()


def build_category_tree_choices(include_blank=False):
    categories = list(Category.objects.order_by("sort_order", "name"))
    children_map = {}
    for category in categories:
        children_map.setdefault(category.parent_id, []).append(category)

    choices = [("", "Select categories")] if include_blank else []

    def walk(parent_id=None, depth=0):
        for category in children_map.get(parent_id, []):
            prefix = "\u2014 " * depth
            choices.append((str(category.pk), f"{prefix}{category.name}"))
            walk(category.pk, depth + 1)

    walk()
    return choices


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "form-control"
                widget.attrs.setdefault("rows", 5)
            else:
                widget.attrs["class"] = "form-control"


class AutoSlugFormMixin:
    slug_source_field = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "slug" in self.fields:
            self.fields["slug"].widget.attrs.update(
                {
                    "readonly": "readonly",
                    "data-autoslug-target": "true",
                }
            )
            self.fields["slug"].help_text = "Slug is generated automatically from the main title or name."
        if self.slug_source_field and self.slug_source_field in self.fields:
            self.fields[self.slug_source_field].widget.attrs["data-autoslug-source"] = "true"


class PostForm(AutoSlugFormMixin, BootstrapFormMixin, forms.ModelForm):
    slug_source_field = "title"
    ai_generated_by_display = forms.CharField(
        required=False,
        label="Post by AI",
        disabled=True,
    )
    image_asset_ids = forms.CharField(
        required=False,
        label="Media",
        widget=forms.HiddenInput(),
        help_text="Select gallery assets from the media library.",
    )
    tag_names = forms.CharField(
        required=False,
        label="Tags",
        help_text="Enter tags separated by commas. Existing tags are reused and new ones are created automatically.",
    )

    class Meta:
        model = Post
        fields = ("title", "slug", "excerpt", "content", "author", "categories", "is_published")
        widgets = {
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "content": forms.Textarea(
                attrs={
                    "rows": 12,
                    "data-tiptap": "true",
                    "data-tiptap-placeholder": "Write the post body here...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_media_assets = get_post_media_assets(self.instance) if self.instance.pk else set()
        self.fields["ai_generated_by_display"].initial = getattr(self.instance, "ai_generated_by", "") or "Manual post"
        self.order_fields(
            [
                "title",
                "slug",
                "excerpt",
                "content",
                "ai_generated_by_display",
                "author",
                "categories",
                "is_published",
                "tag_names",
                "image_asset_ids",
            ]
        )
        self.fields["author"].queryset = User.objects.order_by("email")
        self.fields["categories"].queryset = Category.objects.order_by("sort_order", "name")
        self.fields["categories"].choices = build_category_tree_choices()
        self.fields["categories"].widget.attrs.update(
            {
                "data-category-multiselect": "true",
                "data-placeholder": "Select categories",
                "class": "form-select d-none",
            }
        )
        self.fields["categories"].help_text = "Choose one or more categories for this post."
        self.fields["image_asset_ids"].widget.attrs.update(
            {
                "data-media-picker-input": "true",
            }
        )
        self.fields["tag_names"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "input your tag here, user comma to seperate tag",
                "list": "tag-suggestions",
                "data-tag-suggest-input": "true",
            }
        )
        self.tag_suggestions = list(Tag.objects.order_by("name").values_list("name", flat=True))
        self.initial_media_assets = [
            {
                "id": asset.media_asset_id or asset.id,
                "document_id": getattr(asset.media_asset, "document_id", ""),
                "url": asset.media_asset.cloudinary_secure_url if asset.media_asset and asset.media_asset.cloudinary_secure_url else asset.file.url,
                "thumbnail_url": asset.media_asset.cloudinary_secure_url if asset.media_asset and asset.media_asset.cloudinary_secure_url else asset.file.url,
                "original_filename": getattr(asset.media_asset, "original_filename", "") or asset.file.name,
            }
            for asset in self.instance.assets.select_related("media_asset").all()
        ] if self.instance.pk else []
        self.fields["image_asset_ids"].initial = ",".join(str(item["id"]) for item in self.initial_media_assets)
        if self.instance.pk:
            self.fields["tag_names"].initial = ", ".join(self.instance.tags.order_by("name").values_list("name", flat=True))

    @transaction.atomic
    def save(self, commit=True):
        post = super().save(commit=commit)
        tag_names = []
        for raw_name in str(self.cleaned_data.get("tag_names", "")).split(","):
            normalized = raw_name.strip()
            if normalized and normalized.lower() not in {item.lower() for item in tag_names}:
                tag_names.append(normalized)
        image_asset_ids = [
            int(value)
            for value in str(self.cleaned_data.get("image_asset_ids", "")).split(",")
            if str(value).strip().isdigit()
        ]

        tag_objects = []
        for name in tag_names:
            existing = Tag.objects.filter(slug=trekky_slugify(name)).first()
            if existing is None:
                existing = Tag.objects.filter(name__iexact=name).first()
            if existing is None:
                existing = Tag.objects.create(name=name)
            tag_objects.append(existing)
        post.tags.set(tag_objects)
        sync_post_media(post, self._previous_media_assets, image_asset_ids)
        return post


class CategoryForm(AutoSlugFormMixin, BootstrapFormMixin, forms.ModelForm):
    slug_source_field = "name"

    class Meta:
        model = Category
        fields = ("name", "slug", "description", "sort_order", "status", "parent")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Category.objects.order_by("sort_order", "name")


class TagForm(AutoSlugFormMixin, BootstrapFormMixin, forms.ModelForm):
    slug_source_field = "name"

    aliases_text = forms.CharField(
        required=False,
        label="Aliases",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One alias per line"}),
        help_text="Store aliases as one item per line.",
    )

    class Meta:
        model = Tag
        fields = ("name", "slug", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aliases_text"].initial = "\n".join(self.instance.aliases or [])

    def save(self, commit=True):
        self.instance.aliases = [line.strip() for line in self.cleaned_data["aliases_text"].splitlines() if line.strip()]
        return super().save(commit=commit)


class PageForm(AutoSlugFormMixin, BootstrapFormMixin, forms.ModelForm):
    slug_source_field = "title"

    class Meta:
        model = Page
        fields = ("title", "slug", "type", "content", "is_published")
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 12,
                    "data-tiptap": "true",
                    "data-tiptap-placeholder": "Write the page content here...",
                }
            )
        }


class CommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("target_type", "target_document_id", "parent", "author", "author_name", "author_email", "content", "status")
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Comment.objects.order_by("created_at")
        self.fields["author"].queryset = User.objects.order_by("email")


class ReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Report
        fields = ("target_type", "target_document_id", "reason", "status", "moderator_note")
        widgets = {"reason": forms.Textarea(attrs={"rows": 5}), "moderator_note": forms.Textarea(attrs={"rows": 5})}


class ModeratorAssignmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ModeratorCategoryAssignment
        fields = ("moderator", "category")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["moderator"].queryset = User.objects.filter(role="moderator").order_by("email")
        self.fields["category"].queryset = Category.objects.order_by("sort_order", "name")


class GA4SettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = GA4AnalyticsSettings
        fields = ("property_id", "measurement_id", "client_id", "client_secret", "refresh_token", "is_connected")
        widgets = {"refresh_token": forms.Textarea(attrs={"rows": 4})}


class MediaStorageSettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MediaStorageSettings
        fields = (
            "provider",
            "cloudinary_cloud_name",
            "cloudinary_api_key",
            "cloudinary_api_secret",
            "cloudinary_secure",
            "r2_account_id",
            "r2_access_key_id",
            "r2_secret_access_key",
            "r2_bucket_name",
            "r2_public_base_url",
            "r2_endpoint_url",
            "r2_custom_domain",
        )


class AISettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AIAutomationSettings
        fields = (
            "timezone",
            "content_enabled",
            "content_cron",
            "content_posts_per_run",
            "content_scenario_prompt",
            "content_last_scenario",
            "content_prompt",
            "content_image_provider",
            "content_image_count_min",
            "content_image_count_max",
            "content_preferred_media_mode",
            "comments_enabled",
            "comments_cron",
            "comments_per_run",
            "comments_allow_replies",
            "comment_prompt",
            "reply_prompt",
            "openai_enabled",
            "openai_api_key",
            "openai_models",
            "anthropic_enabled",
            "anthropic_api_key",
            "anthropic_models",
            "google_image_search_enabled",
            "google_image_search_api_key",
            "google_image_search_engine_id",
            "pexels_enabled",
            "pexels_api_key",
        )
        widgets = {
            "content_prompt": forms.Textarea(attrs={"rows": 5}),
            "comment_prompt": forms.Textarea(attrs={"rows": 5}),
            "reply_prompt": forms.Textarea(attrs={"rows": 5}),
            "content_scenario_prompt": forms.Textarea(attrs={"rows": 8}),
            "content_last_scenario": forms.TextInput(),
            "openai_models": forms.Textarea(attrs={"rows": 3}),
            "anthropic_models": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for json_field in ("openai_models", "anthropic_models"):
            initial = self.initial.get(json_field, getattr(self.instance, json_field, []))
            if isinstance(initial, list):
                self.fields[json_field].initial = "\n".join(str(item) for item in initial)

    def clean_openai_models(self):
        raw = self.cleaned_data["openai_models"]
        if isinstance(raw, list):
            return raw
        return [line.strip() for line in str(raw).splitlines() if line.strip()]

    def clean_anthropic_models(self):
        raw = self.cleaned_data["anthropic_models"]
        if isinstance(raw, list):
            return raw
        return [line.strip() for line in str(raw).splitlines() if line.strip()]


class GoogleOAuthSettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = GoogleOAuthSettings
        fields = ("client_id", "client_secret", "redirect_uri", "frontend_url")


class EmailAuthSettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailAuthSettings
        fields = (
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_use_tls",
            "smtp_use_ssl",
            "smtp_timeout",
            "from_email",
            "from_name",
            "reply_to",
            "frontend_base_url",
            "login_path",
            "password_reset_path",
            "registration_email_subject",
            "registration_email_body",
            "password_reset_email_subject",
            "password_reset_email_body",
        )
        widgets = {
            "smtp_password": forms.PasswordInput(render_value=True),
            "registration_email_body": forms.Textarea(attrs={"rows": 8}),
            "password_reset_email_body": forms.Textarea(attrs={"rows": 8}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("smtp_use_tls") and cleaned_data.get("smtp_use_ssl"):
            self.add_error("smtp_use_ssl", "Chỉ nên bật một trong hai chế độ TLS hoặc SSL.")
        return cleaned_data


class UserForm(BootstrapFormMixin, forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Leave blank to keep existing password. Required when creating a new user.",
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label="Confirm password",
    )

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "role", "bio", "is_active")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if not self.instance.pk and not password:
            self.add_error("password", "Password is required for new users.")
        if password and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
