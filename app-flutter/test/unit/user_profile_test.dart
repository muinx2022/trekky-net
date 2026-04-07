import 'package:app_flutter/shared/models/user_profile.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('user profile parses document id from snake case payload', () {
    final profile = UserProfile.fromJson({
      'id': 7,
      'document_id': 'abc123',
      'email': 'demo@example.com',
      'username': 'demo',
      'bio': 'Traveler',
    });

    expect(profile.documentId, 'abc123');
    expect(profile.email, 'demo@example.com');
    expect(profile.username, 'demo');
    expect(profile.bio, 'Traveler');
  });
}
