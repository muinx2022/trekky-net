import '../../../core/auth/auth_session.dart';

abstract class AuthRepository {
  Future<AuthSession> login({required String email, required String password});

  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
  });

  Future<void> requestPasswordReset(String email);

  Future<void> resetPassword({
    required String uid,
    required String token,
    required String password,
  });

  Future<AuthSession> refresh(String refreshToken);

  Future<AuthSession> hydrateSession({
    required String accessToken,
    required String refreshToken,
  });

  Future<void> logout(String refreshToken);

  Uri buildGoogleAuthUrl();
}
