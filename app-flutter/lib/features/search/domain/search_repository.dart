import '../../../shared/models/search_suggestions.dart';

abstract class SearchRepository {
  Future<SearchSuggestions> search(String query);
}
