from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from trekky_apps.accounts.views import ForgotPasswordView, GoogleOAuthCallbackView, GoogleOAuthInitView, RegisterView, ResetPasswordView

from .api_views import (
    AdminCategoryViewSet,
    AdminCommentViewSet,
    AdminMediaAssetsView,
    AdminMediaDeleteView,
    AdminMediaDetailView,
    AdminMediaFoldersView,
    AdminPageViewSet,
    AdminPostViewSet,
    AdminBatchDeleteSeedUsersView,
    AdminReportViewSet,
    AdminRoleListView,
    AdminSeedUsersView,
    AdminTagViewSet,
    AdminMediaUploadView,
    AdminUserViewSet,
    CommentViewSet,
    DashboardView,
    IntegrationSettingsView,
    LegacyMeView,
    LegacyMyPostsView,
    LegacyMyReportsView,
    LegacyPostCreateView,
    LegacyPostPublishView,
    LegacyPostUnpublishView,
    LegacyPostUpdateView,
    LegacyReportSubmitView,
    LegacyTagCreateView,
    LegacyUploadView,
    InteractionViewSet,
    MeView,
    MyPostPublishView,
    MyPostUnpublishView,
    MyPostViewSet,
    ModerationActionViewSet,
    ModeratorAssignmentViewSet,
    ModeratorQueueView,
    PublicCategoryViewSet,
    PublicPageViewSet,
    PublicPostViewSet,
    PublicTagViewSet,
    PublicSearchView,
    PublicUserPostsView,
    ReportViewSet,
    permalink_lookup,
)

public_router = DefaultRouter()
public_router.register("posts", PublicPostViewSet, basename="public-post")
public_router.register("pages", PublicPageViewSet, basename="public-page")
public_router.register("categories", PublicCategoryViewSet, basename="public-category")
public_router.register("tags", PublicTagViewSet, basename="public-tag")
public_router.register("comments", CommentViewSet, basename="comment")
public_router.register("interactions", InteractionViewSet, basename="interaction")
public_router.register("reports", ReportViewSet, basename="report")
public_router.register("me/posts", MyPostViewSet, basename="my-post")

me_router = DefaultRouter()
me_router.register("posts", MyPostViewSet, basename="me-post")

admin_router = DefaultRouter()
admin_router.register("posts", AdminPostViewSet, basename="admin-post")
admin_router.register("pages", AdminPageViewSet, basename="admin-page")
admin_router.register("categories", AdminCategoryViewSet, basename="admin-category")
admin_router.register("tags", AdminTagViewSet, basename="admin-tag")
admin_router.register("comments", AdminCommentViewSet, basename="admin-comment")
admin_router.register("reports", AdminReportViewSet, basename="admin-report")
admin_router.register("users", AdminUserViewSet, basename="admin-user")
admin_router.register("moderator-assignments", ModeratorAssignmentViewSet, basename="moderator-assignment")

mod_router = DefaultRouter()
mod_router.register("actions", ModerationActionViewSet, basename="moderation-action")

urlpatterns = [
    path("users/me", LegacyMeView.as_view(), name="legacy-me"),
    path("upload", LegacyUploadView.as_view(), name="legacy-upload"),
    path("posts/my-posts", LegacyMyPostsView.as_view(), name="legacy-my-posts"),
    path("posts/user-create", LegacyPostCreateView.as_view(), name="legacy-post-create"),
    path("posts/<str:document_id>/user-update", LegacyPostUpdateView.as_view(), name="legacy-post-update"),
    path("posts/<str:document_id>/user-publish", LegacyPostPublishView.as_view(), name="legacy-post-publish"),
    path("posts/<str:document_id>/user-unpublish", LegacyPostUnpublishView.as_view(), name="legacy-post-unpublish"),
    path("posts/<str:document_id>/publish", LegacyPostPublishView.as_view(), name="legacy-post-publish-alt"),
    path("posts/<str:document_id>/unpublish", LegacyPostUnpublishView.as_view(), name="legacy-post-unpublish-alt"),
    path("reports/mine", LegacyMyReportsView.as_view(), name="legacy-reports-mine"),
    path("reports/submit", LegacyReportSubmitView.as_view(), name="legacy-reports-submit"),
    path("tags/user-create", LegacyTagCreateView.as_view(), name="legacy-tag-create"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("auth/google/", GoogleOAuthInitView.as_view(), name="google-oauth-init"),
    path("auth/google/callback/", GoogleOAuthCallbackView.as_view(), name="google-oauth-callback"),
    path("me/", MeView.as_view(), name="me"),
    path("me/", include(me_router.urls)),
    path("me/posts/<str:document_id>/publish/", MyPostPublishView.as_view(), name="my-post-publish"),
    path("me/posts/<str:document_id>/unpublish/", MyPostUnpublishView.as_view(), name="my-post-unpublish"),
    path("public/search/", PublicSearchView.as_view(), name="public-search"),
    path("public/permalinks/<str:document_id>/", permalink_lookup, name="permalink-lookup"),
    path("public/users/<str:username>/posts/", PublicUserPostsView.as_view(), name="public-user-posts"),
    path("public/", include(public_router.urls)),
    path("admin/dashboard/", DashboardView.as_view(), name="admin-dashboard"),
    path("admin/media/folders/", AdminMediaFoldersView.as_view(), name="admin-media-folders"),
    path("admin/media/assets/", AdminMediaAssetsView.as_view(), name="admin-media-assets"),
    path("admin/media/assets/detail/", AdminMediaDetailView.as_view(), name="admin-media-detail"),
    path("admin/media/upload/", AdminMediaUploadView.as_view(), name="admin-media-upload"),
    path("admin/media/delete/", AdminMediaDeleteView.as_view(), name="admin-media-delete"),
    path("admin/settings/", IntegrationSettingsView.as_view(), name="admin-settings"),
    path("admin/roles/", AdminRoleListView.as_view(), name="admin-roles"),
    path("admin/users/seed/", AdminSeedUsersView.as_view(), name="admin-users-seed"),
    path("admin/users/seed/batch-delete/", AdminBatchDeleteSeedUsersView.as_view(), name="admin-users-seed-batch-delete"),
    path("admin/", include(admin_router.urls)),
    path("mod/queue/", ModeratorQueueView.as_view(), name="mod-queue"),
    path("mod/", include(mod_router.urls)),
]
