import '../../../shared/models/comment_item.dart';

abstract class CommentsRepository {
  Future<List<CommentItem>> fetchComments(String targetDocumentId);

  Future<void> addComment({
    required String targetDocumentId,
    required String content,
  });
}
