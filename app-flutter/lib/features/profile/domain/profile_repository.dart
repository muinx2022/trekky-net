import '../../../core/auth/auth_session.dart';

abstract class ProfileRepository {
  Future<AuthSession> updateProfile({
    required AuthSession session,
    required String username,
    required String bio,
  });
}
