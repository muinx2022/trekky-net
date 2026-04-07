import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_defaults.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/paginated_response.dart';
import '../../../shared/models/post_summary.dart';
import '../../taxonomy/data/taxonomy_repository_impl.dart';
import '../domain/posts_repository.dart';

final postsRepositoryProvider = Provider<PostsRepository>((ref) {
  return PostsRepositoryImpl(
    ref.read(apiClientProvider),
    ref.read(taxonomyRepositoryProvider),
  );
});

class PostsRepositoryImpl implements PostsRepository {
  PostsRepositoryImpl(this._client, this._taxonomyRepository);

  final ApiClient _client;
  final TaxonomyRepositoryImpl _taxonomyRepository;

  @override
  Future<PaginatedResponse<PostSummary>> fetchHomeFeed() async {
    final response = await _client.get(
      '/public/posts/',
      queryParameters: {'page_size': AppDefaults.pageSize},
    );
    return PaginatedResponse.fromJson(response, PostSummary.fromJson);
  }

  @override
  Future<PostSummary> fetchPost(String documentId) async {
    final response = await _client.get('/public/posts/$documentId/');
    return PostSummary.fromJson(response);
  }

  @override
  Future<List<PostSummary>> fetchPostsByCategorySlug(String slug) async {
    final category = await _taxonomyRepository.fetchCategoryBySlug(slug);
    final response = await _client.get(
      '/public/posts/',
      queryParameters: {
        'categories__document_id': category.documentId,
        'page_size': 100,
      },
    );
    return PaginatedResponse.fromJson(response, PostSummary.fromJson).items;
  }

  @override
  Future<List<PostSummary>> fetchPostsByTagSlug(String slug) async {
    final tag = await _taxonomyRepository.fetchTagBySlug(slug);
    final response = await _client.get(
      '/public/posts/',
      queryParameters: {'tags__document_id': tag.documentId, 'page_size': 100},
    );
    return PaginatedResponse.fromJson(response, PostSummary.fromJson).items;
  }

  @override
  Future<List<PostSummary>> fetchPostsByUser(String username) async {
    final response = await _client.get('/public/users/$username/posts/');
    final results = response['results'] as List<dynamic>? ?? const [];
    return results
        .map((item) => PostSummary.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
