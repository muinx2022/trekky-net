import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/category.dart';
import '../../../shared/models/tag.dart';
import '../domain/taxonomy_repository.dart';

final taxonomyRepositoryProvider = Provider<TaxonomyRepositoryImpl>((ref) {
  return TaxonomyRepositoryImpl(ref.read(apiClientProvider));
});

class TaxonomyRepositoryImpl implements TaxonomyRepository {
  TaxonomyRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<List<Category>> fetchCategories() async {
    final response = await _client.getList('/public/categories/');
    return response
        .map((item) => Category.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<Tag>> fetchTags() async {
    final response = await _client.get(
      '/public/tags/',
      queryParameters: {'page_size': 100},
    );
    final results = response['results'] as List<dynamic>? ?? const [];
    return results
        .map((item) => Tag.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<Category> fetchCategoryBySlug(String slug) async {
    final categories = await fetchCategories();
    return categories.firstWhere((category) => category.slug == slug);
  }

  @override
  Future<Tag> fetchTagBySlug(String slug) async {
    final tags = await fetchTags();
    return tags.firstWhere((tag) => tag.slug == slug);
  }
}
