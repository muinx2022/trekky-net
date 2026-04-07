import '../../core/utils/json_helpers.dart';

class SearchSuggestion {
  const SearchSuggestion({
    required this.documentId,
    required this.slug,
    this.title,
    this.name,
    this.excerpt,
    this.description,
  });

  final String documentId;
  final String slug;
  final String? title;
  final String? name;
  final String? excerpt;
  final String? description;

  factory SearchSuggestion.fromJson(Map<String, dynamic> json) =>
      SearchSuggestion(
        documentId: asString(json['documentId']),
        slug: asString(json['slug']),
        title: asString(json['title']).isEmpty ? null : asString(json['title']),
        name: asString(json['name']).isEmpty ? null : asString(json['name']),
        excerpt: asString(json['excerpt']).isEmpty
            ? null
            : asString(json['excerpt']),
        description: asString(json['description']).isEmpty
            ? null
            : asString(json['description']),
      );
}

class SearchSuggestions {
  const SearchSuggestions({
    this.posts = const [],
    this.tags = const [],
    this.categories = const [],
  });

  final List<SearchSuggestion> posts;
  final List<SearchSuggestion> tags;
  final List<SearchSuggestion> categories;

  factory SearchSuggestions.fromJson(Map<String, dynamic> json) =>
      SearchSuggestions(
        posts: asList(
          json['posts'],
        ).map((item) => SearchSuggestion.fromJson(asMap(item))).toList(),
        tags: asList(
          json['tags'],
        ).map((item) => SearchSuggestion.fromJson(asMap(item))).toList(),
        categories: asList(
          json['categories'],
        ).map((item) => SearchSuggestion.fromJson(asMap(item))).toList(),
      );
}
