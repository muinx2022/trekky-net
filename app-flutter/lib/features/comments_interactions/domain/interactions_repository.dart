abstract class InteractionsRepository {
  Future<void> likePost(String targetDocumentId);

  Future<void> reportPost({
    required String targetDocumentId,
    required String reason,
  });
}
