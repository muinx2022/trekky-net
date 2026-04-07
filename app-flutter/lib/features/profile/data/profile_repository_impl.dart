import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/auth_session.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/user_profile.dart';
import '../domain/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepositoryImpl(ref.read(apiClientProvider));
});

class ProfileRepositoryImpl implements ProfileRepository {
  ProfileRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<AuthSession> updateProfile({
    required AuthSession session,
    required String username,
    required String bio,
  }) async {
    final response = await _client.put(
      '/me/',
      data: {'username': username, 'bio': bio},
    );
    return AuthSession(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      user: UserProfile.fromJson(response),
    );
  }
}
