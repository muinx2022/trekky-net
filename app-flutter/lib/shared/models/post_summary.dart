import '../../core/utils/json_helpers.dart';
import 'category.dart';
import 'media_asset.dart';
import 'tag.dart';
import 'user_profile.dart';

class PostSummary {
  const PostSummary({
    required this.documentId,
    required this.title,
    required this.slug,
    required this.content,
    this.excerpt,
    this.author,
    this.categories = const [],
    this.tags = const [],
    this.images = const [],
    this.permalink,
    this.publishedAt,
  });

  final String documentId;
  final String title;
  final String slug;
  final String content;
  final String? excerpt;
  final UserProfile? author;
  final List<Category> categories;
  final List<Tag> tags;
  final List<MediaAsset> images;
  final String? permalink;
  final DateTime? publishedAt;

  factory PostSummary.fromJson(Map<String, dynamic> json) => PostSummary(
    documentId: asString(json['document_id']),
    title: asString(json['title']),
    slug: asString(json['slug']),
    content: asString(json['content']),
    excerpt: asString(json['excerpt']).isEmpty
        ? null
        : asString(json['excerpt']),
    author: json['author'] is Map<String, dynamic>
        ? UserProfile.fromJson(json['author'] as Map<String, dynamic>)
        : null,
    categories: asList(
      json['categories'],
    ).map((item) => Category.fromJson(asMap(item))).toList(),
    tags: asList(
      json['tags'],
    ).map((item) => Tag.fromJson(asMap(item))).toList(),
    images: asList(
      json['assets'],
    ).map((item) => MediaAsset.fromJson(asMap(item))).toList(),
    permalink: asString(json['permalink']).isEmpty
        ? null
        : asString(json['permalink']),
    publishedAt: DateTime.tryParse(asString(json['published_at'])),
  );
}
