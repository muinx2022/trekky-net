import '../../core/utils/json_helpers.dart';
import 'user_profile.dart';

class CommentItem {
  const CommentItem({
    required this.id,
    required this.documentId,
    required this.content,
    required this.authorName,
    this.author,
    this.createdAt,
  });

  final int id;
  final String documentId;
  final String content;
  final String authorName;
  final UserProfile? author;
  final DateTime? createdAt;

  factory CommentItem.fromJson(Map<String, dynamic> json) => CommentItem(
    id: asType<int>(json['id'], 0),
    documentId: asString(json['document_id']),
    content: asString(json['content']),
    authorName: asString(json['author_name']),
    author: json['author'] is Map<String, dynamic>
        ? UserProfile.fromJson(json['author'] as Map<String, dynamic>)
        : null,
    createdAt: DateTime.tryParse(asString(json['created_at'])),
  );
}
