import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/search_suggestions.dart';
import '../domain/search_repository.dart';

final searchRepositoryProvider = Provider<SearchRepository>((ref) {
  return SearchRepositoryImpl(ref.read(apiClientProvider));
});

class SearchRepositoryImpl implements SearchRepository {
  SearchRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<SearchSuggestions> search(String query) async {
    final response = await _client.get(
      '/public/search/',
      queryParameters: {'q': query},
    );
    return SearchSuggestions.fromJson(response);
  }
}
