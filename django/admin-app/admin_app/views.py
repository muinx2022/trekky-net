from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
import json
import re

from .forms import AISettingsForm, CategoryForm, CommentForm, EmailAuthSettingsForm, GA4SettingsForm, GoogleOAuthSettingsForm, MediaStorageSettingsForm, ModeratorAssignmentForm, PageForm, PostForm, ReportForm, TagForm, UserForm
from trekky_apps.accounts.seed_users import DEFAULT_SEED_PASSWORD, build_seed_user_draft
from trekky_apps.content.models import Comment, CommentStatus, Page, Post
from trekky_apps.content.post_media_service import PostMediaSyncError, delete_post_with_media
from trekky_apps.engagement.models import Report, ReportStatus
from trekky_apps.integrations.ai_automation import run_comment_automation, run_content_automation
from trekky_apps.integrations.models import AIAutomationSettings, EmailAuthSettings, GA4AnalyticsSettings, GoogleOAuthSettings, MediaStorageSettings
from trekky_apps.moderation.models import ModerationAction, ModeratorCategoryAssignment
from trekky_apps.taxonomy.models import Category, CategoryStatus, Tag

User = get_user_model()
ALLOWED_ADMIN_APP_ROLES = {"admin", "editor"}


def resolve_report_target_state(target_type, target_document_id):
    if target_type == "post":
        post = Post.objects.filter(document_id=target_document_id).only("document_id", "is_published").first()
        if not post:
            return {"label": "Missing", "variant": "secondary", "exists": False}
        return {"label": "Published" if post.is_published else "Hidden", "variant": "success" if post.is_published else "warning", "exists": True}
    if target_type == "comment":
        comment = Comment.objects.filter(document_id=target_document_id).only("document_id", "status").first()
        if not comment:
            return {"label": "Missing", "variant": "secondary", "exists": False}
        status_label = comment.get_status_display()
        variant = "success" if comment.status == CommentStatus.PUBLISHED else "warning"
        return {"label": status_label, "variant": variant, "exists": True}
    return {"label": "Unknown", "variant": "secondary", "exists": False}


def resolve_reports_for_target(*, moderator, report, approved):
    sibling_qs = Report.objects.filter(
        target_type=report.target_type,
        target_document_id=report.target_document_id,
        status=ReportStatus.PENDING,
    )
    resolved_count = sibling_qs.count()
    next_status = ReportStatus.REVIEWED if approved else ReportStatus.DISMISSED
    target_missing = False

    with transaction.atomic():
        if resolved_count:
            sibling_qs.update(status=next_status)

        if approved:
            if report.target_type == "post":
                updated = Post.objects.filter(document_id=report.target_document_id, is_published=True).update(
                    is_published=False,
                    published_at=None,
                )
                target_missing = not Post.objects.filter(document_id=report.target_document_id).exists()
            elif report.target_type == "comment":
                updated = Comment.objects.filter(document_id=report.target_document_id).exclude(status=CommentStatus.HIDDEN).update(
                    status=CommentStatus.HIDDEN,
                    is_published=False,
                    published_at=None,
                )
                target_missing = not Comment.objects.filter(document_id=report.target_document_id).exists()
            else:
                updated = 0
                target_missing = True
        else:
            updated = 0
            if report.target_type == "post":
                target_missing = not Post.objects.filter(document_id=report.target_document_id).exists()
            elif report.target_type == "comment":
                target_missing = not Comment.objects.filter(document_id=report.target_document_id).exists()
            else:
                target_missing = True

        action_prefix = "approve" if approved else "reject"
        ModerationAction.objects.create(
            moderator=moderator,
            target_type=report.target_type,
            target_document_id=report.target_document_id,
            action=f"{action_prefix}_{report.target_type}_report",
            note=report.moderator_note,
        )

    return {
        "resolved_count": resolved_count,
        "updated_target": bool(updated),
        "target_missing": target_missing,
    }


def build_category_tree(categories):
    children_map = {}
    for category in categories:
        children_map.setdefault(category.parent_id, []).append(category)

    for siblings in children_map.values():
        siblings.sort(key=lambda item: (item.sort_order, item.name))

    def nest(parent_id=None):
        nodes = []
        for category in children_map.get(parent_id, []):
            nodes.append({"category": category, "children": nest(category.id)})
        return nodes

    return nest(None)


def build_category_filter_choices(categories):
    choices = []

    def flatten(nodes, depth=0):
        prefix = "" if depth == 0 else f'{"-- " * depth}'
        for node in nodes:
            category = node["category"]
            choices.append({"value": category.document_id, "label": f"{prefix}{category.name}"})
            flatten(node["children"], depth + 1)

    flatten(build_category_tree(categories))
    return choices


def build_comment_tree(comments):
    children_map = {}
    for comment in comments:
        children_map.setdefault(comment.parent_id, []).append(comment)

    def nest(parent_id=None):
        nodes = []
        for comment in children_map.get(parent_id, []):
            nodes.append({"comment": comment, "children": nest(comment.id)})
        return nodes

    return nest(None)


def is_ajax_request(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def build_toggle_response(*, is_on: bool, title: str, aria_label: str, message: str):
    return JsonResponse(
        {
            "ok": True,
            "is_on": is_on,
            "title": title,
            "aria_label": aria_label,
            "message": message,
        }
    )


def build_login_form(request, data=None):
    form = AuthenticationForm(request=request, data=data)
    form.fields["username"].widget.attrs.update({"class": "form-control form-control-lg login-input", "placeholder": "admin@trekky.local", "autocomplete": "username"})
    form.fields["password"].widget.attrs.update({"class": "form-control form-control-lg login-input", "placeholder": "Enter your password", "autocomplete": "current-password"})
    return form


class AdminAppAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "/admin-app/login/"

    def test_func(self):
        return bool(self.request.user.is_authenticated and getattr(self.request.user, "role", None) in ALLOWED_ADMIN_APP_ROLES)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Your account does not have access to the admin app.")
            return redirect("admin_app:login")
        return super().handle_no_permission()

    def get_navigation(self):
        return [
            {"items": [
                {"label": "Dashboard", "icon": "bi-speedometer2", "url": reverse("admin_app:dashboard"), "key": "dashboard"},
            ]},
            {"label": "Content", "items": [
                {"label": "Posts", "icon": "bi-file-earmark-text", "url": reverse("admin_app:post-list"), "key": "posts"},
                {"label": "Pages", "icon": "bi-window-stack", "url": reverse("admin_app:page-list"), "key": "pages"},
                {"label": "Media", "icon": "bi-images", "url": reverse("admin_app:media-library"), "key": "media"},
                {"label": "Categories", "icon": "bi-diagram-3", "url": reverse("admin_app:category-list"), "key": "categories"},
            ]},
            {"label": "Engagement", "items": [
                {"label": "Tags", "icon": "bi-tags", "url": reverse("admin_app:tag-list"), "key": "tags"},
                {"label": "Comments", "icon": "bi-chat-square-text", "url": reverse("admin_app:comment-list"), "key": "comments"},
                {"label": "Reports", "icon": "bi-flag", "url": reverse("admin_app:report-list"), "key": "reports"},
            ]},
            {"label": "Administration", "items": [
                {"label": "Users", "icon": "bi-person-badge", "url": reverse("admin_app:user-list"), "key": "users"},
                {"label": "Settings", "icon": "bi-sliders2", "url": reverse("admin_app:settings"), "key": "settings"},
            ]},
        ]

    def get_bottom_navigation(self):
        return [
            {"label": "Django Admin", "icon": "bi-shield-lock", "url": "/admin/", "key": "django-admin"},
            {"label": "Sign Out", "icon": "bi-box-arrow-right", "url": reverse("admin_app:logout"), "key": "sign-out", "danger": True},
        ]

    def get_context_data(self, **kwargs):
        context = getattr(super(), "get_context_data", lambda **k: {})(**kwargs)
        context["admin_navigation"] = self.get_navigation()
        context["admin_bottom_navigation"] = self.get_bottom_navigation()
        context["active_nav"] = getattr(self, "active_nav", "")
        return context


class AdminAppLoginView(View):
    template_name = "admin_app/login.html"

    def get(self, request):
        if request.user.is_authenticated and getattr(request.user, "role", None) in ALLOWED_ADMIN_APP_ROLES:
            return redirect("admin_app:dashboard")
        return render(request, self.template_name, {"form": build_login_form(request)})

    def post(self, request):
        form = build_login_form(request, data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        user = form.get_user()
        if getattr(user, "role", None) not in ALLOWED_ADMIN_APP_ROLES:
            messages.error(request, "Only admin and editor accounts can access the admin app.")
            logout(request)
            return render(request, self.template_name, {"form": build_login_form(request)}, status=403)

        login(request, user)
        messages.success(request, f"Welcome back, {user.username or user.email}.")
        return redirect(request.GET.get("next") or request.POST.get("next") or "/admin-app/")


class AdminAppLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been signed out from the admin app.")
        return redirect("admin_app:login")

    def post(self, request):
        logout(request)
        messages.success(request, "You have been signed out from the admin app.")
        return redirect("admin_app:login")


class AdminAppListView(AdminAppAccessMixin, ListView):
    template_name = "admin_app/entity_list.html"
    context_object_name = "items"
    paginate_by = 20
    page_title = ""
    page_subtitle = ""
    create_url_name = ""
    create_label = "Create"
    columns = []
    active_nav = ""
    search_fields = ()
    detail_url_name = ""
    delete_url_name = ""
    view_url_name = ""
    extra_actions = []
    filter_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query and self.search_fields:
            filters = Q()
            for field in self.search_fields:
                filters |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(filters)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        active_filter_values = []
        for field in self.filter_fields:
            field_name = field.get("name") if isinstance(field, dict) else None
            if field_name:
                active_filter_values.append(self.request.GET.get(field_name, "").strip())
        page_obj = context.get("page_obj")
        pagination_pages = []
        if page_obj:
            current = page_obj.number
            total = page_obj.paginator.num_pages
            start = max(1, current - 2)
            end = min(total, current + 2)
            pagination_pages = list(range(start, end + 1))
        reset_url = self.request.path
        if self.active_nav == "users":
            reset_url = f"{reset_url}?tab={getattr(self, 'get_user_tab', lambda: 'user')()}"
        context.update({"page_title": self.page_title, "page_subtitle": self.page_subtitle, "create_url": reverse(self.create_url_name) if self.create_url_name else "", "create_label": self.create_label, "columns": self.columns, "query": self.request.GET.get("q", ""), "detail_url_name": self.detail_url_name, "delete_url_name": self.delete_url_name, "extra_actions": self.extra_actions, "pagination_query": params.urlencode(), "pagination_pages": pagination_pages, "filter_fields": self.filter_fields, "reset_url": reset_url, "has_active_filters": bool(self.request.GET.get("q", "").strip() or any(active_filter_values))})
        context["view_url_name"] = self.view_url_name
        return context


class AdminAppFormView(AdminAppAccessMixin):
    template_name = "admin_app/entity_form.html"
    page_title = ""
    page_subtitle = ""
    success_message = ""
    active_nav = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["cancel_url"] = str(self.success_url) if getattr(self, "success_url", None) else ""
        return context


class AdminAppDeleteView(AdminAppAccessMixin, DeleteView):
    template_name = "admin_app/confirm_delete.html"
    page_title = ""
    page_subtitle = ""
    success_message = ""
    active_nav = ""

    def form_valid(self, form):
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["cancel_url"] = self.get_success_url()
        return context


class DashboardView(AdminAppAccessMixin, TemplateView):
    template_name = "admin_app/dashboard.html"
    active_nav = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary_cards"] = [
            {"label": "Posts", "value": Post.objects.count()},
            {"label": "Categories", "value": Category.objects.count()},
            {"label": "Tags", "value": Tag.objects.count()},
            {"label": "Comments", "value": Comment.objects.count()},
            {"label": "Pending Reports", "value": Report.objects.filter(status="pending").count()},
            {"label": "Moderator Assignments", "value": ModeratorCategoryAssignment.objects.count()},
        ]
        context["recent_posts"] = Post.objects.select_related("author").order_by("-updated_at")[:8]
        context["top_categories"] = Category.objects.annotate(post_count=Count("posts")).order_by("-post_count", "name")[:8]
        context["integration_state"] = {"ga4": GA4AnalyticsSettings.objects.order_by("-updated_at").first(), "ai": AIAutomationSettings.objects.order_by("-updated_at").first()}
        context["recent_reports"] = Report.objects.order_by("-created_at")[:6]
        return context


class PostListView(AdminAppListView):
    model = Post
    queryset = Post.objects.select_related("author").prefetch_related("categories").annotate(
        comment_count=Coalesce(
            Subquery(
                Comment.objects.filter(
                    target_type="post",
                    target_document_id=OuterRef("document_id"),
                )
                .values("target_document_id")
                .annotate(total=Count("id"))
                .values("total")[:1]
            ),
            Value(0),
            output_field=IntegerField(),
        )
    ).order_by("-created_at")
    page_title = "Posts"
    page_subtitle = "Manage editorial content and preserve public permalink identifiers."
    create_url_name = "admin_app:post-create"
    create_label = "New Post"
    columns = ["Title", "Category", "Cmt", "Published", "Updated", "Actions"]
    active_nav = "posts"
    search_fields = ("title", "slug", "document_id")
    detail_url_name = "admin_app:post-update"
    delete_url_name = "admin_app:post-delete"
    view_url_name = "admin_app:post-detail"

    def get_queryset(self):
        queryset = super().get_queryset()
        category_filter = self.request.GET.get("category", "").strip()
        status_filter = self.request.GET.get("status", "").strip()

        if category_filter:
            queryset = queryset.filter(categories__document_id=category_filter)

        if status_filter == "published":
            queryset = queryset.filter(is_published=True)
        elif status_filter == "draft":
            queryset = queryset.filter(is_published=False)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_category = self.request.GET.get("category", "").strip()
        selected_status = self.request.GET.get("status", "").strip()
        category_choices = build_category_filter_choices(
            Category.objects.select_related("parent").only("id", "document_id", "name", "sort_order", "parent_id")
        )
        filter_fields = [
            {
                "name": "category",
                "label": "Category",
                "value": selected_category,
                "choices": category_choices,
            },
            {
                "name": "status",
                "label": "Status",
                "value": selected_status,
                "choices": [
                    {"value": "published", "label": "Published"},
                    {"value": "draft", "label": "Draft"},
                ],
            },
        ]
        context["filter_fields"] = filter_fields
        context["has_active_filters"] = bool(context.get("query") or selected_category or selected_status)
        return context


class PostCreateView(AdminAppFormView, CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("admin_app:post-list")
    page_title = "Create Post"
    page_subtitle = "Create a new Trekky post."
    success_message = "Post created successfully."
    active_nav = "posts"


class PostUpdateView(AdminAppFormView, UpdateView):
    model = Post
    form_class = PostForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:post-list")
    page_title = "Edit Post"
    page_subtitle = "Update content, taxonomy, and publish state."
    success_message = "Post updated successfully."
    active_nav = "posts"


class PostDeleteView(AdminAppDeleteView):
    model = Post
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:post-list")
    page_title = "Delete Post"
    page_subtitle = "This removes the selected post."
    success_message = "Post deleted successfully."
    active_nav = "posts"

    def form_valid(self, form):
        try:
            delete_post_with_media(self.object)
        except PostMediaSyncError as exc:
            messages.error(self.request, f"Could not delete post media: {exc}")
            return self.render_to_response(self.get_context_data(form=form))
        if self.success_message:
            messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class PostDetailView(AdminAppAccessMixin, DetailView):
    model = Post
    template_name = "admin_app/post_detail.html"
    context_object_name = "post"
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    active_nav = "posts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        comments = list(
            Comment.objects.select_related("author", "parent")
            .filter(target_type="post", target_document_id=post.document_id)
            .order_by("created_at")
        )
        context["page_title"] = "Post View"
        context["page_subtitle"] = "Review post information and moderate the full comment tree."
        context["comment_tree"] = build_comment_tree(comments)
        context["comment_count"] = len(comments)
        return context


class PostCommentDeleteBranchView(AdminAppAccessMixin, View):
    def post(self, request, document_id, comment_document_id):
        post = get_object_or_404(Post, document_id=document_id)
        comment = get_object_or_404(
            Comment,
            document_id=comment_document_id,
            target_type="post",
            target_document_id=post.document_id,
        )
        deleted_author = comment.author_name or comment.author_email or comment.document_id
        comment.delete()
        messages.success(request, f"Comment branch from {deleted_author} was deleted.")
        return redirect("admin_app:post-detail", document_id=post.document_id)


class PageListView(AdminAppListView):
    model = Page
    queryset = Page.objects.order_by("title")
    page_title = "Pages"
    page_subtitle = "Manage home and footer CMS pages."
    create_url_name = "admin_app:page-create"
    create_label = "New Page"
    columns = ["Title", "Type", "Document ID", "Published", "Updated", "Actions"]
    active_nav = "pages"
    search_fields = ("title", "slug", "document_id")
    detail_url_name = "admin_app:page-update"
    delete_url_name = "admin_app:page-delete"


class PageCreateView(AdminAppFormView, CreateView):
    model = Page
    form_class = PageForm
    success_url = reverse_lazy("admin_app:page-list")
    page_title = "Create Page"
    page_subtitle = "Create reusable page content."
    success_message = "Page created successfully."
    active_nav = "pages"


class PageUpdateView(AdminAppFormView, UpdateView):
    model = Page
    form_class = PageForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:page-list")
    page_title = "Edit Page"
    page_subtitle = "Update page metadata and content."
    success_message = "Page updated successfully."
    active_nav = "pages"


class PageDeleteView(AdminAppDeleteView):
    model = Page
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:page-list")
    page_title = "Delete Page"
    page_subtitle = "This removes the selected page."
    success_message = "Page deleted successfully."
    active_nav = "pages"


class MediaLibraryView(AdminAppAccessMixin, TemplateView):
    template_name = "admin_app/media.html"
    active_nav = "media"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Media"
        context["page_subtitle"] = "Browse Cloudinary folders, manage assets, and reuse media across Trekky content."
        return context


class CategoryListView(AdminAppListView):
    template_name = "admin_app/category_list.html"
    paginate_by = None
    model = Category
    queryset = Category.objects.select_related("parent").prefetch_related("moderator_assignments__moderator").order_by("sort_order", "name")
    page_title = "Categories"
    page_subtitle = "Organize content and moderator assignment scope."
    create_url_name = "admin_app:category-create"
    create_label = "New Category"
    columns = ["Name", "Parent", "Document ID", "Sort", "Status", "Actions"]
    active_nav = "categories"
    search_fields = ("name", "slug", "document_id")
    detail_url_name = "admin_app:category-update"
    delete_url_name = "admin_app:category-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["moderator_options"] = User.objects.filter(role__in=["moderator", "user"], is_seeded=False).order_by("email")
        context["category_tree"] = build_category_tree(list(context["items"]))
        return context


class CategoryCreateView(AdminAppFormView, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("admin_app:category-list")
    page_title = "Create Category"
    page_subtitle = "Add a new taxonomy category."
    success_message = "Category created successfully."
    active_nav = "categories"


class CategoryUpdateView(AdminAppFormView, UpdateView):
    model = Category
    form_class = CategoryForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:category-list")
    page_title = "Edit Category"
    page_subtitle = "Update category hierarchy and metadata."
    success_message = "Category updated successfully."
    active_nav = "categories"


class CategoryDeleteView(AdminAppDeleteView):
    model = Category
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:category-list")
    page_title = "Delete Category"
    page_subtitle = "Delete the selected category."
    success_message = "Category deleted successfully."
    active_nav = "categories"


class CategoryAssignModeratorView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        category = get_object_or_404(Category, document_id=document_id)
        moderator_id = request.POST.get("moderator_id")
        moderator = get_object_or_404(User, pk=moderator_id, role__in=["moderator", "user"])
        assignment, created = ModeratorCategoryAssignment.objects.get_or_create(
            moderator=moderator,
            category=category,
        )
        if created:
            messages.success(request, f"{moderator.email} was assigned to {category.name}.")
        else:
            messages.info(request, f"{moderator.email} is already assigned to {category.name}.")
        return redirect("admin_app:category-list")


class CategoryUnassignModeratorView(AdminAppAccessMixin, View):
    def post(self, request, assignment_id):
        assignment = get_object_or_404(ModeratorCategoryAssignment, pk=assignment_id)
        assignment.delete()
        return JsonResponse({"ok": True})


class CategoryReorderView(AdminAppAccessMixin, View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid payload"}, status=400)

        tree = payload.get("tree")
        if not isinstance(tree, list):
            return JsonResponse({"error": "tree is required"}, status=400)

        categories = {item.document_id: item for item in Category.objects.all()}
        seen = set()
        updates = []

        def walk(nodes, parent=None):
            for index, node in enumerate(nodes):
                document_id = str(node.get("document_id") or "").strip()
                if not document_id or document_id not in categories:
                    raise ValueError("Category not found")
                if document_id in seen:
                    raise ValueError("Duplicate category in tree")
                seen.add(document_id)
                category = categories[document_id]
                if parent and parent.document_id == category.document_id:
                    raise ValueError("Invalid parent relationship")
                updates.append((category, parent, index))
                children = node.get("children", [])
                if children:
                    if not isinstance(children, list):
                        raise ValueError("children must be a list")
                    walk(children, category)

        try:
            walk(tree)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        if len(seen) != len(categories):
            return JsonResponse({"error": "The submitted tree is incomplete"}, status=400)

        for category, parent, index in updates:
            category.parent = parent
            category.sort_order = index
            category.save(update_fields=["parent", "sort_order", "updated_at"])

        return JsonResponse({"ok": True})


class TagListView(AdminAppListView):
    model = Tag
    queryset = Tag.objects.order_by("name")
    page_title = "Tags"
    page_subtitle = "Manage tags and alias metadata."
    create_url_name = "admin_app:tag-create"
    create_label = "New Tag"
    columns = ["Name", "Document ID", "Aliases", "Actions"]
    active_nav = "tags"
    search_fields = ("name", "slug", "document_id")
    detail_url_name = "admin_app:tag-update"
    delete_url_name = "admin_app:tag-delete"


class TagCreateView(AdminAppFormView, CreateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy("admin_app:tag-list")
    page_title = "Create Tag"
    page_subtitle = "Add a new tag and optional aliases."
    success_message = "Tag created successfully."
    active_nav = "tags"


class TagUpdateView(AdminAppFormView, UpdateView):
    model = Tag
    form_class = TagForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:tag-list")
    page_title = "Edit Tag"
    page_subtitle = "Update tag metadata."
    success_message = "Tag updated successfully."
    active_nav = "tags"


class TagDeleteView(AdminAppDeleteView):
    model = Tag
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:tag-list")
    page_title = "Delete Tag"
    page_subtitle = "Delete the selected tag."
    success_message = "Tag deleted successfully."
    active_nav = "tags"


class CommentListView(AdminAppListView):
    model = Comment
    queryset = Comment.objects.select_related("author", "parent").order_by("-created_at")
    page_title = "Comments"
    page_subtitle = "Review comment threads and moderation status."
    create_url_name = "admin_app:comment-create"
    create_label = "New Comment"
    columns = ["Author", "Target", "Status", "Created", "Actions"]
    active_nav = "comments"
    search_fields = ("author_name", "author_email", "document_id", "target_document_id")
    detail_url_name = "admin_app:comment-update"
    delete_url_name = "admin_app:comment-delete"


class CommentCreateView(AdminAppFormView, CreateView):
    model = Comment
    form_class = CommentForm
    success_url = reverse_lazy("admin_app:comment-list")
    page_title = "Create Comment"
    page_subtitle = "Create or backfill a comment."
    success_message = "Comment created successfully."
    active_nav = "comments"


class CommentUpdateView(AdminAppFormView, UpdateView):
    model = Comment
    form_class = CommentForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:comment-list")
    page_title = "Edit Comment"
    page_subtitle = "Update content and moderation status."
    success_message = "Comment updated successfully."
    active_nav = "comments"


class CommentDeleteView(AdminAppDeleteView):
    model = Comment
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:comment-list")
    page_title = "Delete Comment"
    page_subtitle = "Delete the selected comment."
    success_message = "Comment deleted successfully."
    active_nav = "comments"


class ReportListView(AdminAppAccessMixin, TemplateView):
    template_name = "admin_app/report_list.html"
    active_nav = "reports"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "")

        qs = Report.objects.select_related("reporter").order_by("-created_at")
        if q:
            qs = qs.filter(
                Q(target_document_id__icontains=q) |
                Q(reporter__email__icontains=q) |
                Q(reason__icontains=q)
            )
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Collect all reports and resolve target titles
        reports = list(qs)
        post_ids = {r.target_document_id for r in reports if r.target_type == "post"}
        comment_ids = {r.target_document_id for r in reports if r.target_type == "comment"}
        post_titles = {p.document_id: p.title for p in Post.objects.filter(document_id__in=post_ids).only("document_id", "title")}
        comment_posts = {}
        if comment_ids:
            comments = Comment.objects.filter(document_id__in=comment_ids).select_related().only("document_id", "target_document_id")
            for c in comments:
                comment_posts[c.document_id] = c.target_document_id
            extra_post_ids = set(comment_posts.values()) - set(post_titles.keys())
            if extra_post_ids:
                post_titles.update({p.document_id: p.title for p in Post.objects.filter(document_id__in=extra_post_ids).only("document_id", "title")})

        def resolve_title(target_type, target_document_id):
            if target_type == "post":
                return post_titles.get(target_document_id)
            if target_type == "comment":
                post_id = comment_posts.get(target_document_id)
                return post_titles.get(post_id) if post_id else None
            return None

        # Group by target_type + target_document_id
        groups = {}
        for report in reports:
            key = (report.target_type, report.target_document_id)
            if key not in groups:
                groups[key] = {
                    "target_type": report.target_type,
                    "target_document_id": report.target_document_id,
                    "target_title": resolve_title(report.target_type, report.target_document_id),
                    "target_state": resolve_report_target_state(report.target_type, report.target_document_id),
                    "reports": [],
                    "pending_count": 0,
                }
            groups[key]["reports"].append(report)
            if report.status == "pending":
                groups[key]["pending_count"] += 1

        context.update({
            "report_groups": list(groups.values()),
            "query": q,
            "status_filter": status_filter,
            "status_choices": ReportStatus.choices,
            "page_title": "Reports",
            "admin_navigation": self.get_navigation(),
            "admin_bottom_navigation": self.get_bottom_navigation(),
            "active_nav": self.active_nav,
        })
        return context


class ReportCreateView(AdminAppFormView, CreateView):
    model = Report
    form_class = ReportForm
    success_url = reverse_lazy("admin_app:report-list")
    page_title = "Create Report"
    page_subtitle = "Create a moderation report."
    success_message = "Report created successfully."
    active_nav = "reports"

    def form_valid(self, form):
        if not form.instance.reporter_id:
            form.instance.reporter = self.request.user
        return super().form_valid(form)


class ReportUpdateView(AdminAppFormView, UpdateView):
    model = Report
    form_class = ReportForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:report-list")
    page_title = "Edit Report"
    page_subtitle = "Update report status and moderator notes."
    success_message = "Report updated successfully."
    active_nav = "reports"


class ReportDeleteView(AdminAppDeleteView):
    model = Report
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:report-list")
    page_title = "Delete Report"
    page_subtitle = "Delete the selected report."
    success_message = "Report deleted successfully."
    active_nav = "reports"


class ModeratorListView(AdminAppListView):
    model = ModeratorCategoryAssignment
    queryset = ModeratorCategoryAssignment.objects.select_related("moderator", "category").order_by("-created_at")
    page_title = "Moderators"
    page_subtitle = "Assign moderator coverage by category."
    create_url_name = "admin_app:moderator-create"
    create_label = "New Assignment"
    columns = ["Moderator", "Role", "Category", "Assigned", "Actions"]
    active_nav = "moderators"
    search_fields = ("moderator__email", "category__name")
    detail_url_name = "admin_app:moderator-update"
    delete_url_name = "admin_app:moderator-delete"


class ModeratorCreateView(AdminAppFormView, CreateView):
    model = ModeratorCategoryAssignment
    form_class = ModeratorAssignmentForm
    success_url = reverse_lazy("admin_app:moderator-list")
    page_title = "Create Moderator Assignment"
    page_subtitle = "Assign a moderator to a category."
    success_message = "Moderator assignment created successfully."
    active_nav = "moderators"


class ModeratorUpdateView(AdminAppFormView, UpdateView):
    model = ModeratorCategoryAssignment
    form_class = ModeratorAssignmentForm
    success_url = reverse_lazy("admin_app:moderator-list")
    page_title = "Edit Moderator Assignment"
    page_subtitle = "Update a moderator assignment."
    success_message = "Moderator assignment updated successfully."
    active_nav = "moderators"


class ModeratorDeleteView(AdminAppDeleteView):
    model = ModeratorCategoryAssignment
    success_url = reverse_lazy("admin_app:moderator-list")
    page_title = "Delete Moderator Assignment"
    page_subtitle = "Remove the selected moderator assignment."
    success_message = "Moderator assignment deleted successfully."
    active_nav = "moderators"


class UserListView(AdminAppListView):
    model = User
    queryset = User.objects.order_by("email")
    page_title = "Users"
    page_subtitle = "Overview of Trekky users and seeded user pools."
    columns = ["Email", "Username", "Role", "Staff", "Joined"]
    active_nav = "users"
    search_fields = ("email", "username")
    create_url_name = "admin_app:user-create"
    create_label = "New User"
    detail_url_name = "admin_app:user-update"
    delete_url_name = "admin_app:user-delete"

    def get_user_tab(self):
        tab = str(self.request.GET.get("tab") or "user").strip().lower()
        return tab if tab in {"user", "seed"} else "user"

    def get_queryset(self):
        queryset = super().get_queryset()
        generated_seed_filter = Q(is_seeded=True, bio__startswith="Seed user:")
        if self.get_user_tab() == "seed":
            return queryset.filter(generated_seed_filter)
        return queryset.exclude(generated_seed_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        generated_seed_users = User.objects.filter(is_seeded=True, bio__startswith="Seed user:")
        current_tab = self.get_user_tab()
        context["current_user_tab"] = current_tab
        context["generated_seed_user_count"] = generated_seed_users.count()
        context["seed_default_password"] = DEFAULT_SEED_PASSWORD
        context["page_subtitle"] = "System users and internal accounts." if current_tab == "user" else "Generated seeded users for demo, AI, and test flows."
        context["columns"] = ["Email", "Username", "Role", "Staff", "Joined", "Actions"] if current_tab == "user" else ["Select", "Email", "Username", "Joined"]
        return context


class UserSeedCreateView(AdminAppAccessMixin, View):
    def post(self, request):
        try:
            count = int(request.POST.get("count") or 20)
        except (TypeError, ValueError):
            messages.error(request, "Seed count must be an integer between 1 and 200.")
            return redirect(f"{reverse('admin_app:user-list')}?tab=seed")

        if count < 1 or count > 200:
            messages.error(request, "Seed count must be between 1 and 200.")
            return redirect(f"{reverse('admin_app:user-list')}?tab=seed")

        existing_suffixes = set()
        for user in User.objects.filter(is_seeded=True).only("username"):
            match = re.search(r"(\d+)$", user.username or "")
            if match:
                existing_suffixes.add(int(match.group(1)))

        next_index = (max(existing_suffixes) + 1) if existing_suffixes else 1
        created = 0
        while created < count:
            draft = build_seed_user_draft(next_index)
            next_index += 1
            if User.objects.filter(Q(email=draft["email"]) | Q(username=draft["username"])).exists():
                continue
            User.objects.create_user(
                email=draft["email"],
                username=draft["username"],
                password=DEFAULT_SEED_PASSWORD,
                role="user",
                is_seeded=True,
                first_name=draft["display_name"],
                bio=f'Seed user: {draft["display_name"]}',
            )
            created += 1

        messages.success(request, f"Created {created} seeded users. Default password: {DEFAULT_SEED_PASSWORD}")
        return redirect(f"{reverse('admin_app:user-list')}?tab=seed")


class UserSeedDeleteView(AdminAppAccessMixin, View):
    def post(self, request):
        raw_ids = request.POST.getlist("selected_ids")
        selected_ids = [int(value) for value in raw_ids if str(value).isdigit()]
        if not selected_ids:
            messages.error(request, "Select at least one seeded user to delete.")
            return redirect(f"{reverse('admin_app:user-list')}?tab=seed")

        queryset = User.objects.filter(id__in=selected_ids, is_seeded=True, bio__startswith="Seed user:")
        deleted_count = queryset.count()
        queryset.delete()
        messages.success(request, f"Deleted {deleted_count} generated seeded users.")
        return redirect(f"{reverse('admin_app:user-list')}?tab=seed")


class UserCreateView(AdminAppFormView, CreateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy("admin_app:user-list")
    page_title = "Create User"
    page_subtitle = "Add a new user account."
    success_message = "User created successfully."
    active_nav = "users"


class UserUpdateView(AdminAppFormView, UpdateView):
    model = User
    form_class = UserForm
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:user-list")
    page_title = "Edit User"
    page_subtitle = "Update user account details."
    success_message = "User updated successfully."
    active_nav = "users"


class UserDeleteView(AdminAppDeleteView):
    model = User
    slug_field = "document_id"
    slug_url_kwarg = "document_id"
    success_url = reverse_lazy("admin_app:user-list")
    page_title = "Delete User"
    page_subtitle = "Permanently delete this user account."
    success_message = "User deleted successfully."
    active_nav = "users"


class SettingsView(AdminAppAccessMixin, TemplateView):
    template_name = "admin_app/settings.html"
    active_nav = "settings"
    default_tab = ""

    def get_active_tab(self):
        active_tab = (self.request.POST.get("active_tab") or self.request.GET.get("tab") or self.default_tab).strip()
        return active_tab or self.default_tab

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ga4 = GA4AnalyticsSettings.objects.order_by("-updated_at").first() or GA4AnalyticsSettings()
        ai = AIAutomationSettings.objects.order_by("-updated_at").first() or AIAutomationSettings()
        media = MediaStorageSettings.objects.order_by("-updated_at").first() or MediaStorageSettings()
        google_oauth = GoogleOAuthSettings.get_solo()
        email_auth = EmailAuthSettings.get_solo()
        context["page_title"] = "Settings"
        context["page_subtitle"] = "Manage AI, media, authentication, and email delivery settings."
        context["ga4_form"] = kwargs.get("ga4_form") or GA4SettingsForm(instance=ga4, prefix="ga4")
        context["ai_form"] = kwargs.get("ai_form") or AISettingsForm(instance=ai, prefix="ai")
        context["media_form"] = kwargs.get("media_form") or MediaStorageSettingsForm(instance=media, prefix="media")
        context["google_oauth_form"] = kwargs.get("google_oauth_form") or GoogleOAuthSettingsForm(instance=google_oauth, prefix="google_oauth")
        context["email_auth_form"] = kwargs.get("email_auth_form") or EmailAuthSettingsForm(instance=email_auth, prefix="email_auth")
        context["active_settings_tab"] = kwargs.get("active_settings_tab") or self.get_active_tab()
        return context

    def post(self, request, *args, **kwargs):
        ga4 = GA4AnalyticsSettings.objects.order_by("-updated_at").first() or GA4AnalyticsSettings()
        ai = AIAutomationSettings.objects.order_by("-updated_at").first() or AIAutomationSettings()
        media = MediaStorageSettings.objects.order_by("-updated_at").first() or MediaStorageSettings()
        google_oauth = GoogleOAuthSettings.get_solo()
        email_auth = EmailAuthSettings.get_solo()
        active_tab = self.get_active_tab()
        action = (request.POST.get("action") or "").strip()
        ga4_form = GA4SettingsForm(request.POST, instance=ga4, prefix="ga4")
        ai_form = AISettingsForm(request.POST, instance=ai, prefix="ai")
        media_form = MediaStorageSettingsForm(request.POST, instance=media, prefix="media")
        google_oauth_form = GoogleOAuthSettingsForm(request.POST, instance=google_oauth, prefix="google_oauth")
        email_auth_form = EmailAuthSettingsForm(request.POST, instance=email_auth, prefix="email_auth")
        if ga4_form.is_valid() and ai_form.is_valid() and media_form.is_valid() and google_oauth_form.is_valid() and email_auth_form.is_valid():
            ga4_form.save()
            ai_form.save()
            media_form.save()
            google_oauth_form.save()
            email_auth_form.save()
            if action == "run_ai_content_test":
                try:
                    result = run_content_automation()
                    messages.success(
                        request,
                        f"AI content test run completed: created {result.get('created_posts', 0)} post(s), uploaded {result.get('uploaded_images', 0)} image(s).",
                    )
                except Exception as exc:
                    messages.error(request, f"AI content test run failed: {exc}")
                return redirect(f"{reverse('admin_app:settings')}?tab={active_tab}")
            if action == "run_ai_comment_test":
                try:
                    result = run_comment_automation()
                    messages.success(
                        request,
                        f"AI comment test run completed: created {result.get('created_comments', 0)} comment(s).",
                    )
                except Exception as exc:
                    messages.error(request, f"AI comment test run failed: {exc}")
                return redirect(f"{reverse('admin_app:settings')}?tab={active_tab}")
            messages.success(request, "Settings updated successfully.")
            return redirect(f"{reverse('admin_app:settings')}?tab={active_tab}")
        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(
            self.get_context_data(
                ga4_form=ga4_form,
                ai_form=ai_form,
                media_form=media_form,
                google_oauth_form=google_oauth_form,
                email_auth_form=email_auth_form,
                active_settings_tab=active_tab,
            )
        )


class PostToggleStatusView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        post = get_object_or_404(Post, document_id=document_id)
        post.is_published = not post.is_published
        post.save()
        message = "Post status updated."
        if is_ajax_request(request):
            label = "Published" if post.is_published else "Draft"
            return build_toggle_response(
                is_on=post.is_published,
                title=label,
                aria_label=label,
                message=message,
            )
        messages.success(request, message)
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_app:post-list"))


class PageToggleStatusView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        page = get_object_or_404(Page, document_id=document_id)
        page.is_published = not page.is_published
        page.save()
        message = "Page status updated."
        if is_ajax_request(request):
            label = "Published" if page.is_published else "Draft"
            return build_toggle_response(
                is_on=page.is_published,
                title=label,
                aria_label=label,
                message=message,
            )
        messages.success(request, message)
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_app:page-list"))


class CategoryToggleStatusView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        category = get_object_or_404(Category, document_id=document_id)
        category.status = CategoryStatus.DRAFT if category.status == CategoryStatus.PUBLISHED else CategoryStatus.PUBLISHED
        category.save(update_fields=["status", "updated_at"])
        message = "Category status updated."
        if is_ajax_request(request):
            return build_toggle_response(
                is_on=category.status == CategoryStatus.PUBLISHED,
                title=category.status,
                aria_label=category.status,
                message=message,
            )
        messages.success(request, message)
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_app:category-list"))


class CommentToggleStatusView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        comment = get_object_or_404(Comment, document_id=document_id)
        comment.status = CommentStatus.PENDING if comment.status == CommentStatus.PUBLISHED else CommentStatus.PUBLISHED
        comment.save()
        message = "Comment status updated."
        if is_ajax_request(request):
            return build_toggle_response(
                is_on=comment.status == CommentStatus.PUBLISHED,
                title=comment.status,
                aria_label=comment.status,
                message=message,
            )
        messages.success(request, message)
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_app:comment-list"))


class ReportApproveView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        report = get_object_or_404(Report, document_id=document_id)
        resolution = resolve_reports_for_target(moderator=request.user, report=report, approved=True)
        target_label = "post" if report.target_type == "post" else report.target_type
        if resolution["target_missing"]:
            messages.success(request, f"Approved {resolution['resolved_count']} report(s); target {target_label} no longer exists.")
        elif report.target_type == "post":
            messages.success(request, f"Approved {resolution['resolved_count']} report(s) and hid the post.")
        elif report.target_type == "comment":
            messages.success(request, f"Approved {resolution['resolved_count']} report(s) and hid the comment.")
        else:
            messages.success(request, f"Approved {resolution['resolved_count']} report(s).")
        return redirect("admin_app:report-list")


class ReportRejectView(AdminAppAccessMixin, View):
    def post(self, request, document_id):
        report = get_object_or_404(Report, document_id=document_id)
        resolution = resolve_reports_for_target(moderator=request.user, report=report, approved=False)
        if resolution["target_missing"]:
            messages.success(request, f"Rejected {resolution['resolved_count']} report(s); target no longer exists.")
        else:
            messages.success(request, f"Rejected {resolution['resolved_count']} report(s). The {report.target_type} was unchanged.")
        return redirect("admin_app:report-list")
