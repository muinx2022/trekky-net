import '../../core/utils/json_helpers.dart';

class PageContent {
  const PageContent({
    required this.documentId,
    required this.title,
    required this.slug,
    required this.type,
    this.content,
  });

  final String documentId;
  final String title;
  final String slug;
  final String type;
  final String? content;

  factory PageContent.fromJson(Map<String, dynamic> json) => PageContent(
    documentId: asString(json['document_id']),
    title: asString(json['title']),
    slug: asString(json['slug']),
    type: asString(json['type']),
    content: asString(json['content']).isEmpty
        ? null
        : asString(json['content']),
  );
}
