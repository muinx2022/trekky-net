import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/di/providers.dart';
import '../../../core/auth/auth_session.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/network/dio_providers.dart';
import '../../../shared/models/user_profile.dart';
import '../domain/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    ref.read(rawDioProvider),
    ref.read(appConfigProvider).oauthFrontendUrl,
  );
});

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._dio, this._oauthFrontendUrl);

  final Dio _dio;
  final String _oauthFrontendUrl;

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/token/',
      data: {'email': email, 'password': password},
    );
    return _hydrateFromTokens(response.data ?? <String, dynamic>{});
  }

  @override
  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/register/',
      data: {'email': email, 'username': username, 'password': password},
    );
    return _hydrateFromTokens(response.data ?? <String, dynamic>{});
  }

  @override
  Future<void> requestPasswordReset(String email) async {
    await _dio.post<Map<String, dynamic>>(
      '/auth/forgot-password/',
      data: {'email': email},
    );
  }

  @override
  Future<void> resetPassword({
    required String uid,
    required String token,
    required String password,
  }) async {
    await _dio.post<Map<String, dynamic>>(
      '/auth/reset-password/',
      data: {'uid': uid, 'token': token, 'password': password},
    );
  }

  @override
  Future<AuthSession> refresh(String refreshToken) async {
    final tokenResponse = await _dio.post<Map<String, dynamic>>(
      '/auth/token/refresh/',
      data: {'refresh': refreshToken},
    );
    return hydrateSession(
      accessToken: tokenResponse.data?['access'] as String? ?? '',
      refreshToken: tokenResponse.data?['refresh'] as String? ?? refreshToken,
    );
  }

  @override
  Future<AuthSession> hydrateSession({
    required String accessToken,
    required String refreshToken,
  }) async {
    final meResponse = await _dio.get<Map<String, dynamic>>(
      '/me/',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );

    return AuthSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
      user: UserProfile.fromJson(meResponse.data ?? <String, dynamic>{}),
    );
  }

  @override
  Future<void> logout(String refreshToken) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/auth/token/logout/',
        data: {'refresh': refreshToken},
      );
    } catch (_) {
      // Keep local logout resilient even if server-side blacklist fails.
    }
  }

  @override
  Uri buildGoogleAuthUrl() => Uri.parse(
    '${_dio.options.baseUrl}/auth/google/?frontend_url=${Uri.encodeComponent(_oauthFrontendUrl)}',
  );

  Future<AuthSession> _hydrateFromTokens(Map<String, dynamic> payload) async {
    final accessToken = payload['access'] as String? ?? '';
    final refreshToken = payload['refresh'] as String? ?? '';
    if (accessToken.isEmpty || refreshToken.isEmpty) {
      throw const AppException('Missing auth tokens from server response.');
    }
    return hydrateSession(accessToken: accessToken, refreshToken: refreshToken);
  }
}
