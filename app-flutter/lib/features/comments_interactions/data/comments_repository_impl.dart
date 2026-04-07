import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_defaults.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/comment_item.dart';
import '../domain/comments_repository.dart';

final commentsRepositoryProvider = Provider<CommentsRepository>((ref) {
  return CommentsRepositoryImpl(ref.read(apiClientProvider));
});

class CommentsRepositoryImpl implements CommentsRepository {
  CommentsRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<List<CommentItem>> fetchComments(String targetDocumentId) async {
    final response = await _client.getList(
      '/public/comments/',
      queryParameters: {
        'target_type': AppDefaults.postTargetType,
        'target_document_id': targetDocumentId,
      },
    );
    return response
        .map((item) => CommentItem.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<void> addComment({
    required String targetDocumentId,
    required String content,
  }) async {
    await _client.post(
      '/public/comments/',
      data: {
        'target_type': AppDefaults.postTargetType,
        'target_document_id': targetDocumentId,
        'content': content,
      },
    );
  }
}
