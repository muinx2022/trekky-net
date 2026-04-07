import '../../../shared/models/paginated_response.dart';
import '../../../shared/models/post_summary.dart';

abstract class PostsRepository {
  Future<PaginatedResponse<PostSummary>> fetchHomeFeed();

  Future<PostSummary> fetchPost(String documentId);

  Future<List<PostSummary>> fetchPostsByCategorySlug(String slug);

  Future<List<PostSummary>> fetchPostsByTagSlug(String slug);

  Future<List<PostSummary>> fetchPostsByUser(String username);
}
