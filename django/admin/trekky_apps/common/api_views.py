import mimetypes
import re

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils.text import slugify
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from trekky_apps.accounts.serializers import ProfileUpdateSerializer, UserSerializer
from trekky_apps.accounts.seed_users import DEFAULT_SEED_PASSWORD, build_seed_user_draft
from trekky_apps.common.permissions import IsAdminOrEditor, IsModerator
from trekky_apps.content.cloudinary_service import (
    CloudinaryServiceError,
    MediaQuery,
    delete_asset,
    get_asset,
    list_assets,
    list_folder_tree,
    upload_asset,
)
from trekky_apps.content.media_services import attach_media_assets_to_post, create_media_asset_from_upload
from trekky_apps.content.models import Comment, MediaAsset, Page, Post
from trekky_apps.content.serializers import (
    CommentSerializer,
    MediaAssetSerializer,
    MyPostWriteSerializer,
    PageSerializer,
    PostSerializer,
)
from trekky_apps.engagement.models import Interaction, Report
from trekky_apps.engagement.serializers import InteractionSerializer, ReportSerializer
from trekky_apps.integrations.models import AIAutomationSettings, GA4AnalyticsSettings, GoogleOAuthSettings, MediaStorageSettings
from trekky_apps.integrations.serializers import AIAutomationSettingsSerializer, GA4AnalyticsSettingsSerializer, GoogleOAuthSettingsSerializer, MediaStorageSettingsSerializer
from trekky_apps.moderation.models import ModerationAction, ModeratorCategoryAssignment
from trekky_apps.moderation.serializers import ModerationActionSerializer, ModeratorCategoryAssignmentSerializer
from trekky_apps.common import search_service
from trekky_apps.taxonomy.models import Category, Tag
from trekky_apps.taxonomy.serializers import CategorySerializer, TagSerializer


User = get_user_model()


def _file_url(file_field):
    if not file_field:
        return None
    try:
        return file_field.url
    except Exception:
        return None


def _media_asset_url(asset):
    if not asset:
        return None
    return getattr(asset, "cloudinary_secure_url", "") or _file_url(getattr(asset, "file", None))


def legacy_user_payload(user):
    return {
        "id": user.id,
        "documentId": user.document_id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "avatar": {"url": _file_url(user.avatar)} if user.avatar else None,
    }


def legacy_post_payload(post: Post):
    return {
        "id": post.id,
        "documentId": post.document_id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "content": post.content,
        "createdAt": post.created_at.isoformat() if post.created_at else None,
        "updatedAt": post.updated_at.isoformat() if post.updated_at else None,
        "publishedAt": post.published_at.isoformat() if post.published_at else None,
        "categories": [
            {
                "id": category.id,
                "documentId": category.document_id,
                "name": category.name,
                "slug": category.slug,
            }
            for category in post.categories.all()
        ],
        "tags": [
            {
                "id": tag.id,
                "documentId": tag.document_id,
                "name": tag.name,
                "slug": tag.slug,
            }
            for tag in post.tags.all()
        ],
        "images": [
            {
                "id": asset.media_asset_id or asset.id,
                "url": _media_asset_url(asset.media_asset if getattr(asset, "media_asset", None) else asset),
                "mime": mimetypes.guess_type(asset.file.name)[0],
                "alternativeText": asset.alt_text,
            }
            for asset in post.assets.all()
        ],
        "author": {
            "id": post.author.id,
            "documentId": post.author.document_id,
            "username": post.author.username,
            "avatar": {"url": _file_url(post.author.avatar)} if post.author and post.author.avatar else None,
        }
        if post.author
        else None,
    }


def legacy_report_payload(report: Report):
    return {
        "id": report.id,
        "documentId": report.document_id,
        "targetType": report.target_type,
        "targetDocumentId": report.target_document_id,
        "reason": report.reason,
        "status": report.status,
        "moderatorNote": report.moderator_note,
        "createdAt": report.created_at.isoformat() if report.created_at else None,
        "updatedAt": report.updated_at.isoformat() if report.updated_at else None,
    }


def _resolve_category_documents(values):
    if not values:
        return []
    normalized = [str(value).strip() for value in values if str(value).strip()]
    int_values = [int(value) for value in normalized if value.isdigit()]
    categories = Category.objects.none()
    if int_values:
        categories = Category.objects.filter(id__in=int_values)
    if normalized:
        categories = categories | Category.objects.filter(document_id__in=normalized)
    return list(categories.distinct())


def _resolve_tag_documents(values):
    if not values:
        return []
    normalized = [str(value).strip() for value in values if str(value).strip()]
    int_values = [int(value) for value in normalized if value.isdigit()]
    tags = Tag.objects.none()
    if int_values:
        tags = Tag.objects.filter(id__in=int_values)
    if normalized:
        tags = tags | Tag.objects.filter(document_id__in=normalized)
    return list(tags.distinct())


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class PublicUserPostsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = generics.get_object_or_404(User, username=username)
        posts = (
            Post.objects.filter(author=user, is_published=True)
            .select_related("author")
            .prefetch_related("categories", "tags", "assets")
            .order_by("-published_at", "-created_at")
        )
        return Response({"user": UserSerializer(user).data, "results": PostSerializer(posts, many=True).data})


class PublicPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PublicPostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "document_id"
    permission_classes = [AllowAny]
    pagination_class = PublicPagination
    queryset = Post.objects.filter(is_published=True).prefetch_related("categories", "tags", "assets", "author")
    search_fields = ("title", "excerpt", "content")
    filterset_fields = ("categories__document_id", "tags__document_id", "slug")


class PublicPageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PageSerializer
    lookup_field = "document_id"
    permission_classes = [AllowAny]
    queryset = Page.objects.filter(is_published=True)
    filterset_fields = ("type", "slug")


class PublicCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = "document_id"
    permission_classes = [AllowAny]
    queryset = Category.objects.select_related("parent").filter(status="published")


class PublicTagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    lookup_field = "document_id"
    filterset_fields = ("slug",)
    permission_classes = [AllowAny]
    pagination_class = PublicPagination
    queryset = (
        Tag.objects.annotate(
            published_post_count=Count("posts", filter=Q(posts__is_published=True), distinct=True)
        )
        .filter(published_post_count__gt=0)
        .order_by("-published_post_count", "name")
    )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    lookup_field = "document_id"

    def get_queryset(self):
        queryset = Comment.objects.select_related("author", "parent")
        target_type = self.request.query_params.get("target_type")
        target_document_id = self.request.query_params.get("target_document_id")
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_document_id:
            queryset = queryset.filter(target_document_id=target_document_id)
        if self.request.user.is_authenticated and self.request.user.role in {"admin", "editor", "moderator"}:
            return queryset
        return queryset.filter(status="published")

    def get_permissions(self):
        if self.action in {"create"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            author_name=self.request.user.username or self.request.user.email,
            author_email=self.request.user.email,
            status="published",
        )


class InteractionViewSet(viewsets.ModelViewSet):
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Interaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role in {"admin", "editor"}:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class AdminPostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Post.objects.prefetch_related("categories", "tags", "assets", "author").all()


class AdminPageViewSet(viewsets.ModelViewSet):
    serializer_class = PageSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Page.objects.all()


class AdminCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Category.objects.all()


class AdminTagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Tag.objects.all()


class AdminCommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Comment.objects.select_related("author", "parent").all()


class AdminReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = Report.objects.all()


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = User.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        queryset = User.objects.all().order_by("id")
        keyword = str(self.request.query_params.get("q") or "").strip()
        is_seeded = str(self.request.query_params.get("isSeeded") or "false").lower() == "true"
        if is_seeded:
            queryset = queryset.filter(is_seeded=True)
        if keyword:
            queryset = queryset.filter(Q(email__icontains=keyword) | Q(username__icontains=keyword))
        return queryset


class MyPostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "document_id"

    def get_queryset(self):
        return (
            Post.objects.filter(author=self.request.user)
            .select_related("author")
            .prefetch_related("categories", "tags", "assets")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return MyPostWriteSerializer
        return PostSerializer

    def _apply_relations(self, post: Post, validated_data: dict):
        category_document_ids = validated_data.pop("category_document_ids", None)
        tag_document_ids = validated_data.pop("tag_document_ids", None)
        image_ids = validated_data.pop("image_ids", None)
        status_value = validated_data.pop("status", None)

        for attr, value in validated_data.items():
            setattr(post, attr, value)

        if status_value:
            post.is_published = status_value == "published"

        post.author = self.request.user
        post.save()

        if category_document_ids is not None:
            categories = Category.objects.filter(document_id__in=category_document_ids)
            post.categories.set(categories)

        if tag_document_ids is not None:
            tags = Tag.objects.filter(document_id__in=tag_document_ids)
            post.tags.set(tags)

        if image_ids is not None:
            attach_media_assets_to_post(post, image_ids)

        return post

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = self._apply_relations(Post(), serializer.validated_data)
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        post = self._apply_relations(instance, serializer.validated_data)
        return Response(PostSerializer(post).data)


class MyPostPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        post = generics.get_object_or_404(Post, document_id=document_id, author=request.user)
        post.is_published = True
        post.save()
        return Response(PostSerializer(post).data)


class MyPostUnpublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        post = generics.get_object_or_404(Post, document_id=document_id, author=request.user)
        post.is_published = False
        post.save()
        return Response(PostSerializer(post).data)


class ModeratorAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = ModeratorCategoryAssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = ModeratorCategoryAssignment.objects.select_related("moderator", "category").all()


class ModeratorQueueView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]

    def get(self, request):
        assignments = ModeratorCategoryAssignment.objects.filter(moderator=request.user).values_list("category_id", flat=True)
        posts = Post.objects.filter(categories__id__in=assignments).distinct().count()
        comments = Comment.objects.filter(
            target_type="post",
            target_document_id__in=Post.objects.filter(categories__id__in=assignments).values_list("document_id", flat=True),
        ).count()
        pending_reports = Report.objects.filter(status="pending").count()
        return Response(
            {
                "assigned_categories": len(set(assignments)),
                "posts": posts,
                "comments": comments,
                "pending_reports": pending_reports,
            }
        )


class ModerationActionViewSet(viewsets.ModelViewSet):
    serializer_class = ModerationActionSerializer
    permission_classes = [IsAuthenticated, IsModerator]
    queryset = ModerationAction.objects.select_related("moderator").all()

    def perform_create(self, serializer):
        serializer.save(moderator=self.request.user)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        payload = {
            "posts": Post.objects.count(),
            "published_posts": Post.objects.filter(is_published=True).count(),
            "comments": Comment.objects.count(),
            "pending_reports": Report.objects.filter(status="pending").count(),
            "moderators": User.objects.filter(role="moderator").count(),
            "categories": Category.objects.count(),
            "tags": Tag.objects.count(),
            "top_categories": list(
                Category.objects.annotate(post_count=Count("posts"))
                .order_by("-post_count", "name")
                .values("name", "post_count")[:5]
            ),
        }
        return Response(payload)


class IntegrationSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        ga4 = GA4AnalyticsSettings.objects.order_by("-updated_at").first()
        ai = AIAutomationSettings.objects.order_by("-updated_at").first()
        media = MediaStorageSettings.objects.order_by("-updated_at").first()
        google_oauth = GoogleOAuthSettings.objects.order_by("-updated_at").first()
        return Response(
            {
                "ga4": GA4AnalyticsSettingsSerializer(ga4).data if ga4 else None,
                "ai": AIAutomationSettingsSerializer(ai).data if ai else None,
                "media": MediaStorageSettingsSerializer(media).data if media else None,
                "google_oauth": GoogleOAuthSettingsSerializer(google_oauth).data if google_oauth else None,
            }
        )


class PublicSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if not q:
            return Response({"posts": [], "tags": [], "categories": []})
        results = search_service.search(q)
        return Response(results)


class AdminRoleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        return Response(
            {
                "data": [
                    {"id": "admin", "name": "Admin", "type": "admin"},
                    {"id": "editor", "name": "Editor", "type": "editor"},
                    {"id": "moderator", "name": "Moderator", "type": "moderator"},
                    {"id": "user", "name": "User", "type": "authenticated"},
                ]
            }
        )


class AdminMediaFoldersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        try:
            return Response({"items": list_folder_tree()})
        except CloudinaryServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class AdminMediaAssetsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        query = MediaQuery(
            folder=str(request.query_params.get("folder") or ""),
            query=str(request.query_params.get("q") or ""),
            resource_type=str(request.query_params.get("resource_type") or "image"),
            sort_by=str(request.query_params.get("sort_by") or "created_at"),
            sort_dir=str(request.query_params.get("sort_dir") or "desc"),
            next_cursor=str(request.query_params.get("next_cursor") or ""),
            max_results=int(request.query_params.get("max_results") or 30),
        )
        try:
            payload = list_assets(query, uploader=request.user)
            return Response(payload)
        except CloudinaryServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class AdminMediaUploadView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist("files") or ([request.FILES["file"]] if "file" in request.FILES else [])
        if not files:
            return Response({"error": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        folder = str(request.data.get("folder") or "")
        items = []
        try:
            for file_obj in files:
                items.append(upload_asset(file_obj, folder=folder, uploader=request.user))
            return Response({"items": items}, status=status.HTTP_201_CREATED)
        except CloudinaryServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class AdminMediaDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def get(self, request):
        public_id = str(request.query_params.get("public_id") or "")
        try:
            return Response({"item": get_asset(public_id, uploader=request.user)})
        except CloudinaryServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)


class AdminMediaDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    parser_classes = [JSONParser]

    def post(self, request):
        public_id = str(request.data.get("public_id") or "")
        resource_type = str(request.data.get("resource_type") or "image")
        try:
            return Response(delete_asset(public_id, resource_type=resource_type))
        except CloudinaryServiceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class AdminSeedUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def post(self, request):
        raw_count = request.data.get("count", 20)
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            return Response({"error": {"message": "count must be an integer between 1 and 500"}}, status=400)

        if count < 1 or count > 500:
            return Response({"error": {"message": "count must be an integer between 1 and 500"}}, status=400)

        seeded_users = User.objects.filter(is_seeded=True).only("username")
        used_suffixes: set[int] = set()
        for user in seeded_users:
            match = re.search(r"(\d+)$", user.username or "")
            if match:
                used_suffixes.add(int(match.group(1)))
        next_index = (max(used_suffixes) + 1) if used_suffixes else 1

        created_count = 0
        start_username = None
        end_username = None

        while created_count < count:
            draft = build_seed_user_draft(next_index)
            next_index += 1
            if User.objects.filter(Q(username=draft["username"]) | Q(email=draft["email"])).exists():
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
            created_count += 1
            if not start_username:
                start_username = draft["username"]
            end_username = draft["username"]

        return Response(
            {
                "data": {
                    "createdCount": created_count,
                    "startUsername": start_username,
                    "endUsername": end_username,
                    "defaultPasswordHint": DEFAULT_SEED_PASSWORD,
                }
            }
        )


class AdminBatchDeleteSeedUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrEditor]

    def post(self, request):
        raw_ids = request.data.get("ids") if isinstance(request.data, dict) else []
        normalized_ids = sorted({int(value) for value in (raw_ids or []) if str(value).isdigit() and int(value) > 0})
        if not normalized_ids:
            return Response({"data": {"requestedCount": 0, "deletedCount": 0, "skippedCount": 0}})

        rows = list(User.objects.filter(id__in=normalized_ids).only("id", "is_seeded"))
        seeded_ids = [row.id for row in rows if row.is_seeded]
        deleted_count = len(seeded_ids)
        if seeded_ids:
            User.objects.filter(id__in=seeded_ids).delete()
        return Response(
            {
                "data": {
                    "requestedCount": len(normalized_ids),
                    "deletedCount": deleted_count,
                    "skippedCount": len(normalized_ids) - deleted_count,
                }
            }
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def permalink_lookup(request, document_id):
    post = generics.get_object_or_404(Post, document_id=document_id)
    expected_slug = post.slug
    requested_slug = request.query_params.get("slug")
    payload = PostSerializer(post).data
    if requested_slug and requested_slug != expected_slug:
        payload["redirect_to"] = post.permalink
    return Response(payload)


class LegacyMeView(MeView):
    def get(self, request):
        return Response(legacy_user_payload(request.user))

    def put(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(legacy_user_payload(request.user))


class LegacyUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": {"message": "No files uploaded"}}, status=status.HTTP_400_BAD_REQUEST)

        uploaded = []
        for file_obj in files:
            asset = create_media_asset_from_upload(file_obj, uploader=request.user)
            uploaded.append(
                {
                    "id": asset.id,
                    "documentId": asset.document_id,
                    "url": _media_asset_url(asset),
                    "alternativeText": asset.alt_text,
                    "name": asset.original_filename,
                    "mime": asset.mime_type,
                    "width": asset.width,
                    "height": asset.height,
                }
            )
        return Response(uploaded, status=status.HTTP_201_CREATED)


class LegacyMyPostsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_id = str(request.query_params.get("documentId") or "").strip()
        status_filter = str(request.query_params.get("status") or "all").strip()
        page = max(1, int(request.query_params.get("page", "1")))
        page_size = max(1, min(1000, int(request.query_params.get("pageSize", "10"))))

        queryset = (
            Post.objects.filter(author=request.user)
            .select_related("author")
            .prefetch_related("categories", "tags", "assets")
            .order_by("-updated_at")
        )
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        if status_filter == "published":
            queryset = queryset.filter(is_published=True)
        elif status_filter == "draft":
            queryset = queryset.filter(is_published=False)

        total = queryset.count()
        start = (page - 1) * page_size
        rows = list(queryset[start : start + page_size])
        payload = [legacy_post_payload(post) for post in rows]
        if document_id:
            return Response({"data": payload[0] if payload else None})
        return Response(
            {
                "data": payload,
                "meta": {
                    "pagination": {
                        "page": page,
                        "pageSize": page_size,
                        "pageCount": max(1, (total + page_size - 1) // page_size),
                        "total": total,
                    }
                },
            }
        )


class LegacyPostCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.get("data", request.data)
        title = str(data.get("title") or "").strip()
        content = str(data.get("content") or "").strip()
        excerpt = str(data.get("excerpt") or "").strip()
        slug = str(data.get("slug") or "").strip()
        category_values = data.get("categories") or []
        tag_values = data.get("tags") or []
        image_ids = [int(value) for value in (data.get("images") or []) if str(value).isdigit()]

        if not title or not content:
            return Response({"error": {"message": "Title and content are required"}}, status=status.HTTP_400_BAD_REQUEST)

        post = Post(title=title, excerpt=excerpt, content=content, slug=slug, author=request.user)
        if data.get("publishedAt"):
            post.is_published = True
        post.save()
        post.categories.set(_resolve_category_documents(category_values))
        post.tags.set(_resolve_tag_documents(tag_values))
        if image_ids:
            attach_media_assets_to_post(post, image_ids)
        post.refresh_from_db()
        return Response({"data": legacy_post_payload(post)}, status=status.HTTP_201_CREATED)


class LegacyPostUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, document_id):
        post = generics.get_object_or_404(Post, document_id=document_id, author=request.user)
        data = request.data.get("data", request.data)
        title = data.get("title")
        content = data.get("content")
        excerpt = data.get("excerpt")
        slug = data.get("slug")
        category_values = data.get("categories")
        tag_values = data.get("tags")
        image_values = data.get("images")

        if title is not None:
            post.title = str(title).strip()
        if content is not None:
            post.content = str(content)
        if excerpt is not None:
            post.excerpt = str(excerpt)
        if slug is not None:
            post.slug = str(slug).strip()
        if "publishedAt" in data:
            post.is_published = bool(data.get("publishedAt"))
        post.save()

        if category_values is not None:
            post.categories.set(_resolve_category_documents(category_values))
        if tag_values is not None:
            post.tags.set(_resolve_tag_documents(tag_values))
        if image_values is not None:
            image_ids = [int(value) for value in image_values if str(value).isdigit()]
            attach_media_assets_to_post(post, image_ids)

        post.refresh_from_db()
        return Response({"data": legacy_post_payload(post)})


class LegacyPostPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        post = generics.get_object_or_404(Post, document_id=document_id, author=request.user)
        post.is_published = True
        post.save()
        return Response({"data": legacy_post_payload(post)})


class LegacyPostUnpublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        post = generics.get_object_or_404(Post, document_id=document_id, author=request.user)
        post.is_published = False
        post.save()
        return Response({"data": legacy_post_payload(post)})


class LegacyMyReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = [legacy_report_payload(item) for item in Report.objects.filter(reporter=request.user)]
        return Response({"data": rows})


class LegacyReportSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data.get("data", request.data)
        target_type = str(payload.get("targetType") or payload.get("target_type") or "").strip()
        target_document_id = str(payload.get("targetDocumentId") or payload.get("target_document_id") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        if not target_type or not target_document_id:
            return Response(
                {"error": {"message": "targetType and targetDocumentId are required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = Report.objects.create(
            reporter=request.user,
            target_type=target_type,
            target_document_id=target_document_id,
            reason=reason,
        )
        return Response({"data": legacy_report_payload(report)}, status=status.HTTP_201_CREATED)


class LegacyTagCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = str(request.data.get("name") or "").strip()
        if not name:
            return Response({"error": {"message": "Tag name is required"}}, status=status.HTTP_400_BAD_REQUEST)
        tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
        return Response(
            {
                "data": {
                    "id": tag.id,
                    "documentId": tag.document_id,
                    "name": tag.name,
                    "slug": tag.slug,
                }
            },
            status=status.HTTP_201_CREATED,
        )
