import '../../core/utils/json_helpers.dart';

class Tag {
  const Tag({
    required this.documentId,
    required this.name,
    required this.slug,
    this.description,
  });

  final String documentId;
  final String name;
  final String slug;
  final String? description;

  factory Tag.fromJson(Map<String, dynamic> json) => Tag(
    documentId: asString(json['document_id']),
    name: asString(json['name']),
    slug: asString(json['slug']),
    description: asString(json['description']).isEmpty
        ? null
        : asString(json['description']),
  );
}
