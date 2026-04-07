import '../../core/utils/json_helpers.dart';

class Category {
  const Category({
    required this.id,
    required this.documentId,
    required this.name,
    required this.slug,
    this.description,
  });

  final int id;
  final String documentId;
  final String name;
  final String slug;
  final String? description;

  factory Category.fromJson(Map<String, dynamic> json) => Category(
    id: asType<int>(json['id'], 0),
    documentId: asString(json['document_id']),
    name: asString(json['name']),
    slug: asString(json['slug']),
    description: asString(json['description']).isEmpty
        ? null
        : asString(json['description']),
  );
}
