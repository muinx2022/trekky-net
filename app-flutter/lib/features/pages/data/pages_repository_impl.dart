import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/page_content.dart';
import '../domain/pages_repository.dart';

final pagesRepositoryProvider = Provider<PagesRepository>((ref) {
  return PagesRepositoryImpl(ref.read(apiClientProvider));
});

class PagesRepositoryImpl implements PagesRepository {
  PagesRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<PageContent> fetchBySlug(String slug) async {
    final results = await _client.getList(
      '/public/pages/',
      queryParameters: {'slug': slug},
    );
    return PageContent.fromJson(results.first as Map<String, dynamic>);
  }
}
