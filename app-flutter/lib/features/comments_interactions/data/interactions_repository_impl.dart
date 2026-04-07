import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/app_defaults.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../domain/interactions_repository.dart';

final interactionsRepositoryProvider = Provider<InteractionsRepository>((ref) {
  return InteractionsRepositoryImpl(ref.read(apiClientProvider));
});

class InteractionsRepositoryImpl implements InteractionsRepository {
  InteractionsRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<void> likePost(String targetDocumentId) async {
    await _client.post(
      '/public/interactions/',
      data: {
        'target_type': AppDefaults.postTargetType,
        'target_document_id': targetDocumentId,
        'action_type': 'like',
      },
    );
  }

  @override
  Future<void> reportPost({
    required String targetDocumentId,
    required String reason,
  }) async {
    await _client.post(
      '/public/reports/',
      data: {
        'target_type': AppDefaults.postTargetType,
        'target_document_id': targetDocumentId,
        'reason': reason,
      },
    );
  }
}
