import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/data/auth_repository_impl.dart';
import '../../features/auth/domain/auth_repository.dart';
import '../errors/app_exception.dart';
import '../storage/secure_storage_service.dart';
import 'auth_session.dart';

const _sessionStorageKey = 'trekky.session';

final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

final sessionControllerProvider =
    StateNotifierProvider<SessionController, AuthSession?>((ref) {
      return SessionController(
        ref.read(secureStorageProvider),
        ref.read(authRepositoryProvider),
      );
    });

class SessionController extends StateNotifier<AuthSession?> {
  SessionController(this._storage, this._authRepository) : super(null);

  final SecureStorageService _storage;
  final AuthRepository _authRepository;

  Future<void> restoreSession() async {
    final raw = await _storage.read(_sessionStorageKey);
    if (raw == null || raw.isEmpty) return;
    try {
      state = AuthSession.decode(raw);
    } catch (_) {
      await _storage.delete(_sessionStorageKey);
    }
  }

  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    final session = await _authRepository.login(
      email: email,
      password: password,
    );
    await _persist(session);
    return session;
  }

  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
  }) async {
    final session = await _authRepository.register(
      email: email,
      username: username,
      password: password,
    );
    await _persist(session);
    return session;
  }

  Future<void> requestPasswordReset(String email) {
    return _authRepository.requestPasswordReset(email);
  }

  Future<void> resetPassword({
    required String uid,
    required String token,
    required String password,
  }) {
    return _authRepository.resetPassword(
      uid: uid,
      token: token,
      password: password,
    );
  }

  Future<String?> refreshToken() async {
    final current = state;
    if (current == null || current.refreshToken.isEmpty) return null;
    try {
      final updated = await _authRepository.refresh(current.refreshToken);
      await _persist(updated);
      return updated.accessToken;
    } on AppException {
      await clear();
      return null;
    }
  }

  Future<void> consumeOAuthCallback(Uri uri) async {
    final accessToken = uri.queryParameters['access_token'];
    final refreshToken = uri.queryParameters['refresh_token'];
    if (accessToken == null || refreshToken == null) return;
    final session = await _authRepository.hydrateSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
    );
    await _persist(session);
  }

  Future<void> updateSession(AuthSession session) => _persist(session);

  Future<void> logout() async {
    final refreshToken = state?.refreshToken;
    if (refreshToken != null && refreshToken.isNotEmpty) {
      await _authRepository.logout(refreshToken);
    }
    await clear();
  }

  Future<void> clear() async {
    state = null;
    await _storage.delete(_sessionStorageKey);
  }

  Future<void> _persist(AuthSession session) async {
    state = session;
    await _storage.write(_sessionStorageKey, session.encode());
  }
}
