import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/comment_item.dart';
import '../data/comments_repository_impl.dart';

final commentsProvider = FutureProvider.family<List<CommentItem>, String>((
  ref,
  documentId,
) {
  return ref.read(commentsRepositoryProvider).fetchComments(documentId);
});
